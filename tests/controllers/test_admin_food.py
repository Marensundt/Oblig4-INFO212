"""Admin food items (OB4 A1; US-01, US-02, US-03)."""
import re
from dataclasses import replace

import pytest

from app.models.entities import FoodItem
from app.models.enums import Allergen, DietaryLabel
from tests.factories import PASSWORD, log_in, make_order


@pytest.fixture
def admin_client(client, admin):
    log_in(client, "admin@example.com", PASSWORD)
    return client


def item_form(categories, **overrides):
    data = {
        "name": "Fish soup with Bergen cod",
        "description": "Cod, root vegetables and sourdough.",
        "price_nok": "189",
        "min_order_qty": "10",
        "category_ids": [str(categories["conference"].id), str(categories["birthday"].id)],
        "allergens": ["fish", "milk", "gluten"],
        "dietary_labels": [],
        "published": "y",
    }
    data.update(overrides)
    return {k: v for k, v in data.items() if v is not None}


# --- US-01 add -----------------------------------------------------------------------------

def test_list_shows_published_and_unpublished_items(admin_client, repos, soup, categories):
    repos.food_items.add(FoodItem("Rakfisk tasting", "", 210, 10, category_ids=[categories["wedding"].id]))
    page = admin_client.get("/admin/food").data
    assert b"Fish soup" in page and b"Rakfisk tasting" in page
    assert b"Published" in page and b"Not published" in page  # US-03 AC3
    assert b"Conference" in page  # category names, not ids


def test_new_form_shows_every_a1_field(admin_client, categories):
    page = admin_client.get("/admin/food/new").data.decode()
    for label in ("Name", "Description", "Price per portion (NOK)", "Minimum order (portions)",
                  "Event categories", "Allergens", "Dietary labels", "Published"):
        assert label in page
    assert "Birthday" in page and "Crustaceans" in page and "Gluten-free" in page


def test_create_item_with_every_field(admin_client, repos, categories):
    # US-01 AC1
    response = admin_client.post("/admin/food/new", data=item_form(categories, dietary_labels=["lactose_free"]))
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/food")
    [item] = repos.food_items.list_all()
    assert item.name == "Fish soup with Bergen cod"
    assert item.description == "Cod, root vegetables and sourdough."
    assert (item.price_nok, item.min_order_qty) == (189, 10)
    assert set(item.category_ids) == {categories["conference"].id, categories["birthday"].id}
    assert item.allergens == {Allergen.FISH, Allergen.MILK, Allergen.GLUTEN}
    assert item.dietary_labels == {DietaryLabel.LACTOSE_FREE}
    assert item.published is True
    assert "was added" in admin_client.get("/admin/food").data.decode()


def test_create_unpublished_item(admin_client, repos, categories):
    # US-01 AC4: unpublished items are stored but not on the menu
    admin_client.post("/admin/food/new", data=item_form(categories, published=None))
    [item] = repos.food_items.list_all()
    assert item.published is False
    assert repos.food_items.list_published_by_category() == []


@pytest.mark.parametrize("overrides,message", [
    ({"name": ""}, b"This field is required."),
    ({"price_nok": "-5"}, b"Price must be at least 1 NOK."),
    ({"price_nok": "0"}, b"Price must be at least 1 NOK."),
    ({"price_nok": "abc"}, b"Not a valid integer value."),
    ({"min_order_qty": "0"}, b"Minimum order must be at least 1."),
    ({"min_order_qty": ""}, b"Enter a minimum order."),
    ({"category_ids": []}, b"Choose at least one event category."),
    ({"allergens": ["glitter"]}, b"not a valid choice"),
])
def test_invalid_item_is_not_saved(admin_client, repos, categories, overrides, message):
    # US-01 AC2, AC3
    response = admin_client.post("/admin/food/new", data=item_form(categories, **overrides))
    assert response.status_code == 200
    assert message in response.data
    assert repos.food_items.list_all() == []


# --- US-02 edit ----------------------------------------------------------------------------

def test_edit_form_is_prefilled(admin_client, soup):
    page = admin_client.get(f"/admin/food/{soup.id}/edit").data.decode()
    assert 'value="Fish soup"' in page
    assert 'value="189"' in page
    checked = set(re.findall(r'<input checked id="allergens-\d+" name="allergens" type="checkbox" value="(\w+)">', page))
    assert checked == {"fish", "milk"}  # the soup fixture's allergens
    assert '<input checked id="published"' in page


def test_edit_changes_price_and_fields(admin_client, repos, soup, categories):
    # US-02 AC1
    response = admin_client.post(f"/admin/food/{soup.id}/edit", data=item_form(
        categories, name="Fish soup", price_nok="199", allergens=["fish"], dietary_labels=["gluten_free"],
    ))
    assert response.status_code == 302
    item = repos.food_items.get(soup.id)
    assert item.price_nok == 199
    assert item.allergens == {Allergen.FISH}
    assert item.dietary_labels == {DietaryLabel.GLUTEN_FREE}


def test_edit_keeps_picture(admin_client, repos, soup, categories):
    repos.food_items.update(replace(soup, image_filename="soup.png"))
    admin_client.post(f"/admin/food/{soup.id}/edit", data=item_form(categories))
    assert repos.food_items.get(soup.id).image_filename == "soup.png"


def test_price_change_does_not_change_existing_orders(admin_client, repos, soup, categories, customer):
    # US-02 AC2 (ASSUMPTION: price snapshot)
    order = repos.orders.add(make_order(customer.id, soup))
    admin_client.post(f"/admin/food/{soup.id}/edit", data=item_form(categories, price_nok="250"))
    assert repos.orders.get(order.id).lines[0].unit_price_nok == 189


def test_invalid_edit_leaves_item_unchanged(admin_client, repos, soup, categories):
    # US-02 AC3
    response = admin_client.post(f"/admin/food/{soup.id}/edit", data=item_form(categories, price_nok="0"))
    assert response.status_code == 200
    assert repos.food_items.get(soup.id) == soup


def test_edit_unknown_item_is_404(admin_client, repos):
    assert admin_client.get("/admin/food/999/edit").status_code == 404


# --- US-03 remove or unpublish ---------------------------------------------------------------

def test_unpublish_and_publish(admin_client, repos, soup):
    # US-03 AC3
    admin_client.post(f"/admin/food/{soup.id}/publish", data={"published": "0"})
    assert repos.food_items.get(soup.id).published is False
    assert b"Not published" in admin_client.get("/admin/food").data
    admin_client.post(f"/admin/food/{soup.id}/publish", data={"published": "1"})
    assert repos.food_items.get(soup.id).published is True
    assert admin_client.post("/admin/food/999/publish", data={"published": "1"}).status_code == 404


def test_delete_unused_item(admin_client, repos, soup):
    # US-03 AC1
    response = admin_client.post(f"/admin/food/{soup.id}/delete", follow_redirects=True)
    assert repos.food_items.get(soup.id) is None
    assert "was deleted" in response.data.decode()


def test_delete_item_in_order_is_refused_with_unpublish_hint(admin_client, repos, soup, customer):
    # US-03 AC2
    repos.orders.add(make_order(customer.id, soup))
    response = admin_client.post(f"/admin/food/{soup.id}/delete", follow_redirects=True)
    assert repos.food_items.get(soup.id) is not None
    assert "cannot be deleted" in response.data.decode()
    assert "Unpublish it instead" in response.data.decode()


def test_delete_unknown_item_is_404(admin_client, repos):
    assert admin_client.post("/admin/food/999/delete").status_code == 404


# --- access ------------------------------------------------------------------------------------

def test_customer_cannot_use_any_food_route(client, repos, customer, soup):
    log_in(client, "kunde@example.com", PASSWORD)
    assert client.get(f"/admin/food/{soup.id}/edit").status_code == 403
    for path in (f"/admin/food/{soup.id}/edit", f"/admin/food/{soup.id}/publish",
                 f"/admin/food/{soup.id}/delete", "/admin/food/new"):
        assert client.post(path, data={"published": "0", "name": "Hacked"}).status_code == 403, path
    assert repos.food_items.get(soup.id) == soup


def test_admin_start_page_links_to_food_items(admin_client):
    assert b'href="/admin/food"' in admin_client.get("/admin/").data
