"""The manual walkthrough of 01-plan §8 as one end-to-end test on a freshly seeded database.

Every official requirement is used once through the web pages, in the order a demo would show them:
C1 → C2 → C3 → C4 → C5 → A1 → A2 → A3 → A4 → the customer sees the updates.
"""
import re
from datetime import date, timedelta

from app.models.enums import OrderStatus, PaymentStatus
from app.models.seed import seed

SEED_PASSWORD = "ektemat-demo"


def text(response):
    return response.data.decode()


def test_walkthrough(client, repos):
    seed(repos)  # = flask --app run reset-db --yes on a fresh database

    # C1 menu by event: cards grouped by kind of event, with price, minimum order, allergens
    menu = text(client.get("/menu"))
    assert re.findall(r'<h2 id="([\w-]+)">', menu)[:5] == ["birthday", "confirmation", "wedding", "conference", "julebord"]
    soup = next(i for i in repos.food_items.list_all() if i.published and i.min_order_qty > 1)
    assert soup.name in menu and f"{soup.price_nok} NOK per portion" in menu

    # C2 cart: below the minimum is refused, a valid quantity is added, the total is estimated
    refused = text(client.post("/cart/add", data={"item_id": soup.id, "quantity": soup.min_order_qty - 1},
                               follow_redirects=True))
    assert f"minimum order for “{soup.name}” is {soup.min_order_qty} portions" in refused
    client.post("/cart/add", data={"item_id": soup.id, "quantity": 30})
    assert f"{soup.price_nok * 30} NOK" in text(client.get("/cart"))

    # C3 order: anonymous → register → back to checkout → two guest groups incl. a nut allergy
    assert "/account/login?next=/account/checkout" in client.get("/account/checkout").headers["Location"]
    client.post("/account/register", data={
        "name": "Demo Kunde", "email": "demo.kunde@example.com", "phone": "",
        "password": "long-enough", "confirm": "long-enough", "next": "/account/checkout",
    })
    response = client.post("/account/checkout", data={
        "event_date": (date.today() + timedelta(days=21)).isoformat(),
        "guest_count": "30",
        "delivery_address": "Bryggen 1, 5003 Bergen",
        "guest_groups-0-label": "Adults", "guest_groups-0-count": "26",
        "guest_groups-0-dietary_notes": "3 vegetarian",
        "guest_groups-1-label": "Children", "guest_groups-1-count": "4",
        "guest_groups-1-allergies": ["nuts"],
        "submit": "Send order",
    }, follow_redirects=True)
    order_number = re.search(r"Order ([\d-]+) received", text(response)).group(1)
    customer = repos.users.get_by_email("demo.kunde@example.com")
    [order] = repos.orders.list_for_customer(customer.id)
    assert order.order_number == order_number

    # C4 my orders: submitted / not paid
    my_orders = text(client.get("/account/orders"))
    assert order_number in my_orders and ">Submitted<" in my_orders and ">Not paid<" in my_orders

    # C5 question on the order
    client.post(f"/account/orders/{order.id}/questions", data={"text": "Can you deliver at 17:00?"})
    assert "Waiting for an answer" in text(client.get(f"/account/orders/{order.id}"))
    client.post("/account/logout")

    # A1 admin creates a food item
    client.post("/account/login", data={"email": "admin@ektemat.example", "password": SEED_PASSWORD})
    birthday = repos.categories.get_by_slug("birthday")
    client.post("/admin/food/new", data={
        "name": "Cloudberry cream", "description": "Seasonal dessert", "price_nok": "85",
        "min_order_qty": "10", "category_ids": [birthday.id], "allergens": ["milk"], "published": "y",
    })
    item = next(i for i in repos.food_items.list_all() if i.name == "Cloudberry cream")

    # A2 picture from an instruction, previewed, then saved; only now it appears on the menu
    client.post(f"/admin/food/{item.id}/image/generate",
                data={"instruction": "Cloudberries on cream in a glass", "mode": "new"})
    assert "not saved yet" in text(client.get(f"/admin/food/{item.id}/image/preview"))
    assert repos.food_items.get(item.id).image_filename is None
    client.post(f"/admin/food/{item.id}/image/save")
    picture = repos.food_items.get(item.id).image_filename
    assert f"/uploads/{picture}" in text(client.get("/menu"))

    # A3 admin finds the order by status, approves it and sets deposit paid
    assert order_number in text(client.get("/admin/orders?status=submitted"))
    detail = text(client.get(f"/admin/orders/{order.id}"))
    assert "Children (4 guests): Nuts" in detail  # allergies highlighted
    client.post(f"/admin/orders/{order.id}/status", data={"status": "approved"})
    client.post(f"/admin/orders/{order.id}/payment", data={"payment_status": "deposit_paid"})

    # A4 admin answers the question
    [question] = repos.questions.list_for_order(order.id)
    questions = text(client.get("/admin/questions"))
    assert "Can you deliver at 17:00?" in questions and f"/admin/questions/{question.id}/answer" in questions
    client.post(f"/admin/questions/{question.id}/answer", data={"text": "Yes, 17:00 is fine."})
    client.post("/account/logout")

    # The customer sees every update
    client.post("/account/login", data={"email": "demo.kunde@example.com", "password": "long-enough"})
    assert ">Approved<" in text(client.get("/account/orders"))
    page = text(client.get(f"/account/orders/{order.id}"))
    assert "Deposit paid" in page and "Yes, 17:00 is fine." in page
    stored = repos.orders.get(order.id)
    assert (stored.status, stored.payment_status) == (OrderStatus.APPROVED, PaymentStatus.DEPOSIT_PAID)
