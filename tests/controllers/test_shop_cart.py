"""Shopping cart pages (OB4 C2; US-08, US-09)."""
import re
from dataclasses import replace

from app.models.entities import FoodItem
from tests.factories import PASSWORD, log_in


def add(client, item_id, quantity):
    return client.post("/cart/add", data={"item_id": item_id, "quantity": quantity}, follow_redirects=True)


def update(client, item_id, quantity):
    return client.post("/cart/update", data={"item_id": item_id, "quantity": quantity}, follow_redirects=True)


def cart_quantities(client):
    with client.session_transaction() as session:
        return session.get("cart", {})


def cart_page(client):
    return client.get("/cart").data.decode()


def total(page):
    return int(re.search(r'<td class="num cart-total">(\d+) NOK</td>', page).group(1))


def test_menu_card_has_add_to_cart_form(client, repos, soup):
    page = client.get("/menu").data.decode()
    assert 'action="/cart/add"' in page
    assert f'name="item_id" value="{soup.id}"' in page
    assert 'min="10"' in page and 'value="10"' in page  # starts at the minimum order


def test_cart_is_public_and_empty_at_first(client, repos):
    response = client.get("/cart")
    assert response.status_code == 200
    assert "Your cart is empty." in response.data.decode()


def test_add_at_minimum(client, repos, soup):
    # US-08 AC1
    page = add(client, soup.id, 10).data.decode()
    assert "Added 10 portions of “Fish soup” to your cart." in page
    assert cart_quantities(client) == {str(soup.id): 10}
    assert "Cart (1)" in page  # header link


def test_add_below_minimum_rejected_with_message(client, repos, soup):
    # US-08 AC2 / OB4 C2 "Quantities below an item's minimum order are not accepted"
    page = add(client, soup.id, 9).data.decode()
    assert "The minimum order for “Fish soup” is 10 portions." in page
    assert cart_quantities(client) == {}


def test_add_same_item_twice_adds_quantities(client, repos, soup):
    # US-08 AC3
    add(client, soup.id, 10)
    add(client, soup.id, 12)
    assert cart_quantities(client) == {str(soup.id): 22}


def test_add_unpublished_or_unknown_item_rejected(client, repos, categories):
    draft = repos.food_items.add(FoodItem("Rakfisk", "", 210, 10, category_ids=[categories["wedding"].id]))
    assert "not on the menu" in add(client, draft.id, 10).data.decode()
    assert "not on the menu" in add(client, 999, 10).data.decode()
    assert cart_quantities(client) == {}


def test_add_with_non_number_quantity(client, repos, soup):
    page = add(client, soup.id, "ten").data.decode()
    assert "whole number" in page
    assert cart_quantities(client) == {}


def test_cart_shows_lines_and_estimated_total(client, repos, categories, soup):
    # US-09 AC1
    cake = repos.food_items.add(FoodItem("Cake", "", 95, 5, category_ids=[categories["birthday"].id],
                                         published=True))
    add(client, soup.id, 10)
    add(client, cake.id, 6)
    page = cart_page(client)
    assert "Fish soup" in page and "Cake" in page
    assert "<td class=\"num\">1890</td>" in page
    assert "<td class=\"num\">570</td>" in page
    assert total(page) == 1890 + 570
    assert "estimate" in page


def test_update_quantity_recalculates_total(client, repos, soup):
    # US-09 AC2 (valid change)
    add(client, soup.id, 10)
    page = update(client, soup.id, 20).data.decode()
    assert "changed to 20 portions" in page
    assert total(page) == 189 * 20


def test_update_below_minimum_keeps_old_quantity(client, repos, soup):
    # US-09 AC2 (rejected change)
    add(client, soup.id, 15)
    page = update(client, soup.id, 3).data.decode()
    assert "The minimum order for “Fish soup” is 10 portions." in page
    assert cart_quantities(client) == {str(soup.id): 15}
    assert total(page) == 189 * 15


def test_update_item_not_in_cart(client, repos, soup):
    page = update(client, soup.id, 10).data.decode()
    assert "not in the cart" in page
    assert cart_quantities(client) == {}


def test_remove_line_updates_total(client, repos, categories, soup):
    # US-09 AC3
    cake = repos.food_items.add(FoodItem("Cake", "", 95, 5, category_ids=[categories["birthday"].id],
                                         published=True))
    add(client, soup.id, 10)
    add(client, cake.id, 5)
    page = client.post(f"/cart/remove/{soup.id}", follow_redirects=True).data.decode()
    assert "removed from your cart" in page
    assert "Fish soup" not in page
    assert total(page) == 95 * 5


def test_remove_last_line_empties_cart(client, repos, soup):
    add(client, soup.id, 10)
    page = client.post(f"/cart/remove/{soup.id}", follow_redirects=True).data.decode()
    assert "Your cart is empty." in page


def test_unpublished_item_is_dropped_with_explanation(client, repos, soup):
    # US-09 AC4
    add(client, soup.id, 10)
    repos.food_items.update(replace(soup, published=False))
    page = cart_page(client)
    assert "“Fish soup” is no longer on the menu and was removed from your cart." in page
    assert "Your cart is empty." in page
    assert cart_quantities(client) == {}


def test_deleted_item_is_dropped(client, repos, soup):
    add(client, soup.id, 10)
    repos.food_items.delete(soup.id)
    page = cart_page(client)
    assert "An item is no longer on the menu" in page
    assert cart_quantities(client) == {}


def test_price_change_is_reflected_in_cart(client, repos, soup):
    # The cart stores ids and quantities only; the order (phase 6) snapshots the price.
    add(client, soup.id, 10)
    repos.food_items.update(replace(soup, price_nok=200))
    assert total(cart_page(client)) == 2000


def test_raised_minimum_shows_warning(client, repos, soup):
    add(client, soup.id, 10)
    repos.food_items.update(replace(soup, min_order_qty=20))
    assert "The minimum order has changed" in cart_page(client)


def test_cart_survives_login(client, repos, customer, soup):
    # US-11 AC2: the cart is kept when the visitor logs in
    add(client, soup.id, 10)
    log_in(client, "kunde@example.com", PASSWORD)
    assert cart_quantities(client) == {str(soup.id): 10}


def test_cart_forms_post_with_csrf_token(app, repos, soup):
    # With CSRF on (normal config), the menu and cart forms carry a token and posts without it fail.
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    assert 'name="csrf_token"' in client.get("/menu").data.decode()
    assert client.post("/cart/add", data={"item_id": soup.id, "quantity": 10}).status_code == 400


def test_quantity_field_ids_unique_when_item_in_two_categories(client, repos, categories):
    repos.food_items.add(FoodItem("Kids menu", "", 149, 5, published=True,
                                  category_ids=[categories["birthday"].id, categories["wedding"].id]))
    ids = re.findall(r'<input id="([\w-]+)" type="number"', client.get("/menu").data.decode())
    assert len(ids) == 2 and len(set(ids)) == 2
