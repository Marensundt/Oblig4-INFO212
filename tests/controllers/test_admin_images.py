"""Admin pictures: upload or instruction → preview → save/discard (OB4 A2; US-04, US-05)."""
import io
import os
import re
from dataclasses import replace

import pytest

from app.models.images import ImageError
from tests.factories import PASSWORD, log_in
from tests.unit.test_images import JPG, PNG, SVG


@pytest.fixture
def admin_client(client, admin):
    log_in(client, "admin@example.com", PASSWORD)
    return client


def upload(client, item_id, name, data):
    return client.post(f"/admin/food/{item_id}/image/upload",
                       data={"picture": (io.BytesIO(data), name)}, content_type="multipart/form-data")


def generate(client, item_id, instruction, mode="new"):
    return client.post(f"/admin/food/{item_id}/image/generate", data={"instruction": instruction, "mode": mode})


def pending_name(client):
    with client.session_transaction() as session:
        return (session.get("pending_image") or {}).get("name")


def uploads(app):
    folder = app.config["UPLOAD_FOLDER"]
    return sorted(f for f in os.listdir(folder) if f != "pending") if os.path.isdir(folder) else []


def test_picture_page(admin_client, soup):
    page = admin_client.get(f"/admin/food/{soup.id}/image").data.decode()
    assert "Upload a picture" in page and "Create from an instruction" in page
    assert 'enctype="multipart/form-data"' in page
    assert "Image service: offline placeholder." in page
    assert '<input disabled id="mode-1"' in page  # no SVG yet, nothing to modify


def test_links_to_picture_page(admin_client, soup):
    assert f'href="/admin/food/{soup.id}/image"' in admin_client.get("/admin/food").data.decode()
    assert f'href="/admin/food/{soup.id}/image"' in admin_client.get(f"/admin/food/{soup.id}/edit").data.decode()


def test_upload_shows_preview_and_leaves_item_unchanged(app, admin_client, repos, soup):
    # US-04 + OB4 "previews the result before it is saved"
    response = upload(admin_client, soup.id, "soup.png", PNG)
    assert response.headers["Location"] == f"/admin/food/{soup.id}/image/preview"
    page = admin_client.get(f"/admin/food/{soup.id}/image/preview").data.decode()
    assert "New picture" in page and "not saved yet" in page
    assert f'src="/admin/food/{soup.id}/image/pending"' in page
    pending = admin_client.get(f"/admin/food/{soup.id}/image/pending")
    assert pending.status_code == 200 and pending.data == PNG
    assert repos.food_items.get(soup.id).image_filename is None
    assert uploads(app) == []


def test_save_updates_item_and_menu(app, admin_client, repos, soup):
    upload(admin_client, soup.id, "soup.png", PNG)
    name = pending_name(admin_client)
    response = admin_client.post(f"/admin/food/{soup.id}/image/save", follow_redirects=True)
    assert "was saved" in response.data.decode()
    assert repos.food_items.get(soup.id).image_filename == name
    assert uploads(app) == [name]
    assert f'src="/uploads/{name}"' in admin_client.get("/menu").data.decode()
    assert pending_name(admin_client) is None


def test_discard_leaves_item_unchanged_and_removes_file(app, admin_client, repos, soup):
    generate(admin_client, soup.id, "Fish soup in a white bowl")
    name = pending_name(admin_client)
    assert os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], "pending", name))
    page = admin_client.post(f"/admin/food/{soup.id}/image/discard", follow_redirects=True).data.decode()
    assert "discarded" in page
    assert repos.food_items.get(soup.id).image_filename is None
    assert not os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], "pending", name))
    assert "/uploads/" not in admin_client.get("/menu").data.decode()  # only saved pictures appear in C1


def test_saving_replaces_old_picture_file(app, admin_client, repos, soup):
    upload(admin_client, soup.id, "a.png", PNG)
    admin_client.post(f"/admin/food/{soup.id}/image/save")
    first = repos.food_items.get(soup.id).image_filename
    upload(admin_client, soup.id, "b.jpg", JPG)
    admin_client.post(f"/admin/food/{soup.id}/image/save")
    second = repos.food_items.get(soup.id).image_filename
    assert second.endswith(".jpg") and second != first
    assert uploads(app) == [second]


@pytest.mark.parametrize("name,data,message", [
    ("soup.gif", b"GIF89a", "Choose a JPG, PNG, WebP or SVG file."),
    ("soup.png", b"not a picture", "does not look like a PNG"),
    ("evil.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', "may not contain"),
])
def test_invalid_upload_rejected(admin_client, repos, soup, name, data, message):
    response = upload(admin_client, soup.id, name, data)
    assert response.status_code == 200
    assert message in response.data.decode()
    assert pending_name(admin_client) is None


def test_upload_without_file(admin_client, soup):
    page = admin_client.post(f"/admin/food/{soup.id}/image/upload", data={},
                             content_type="multipart/form-data").data.decode()
    assert "Choose a file to upload." in page


def test_too_large_upload(admin_client, soup):
    response = upload(admin_client, soup.id, "big.png", PNG + b"\x00" * (2 * 1024 * 1024))
    assert response.status_code == 413
    assert "at most 2 MB" in response.data.decode()


def test_generate_with_placeholder_service(admin_client, soup):
    # US-05 (offline default)
    generate(admin_client, soup.id, "Steaming bowl with dill")
    svg = admin_client.get(f"/admin/food/{soup.id}/image/pending").data.decode()
    assert "Fish soup" in svg and "Steaming bowl with dill" in svg
    page = admin_client.get(f"/admin/food/{soup.id}/image/preview").data.decode()
    assert "offline placeholder: “Steaming bowl with dill”" in page


def test_empty_instruction_rejected(admin_client, soup):
    page = generate(admin_client, soup.id, "   ").data.decode()
    assert "Write an instruction first." in page
    assert pending_name(admin_client) is None


class RecordingService:
    name = "test service"

    def __init__(self, error=None):
        self.calls, self.error = [], error

    def create_svg(self, item, instruction, current_svg=None):
        self.calls.append((item.name, instruction, current_svg))
        if self.error:
            raise ImageError(self.error)
        return SVG.decode()


def test_modify_sends_current_svg_to_service(app, admin_client, repos, soup):
    # US-05 "modify the picture"
    upload(admin_client, soup.id, "soup.svg", SVG)
    admin_client.post(f"/admin/food/{soup.id}/image/save")
    app.image_service = service = RecordingService()
    assert '<input disabled id="mode-1"' not in admin_client.get(f"/admin/food/{soup.id}/image").data.decode()
    generate(admin_client, soup.id, "Add parsley", mode="modify")
    assert service.calls == [("Fish soup", "Add parsley", SVG.decode())]
    assert pending_name(admin_client)


def test_raster_picture_cannot_be_modified(app, admin_client, repos, soup):
    upload(admin_client, soup.id, "soup.png", PNG)
    admin_client.post(f"/admin/food/{soup.id}/image/save")
    app.image_service = service = RecordingService()
    page = generate(admin_client, soup.id, "Add parsley", mode="modify").data.decode()
    assert "Only SVG pictures can be modified." in page
    assert service.calls == []


def test_service_error_shown_and_nothing_pending(app, admin_client, soup):
    app.image_service = RecordingService(error="The AI image service is busy. Try again in a minute.")
    page = generate(admin_client, soup.id, "Anything").data.decode()
    assert "The AI image service is busy." in page
    assert pending_name(admin_client) is None


def test_preview_and_save_without_pending(admin_client, repos, soup):
    response = admin_client.get(f"/admin/food/{soup.id}/image/preview")
    assert response.headers["Location"] == f"/admin/food/{soup.id}/image"
    assert admin_client.get(f"/admin/food/{soup.id}/image/pending").status_code == 404
    page = admin_client.post(f"/admin/food/{soup.id}/image/save", follow_redirects=True).data.decode()
    assert "no new picture to save" in page
    assert repos.food_items.get(soup.id).image_filename is None


def test_pending_belongs_to_one_item(admin_client, repos, categories, soup):
    from app.models.entities import FoodItem
    cake = repos.food_items.add(FoodItem("Cake", "", 95, 5, category_ids=[categories["birthday"].id]))
    upload(admin_client, soup.id, "soup.png", PNG)
    assert admin_client.get(f"/admin/food/{cake.id}/image/pending").status_code == 404
    admin_client.post(f"/admin/food/{cake.id}/image/save")
    assert repos.food_items.get(cake.id).image_filename is None


def test_new_pending_replaces_older_pending_file(app, admin_client, soup):
    upload(admin_client, soup.id, "a.png", PNG)
    first = pending_name(admin_client)
    upload(admin_client, soup.id, "b.png", PNG)
    assert os.listdir(os.path.join(app.config["UPLOAD_FOLDER"], "pending")) == [pending_name(admin_client)]
    assert first != pending_name(admin_client)


def test_pictures_served_with_security_headers(admin_client, soup):
    upload(admin_client, soup.id, "soup.svg", SVG)
    pending = admin_client.get(f"/admin/food/{soup.id}/image/pending")
    assert pending.headers["Content-Security-Policy"].startswith("default-src 'none'")
    admin_client.post(f"/admin/food/{soup.id}/image/save")
    name = re.search(r'/uploads/([\w.-]+)"', admin_client.get("/menu").data.decode()).group(1)
    served = admin_client.get(f"/uploads/{name}")
    assert served.headers["Content-Security-Policy"].startswith("default-src 'none'")
    assert served.headers["X-Content-Type-Options"] == "nosniff"


def test_customer_cannot_use_picture_routes(client, repos, customer, soup):
    log_in(client, "kunde@example.com", PASSWORD)
    for path in ("image", "image/preview", "image/pending"):
        assert client.get(f"/admin/food/{soup.id}/{path}").status_code == 403
    assert upload(client, soup.id, "soup.png", PNG).status_code == 403
    assert generate(client, soup.id, "x").status_code == 403
    for path in ("image/save", "image/discard"):
        assert client.post(f"/admin/food/{soup.id}/{path}").status_code == 403


def test_unknown_item_is_404(admin_client):
    assert admin_client.get("/admin/food/999/image").status_code == 404
    assert upload(admin_client, 999, "soup.png", PNG).status_code == 404


def test_seed_picture_kept_when_replaced(app, admin_client, repos, soup):
    # Pictures not created by this app (e.g. demo files) are never deleted
    folder = app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "demo.png"), "wb") as f:
        f.write(PNG)
    repos.food_items.update(replace(soup, image_filename="demo.png"))
    upload(admin_client, soup.id, "new.png", PNG)
    admin_client.post(f"/admin/food/{soup.id}/image/save")
    assert os.path.exists(os.path.join(folder, "demo.png"))
