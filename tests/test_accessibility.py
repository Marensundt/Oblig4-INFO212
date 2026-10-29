"""Accessibility pass over every page for every role on the seeded data (NFR-16; 01-plan phase 10).

Checks what can be checked automatically: page language, one h1, alt text on images, a label for
every visible form field, and unique element ids. Colour contrast and keyboard use need a manual check.
"""
from collections import Counter
from html.parser import HTMLParser

import pytest

from app.models.seed import seed
from tests.unit.test_images import PNG

SEED_PASSWORD = "ektemat-demo"
UNLABELLED_TYPES = {"hidden", "submit", "button", "image", "reset"}


class PageAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = None
        self.h1 = 0
        self.images_without_alt = []
        self.fields = []           # (id, name) of visible form fields
        self.label_for = set()
        self.ids = Counter()
        self._label_depth = 0
        self.wrapped = set()       # fields inside a <label>

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids[attrs["id"]] += 1
        if tag == "html":
            self.lang = attrs.get("lang")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img" and "alt" not in attrs:
            self.images_without_alt.append(attrs.get("src"))
        elif tag == "label":
            self._label_depth += 1
            if attrs.get("for"):
                self.label_for.add(attrs["for"])
        elif tag in ("input", "select", "textarea") and attrs.get("type") not in UNLABELLED_TYPES:
            field = (attrs.get("id"), attrs.get("name"), "aria-label" in attrs)
            self.fields.append(field)
            if self._label_depth:
                self.wrapped.add(field)

    def handle_endtag(self, tag):
        if tag == "label" and self._label_depth:
            self._label_depth -= 1

    def problems(self):
        found = []
        if self.lang != "en":
            found.append("html lang missing")
        if self.h1 != 1:
            found.append(f"{self.h1} h1 headings")
        found += [f"img without alt: {src}" for src in self.images_without_alt]
        for field in self.fields:
            field_id, name, has_aria = field
            if not (has_aria or field in self.wrapped or (field_id and field_id in self.label_for)):
                found.append(f"field without label: {name or field_id}")
        found += [f"duplicate id: {i}" for i, n in self.ids.items() if n > 1]
        return found


@pytest.fixture
def seeded(app, repos):
    seed(repos)
    return repos


def audit(client, path):
    # With CSRF on, so hidden token fields are rendered too (two forms must not share an id)
    client.application.config["WTF_CSRF_ENABLED"] = True
    try:
        response = client.get(path)
    finally:
        client.application.config["WTF_CSRF_ENABLED"] = False
    assert response.status_code in (200, 403, 404), (path, response.status_code)
    page = PageAudit()
    page.feed(response.data.decode())
    return page.problems()


def log_in_as(client, email):
    client.post("/account/logout")
    client.post("/account/login", data={"email": email, "password": SEED_PASSWORD})


def test_public_pages(client, seeded):
    item = next(i for i in seeded.food_items.list_all() if i.published)
    paths = ["/menu", "/cart", "/account/login", "/account/register", "/no-such-page"]
    client.post("/cart/add", data={"item_id": item.id, "quantity": item.min_order_qty})
    paths.append("/cart")  # with a line
    assert {path: audit(client, path) for path in paths} == {path: [] for path in paths}


def test_customer_pages(client, seeded):
    customer = seeded.users.get_by_email("kari.kunde@example.com")
    item = next(i for i in seeded.food_items.list_all() if i.published)
    log_in_as(client, customer.email)
    client.post("/cart/add", data={"item_id": item.id, "quantity": item.min_order_qty})
    orders = seeded.orders.list_for_customer(customer.id)
    paths = ["/account/", "/account/orders", "/account/checkout", "/admin/"]  # /admin/ = 403 page
    paths += [f"/account/orders/{o.id}" for o in orders]
    paths += [f"/account/checkout/confirmation/{orders[0].id}"]
    assert {path: audit(client, path) for path in paths} == {path: [] for path in paths}


def test_admin_pages(client, seeded):
    log_in_as(client, "admin@ektemat.example")
    item = seeded.food_items.list_all()[0]
    paths = ["/admin/", "/admin/food", "/admin/food/new", f"/admin/food/{item.id}/edit",
             f"/admin/food/{item.id}/image", "/admin/orders", "/admin/orders?status=submitted",
             "/admin/questions"]
    paths += [f"/admin/orders/{o.id}" for o in seeded.orders.list()]
    client.post(f"/admin/food/{item.id}/image/generate", data={"instruction": "A bowl", "mode": "new"})
    paths.append(f"/admin/food/{item.id}/image/preview")
    assert {path: audit(client, path) for path in paths} == {path: [] for path in paths}


def test_form_errors_are_linked_to_fields(client, seeded):
    # Error messages are announced with the field (aria-describedby) and not shown by colour alone
    log_in_as(client, "admin@ektemat.example")
    page = client.post("/admin/food/new", data={"name": "", "price_nok": "0", "min_order_qty": "1"}).data.decode()
    assert 'aria-describedby="name-errors"' in page and 'id="name-errors"' in page
    assert 'aria-invalid="true"' in page


def test_upload_page_after_error(client, seeded):
    import io
    log_in_as(client, "admin@ektemat.example")
    item = seeded.food_items.list_all()[0]
    response = client.post(f"/admin/food/{item.id}/image/upload",
                           data={"picture": (io.BytesIO(PNG), "x.gif")}, content_type="multipart/form-data")
    page = PageAudit()
    page.feed(response.data.decode())
    assert page.problems() == []
