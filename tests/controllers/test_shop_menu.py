"""Customer menu by kind of event (OB4 C1; US-06, US-01 AC4, US-07)."""
import re
from dataclasses import replace

from app.models.entities import FoodItem
from app.models.enums import Allergen, DietaryLabel
from app.models.seed import seed
from tests.factories import PASSWORD, log_in


def section(page, slug):
    """HTML of one category section of the menu."""
    match = re.search(rf'<section class="menu-category" aria-labelledby="{slug}">(.*?)</section>', page, re.S)
    assert match, f"no section for {slug}"
    return match.group(1)


def test_menu_is_public(client, repos, soup):
    # US-06 / INT-I "at any hour": no login needed
    response = client.get("/menu")
    assert response.status_code == 200
    assert "Fish soup" in response.data.decode()


def test_items_grouped_under_event_headings_in_order(client, repos, categories, soup):
    # US-06 AC1
    repos.food_items.add(FoodItem("Lamb", "", 245, 10, category_ids=[categories["birthday"].id], published=True))
    page = client.get("/menu").data.decode()
    headings = re.findall(r'<h2 id="([\w-]+)">', page)
    assert headings == ["birthday", "conference"]  # category sort order; wedding has no items
    assert "Lamb" in section(page, "birthday")
    assert "Fish soup" in section(page, "conference")
    assert '<a href="#birthday">Birthday</a>' in page


def test_card_shows_picture_price_minimum_order_and_allergens(client, repos, soup):
    # US-06 AC2 (OB4 C1: "picture, price, minimum order and allergens")
    card = section(client.get("/menu").data.decode(), "conference")
    assert 'src="/static/img/placeholder.svg" alt="No picture yet"' in card
    assert "189 NOK per portion" in card
    assert "10 portions" in card
    assert '<span class="badge badge-allergen">Fish</span>' in card
    assert '<span class="badge badge-allergen">Milk</span>' in card
    assert "Bergen cod" in card  # description


def test_card_uses_uploaded_picture(client, repos, soup):
    repos.food_items.update(replace(soup, image_filename="soup.png"))
    card = section(client.get("/menu").data.decode(), "conference")
    assert 'src="/uploads/soup.png" alt="Fish soup"' in card


def test_item_without_allergens(client, repos, categories):
    repos.food_items.add(FoodItem("Fruit", "", 50, 5, category_ids=[categories["birthday"].id], published=True))
    assert "none listed" in section(client.get("/menu").data.decode(), "birthday")


def test_item_in_two_categories_appears_under_both(client, repos, categories):
    # US-06 AC3
    repos.food_items.add(FoodItem(
        "Kids menu", "", 149, 5, category_ids=[categories["birthday"].id, categories["wedding"].id], published=True,
    ))
    page = client.get("/menu").data.decode()
    assert "Kids menu" in section(page, "birthday")
    assert "Kids menu" in section(page, "wedding")
    assert page.count("<h3>Kids menu</h3>") == 2


def test_unpublished_item_is_not_shown(client, repos, categories, soup):
    # US-06 AC4
    repos.food_items.add(FoodItem("Rakfisk tasting", "", 210, 10, category_ids=[categories["conference"].id]))
    page = client.get("/menu").data.decode()
    assert "Rakfisk tasting" not in page
    assert "Fish soup" in page


def test_admin_unpublish_removes_item_from_menu(client, repos, admin, soup):
    # US-01 AC4 / US-03 AC3 end to end: admin unpublishes, visitor no longer sees it
    log_in(client, "admin@example.com", PASSWORD)
    client.post(f"/admin/food/{soup.id}/publish", data={"published": "0"})
    client.post("/account/logout")
    assert "Fish soup" not in client.get("/menu").data.decode()


def test_dietary_labels_shown(client, repos, categories):
    # US-07 (Could)
    repos.food_items.add(FoodItem("Salad", "", 165, 10, category_ids=[categories["birthday"].id],
                                  dietary_labels={DietaryLabel.VEGETARIAN}, published=True))
    assert '<span class="badge badge-diet">Vegetarian</span>' in client.get("/menu").data.decode()


def test_empty_menu_message(client, repos):
    page = client.get("/menu").data.decode()
    assert "The menu is being updated." in page
    assert "<h2" not in page


def test_menu_escapes_text(client, repos, categories):
    repos.food_items.add(FoodItem("<script>alert(1)</script>", "", 10, 1,
                                  category_ids=[categories["birthday"].id], allergens={Allergen.EGGS},
                                  published=True))
    page = client.get("/menu").data.decode()
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_seeded_menu(client, repos):
    # Acceptance (01-plan §8 phase 4): menu matches the seed data
    seed(repos)
    page = client.get("/menu").data.decode()
    assert re.findall(r'<h2 id="([\w-]+)">', page) == [
        "birthday", "confirmation", "wedding", "conference", "julebord", "corporate-lunch",
    ]
    assert "Rakfisk tasting" not in page  # unpublished in the seed
    assert "Traditional julebord buffet" in section(page, "julebord")
    assert "875 NOK per portion" in section(page, "wedding")
