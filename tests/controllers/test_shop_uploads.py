"""Food item pictures are served from the upload folder (C1 card picture; A2 saves them in phase 9)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_upload_folder_defaults_to_instance(app):
    assert app.config["UPLOAD_FOLDER"].endswith("uploads")


def test_serves_picture_from_upload_folder(app, client, tmp_path):
    folder = tmp_path / "uploads"
    folder.mkdir()
    (folder / "soup.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    app.config["UPLOAD_FOLDER"] = str(folder)
    response = client.get("/uploads/soup.svg")
    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"


def test_missing_picture_and_path_traversal_give_404(app, client, tmp_path):
    folder = tmp_path / "uploads"
    folder.mkdir()
    (tmp_path / "secret.txt").write_text("not public")
    app.config["UPLOAD_FOLDER"] = str(folder)
    assert client.get("/uploads/missing.png").status_code == 404
    assert client.get("/uploads/../secret.txt").status_code == 404
    assert client.get("/uploads/%2e%2e/secret.txt").status_code == 404


def test_placeholder_image_exists(client):
    response = client.get("/static/img/placeholder.svg")
    assert response.status_code == 200
    assert (ROOT / "app/static/img/placeholder.svg").read_text().startswith("<svg")
