"""Synthetic seed data (OB4 §3: sample food items, an admin and test customers).

All data is fictional. Data is inserted through the repositories only, so the same seed
works when the storage changes to Neo4j. Minimum orders, categories and allergens are
ASSUMPTIONS (docs/plans/01-implementation-plan.md §7).

DEMO_PASSWORD is for local testing with synthetic data only — never use it in production.
"""
from datetime import date, timedelta

from app.models.entities import EventCategory, FoodItem, GuestGroup, Order, OrderLine, Question, User
from app.models.enums import Allergen as A
from app.models.enums import DietaryLabel as D
from app.models.enums import OrderStatus, PaymentStatus, Role
from app.models.security import hash_password

DEMO_PASSWORD = "ektemat-demo"

CATEGORIES = [
    ("birthday", "Birthday"),
    ("confirmation", "Confirmation"),
    ("wedding", "Wedding"),
    ("conference", "Conference"),
    ("julebord", "Christmas party (julebord)"),
    ("corporate-lunch", "Corporate lunch"),
]

# name, description, price NOK, min order, categories, allergens, dietary labels, published
FOOD_ITEMS = [
    ("Fish soup with Bergen cod", "Creamy soup with cod, root vegetables and sourdough bread.",
     189, 10, ["conference", "corporate-lunch"], {A.FISH, A.MILK, A.GLUTEN, A.CELERY}, set(), True),
    ("Slow-cooked lamb from Voss", "Lamb from Voss with barley risotto.",
     245, 10, ["birthday", "confirmation", "conference"], {A.GLUTEN, A.MILK, A.CELERY}, set(), True),
    ("Beetroot and chickpea salad", "With goat cheese from Hardanger.",
     165, 10, ["conference", "corporate-lunch", "birthday"], {A.MILK, A.MUSTARD}, {D.VEGETARIAN}, True),
    ("Rakfisk tasting", "Seasonal, November only.",
     210, 10, ["julebord"], {A.FISH}, set(), False),
    ("Seasonal lunch buffet", "Changing buffet with local, seasonal produce.",
     229, 8, ["corporate-lunch", "birthday"], {A.GLUTEN, A.MILK}, set(), True),
    ("Vegetarian harvest menu", "Autumn vegetables, grains and nuts.",
     245, 10, ["conference", "birthday", "confirmation"], {A.GLUTEN, A.NUTS}, {D.VEGETARIAN}, True),
    ("Fish and seafood menu", "Fish and shellfish from the west coast.",
     495, 20, ["wedding", "birthday", "conference"], {A.FISH, A.CRUSTACEANS, A.MOLLUSCS, A.MILK}, set(), True),
    ("Meeting sandwiches", "Open sandwiches for meetings.",
     129, 6, ["corporate-lunch", "conference"], {A.GLUTEN, A.MILK, A.EGGS, A.MUSTARD}, set(), True),
    ("Konfirmasjon buffet", "Traditional buffet for confirmations.",
     395, 25, ["confirmation"], {A.GLUTEN, A.MILK, A.EGGS}, set(), True),
    ("Traditional julebord buffet", "Pinnekjøtt, ribbe and Christmas sides.",
     595, 20, ["julebord"], {A.GLUTEN, A.MILK, A.FISH, A.MUSTARD, A.CELERY}, set(), True),
    ("Wedding served dinner (3 courses)", "Served three-course dinner.",
     875, 40, ["wedding"], {A.GLUTEN, A.MILK, A.NUTS}, set(), True),
    ("Kids menu", "Child-sized portions for guests under 12.",
     149, 5, ["birthday", "confirmation", "wedding"], {A.GLUTEN, A.MILK}, {D.KIDS_FRIENDLY}, True),
]

USERS = [
    ("admin@ektemat.example", "Ekte Mat Admin", Role.ADMIN),
    ("kari.kunde@example.com", "Kari Kunde", Role.CUSTOMER),
    ("ola.kunde@example.com", "Ola Kunde", Role.CUSTOMER),
]

# Status changes needed to reach each status from "submitted" (docs/design/state-order.puml)
PATH_TO_STATUS = {
    OrderStatus.SUBMITTED: [],
    OrderStatus.APPROVED: [OrderStatus.APPROVED],
    OrderStatus.IN_PREPARATION: [OrderStatus.APPROVED, OrderStatus.IN_PREPARATION],
    OrderStatus.DELIVERED: [OrderStatus.APPROVED, OrderStatus.IN_PREPARATION, OrderStatus.DELIVERED],
    OrderStatus.REJECTED: [OrderStatus.REJECTED],
    OrderStatus.CANCELLED: [OrderStatus.APPROVED, OrderStatus.CANCELLED],
}

# customer e-mail, days from today, guests, address, [(item, qty)], [(group, count, allergies, notes)],
# final status, payment status
ORDERS = [
    ("kari.kunde@example.com", 14, 40, "Nygårdsgaten 5, 5015 Bergen",
     [("Slow-cooked lamb from Voss", 30), ("Kids menu", 10)],
     [("Adults", 30, set(), "3 vegetarian"), ("Children", 10, {A.NUTS}, "")],
     OrderStatus.SUBMITTED, PaymentStatus.NOT_PAID),
    ("ola.kunde@example.com", 120, 80, "Fana kulturhus, 5244 Fana",
     [("Wedding served dinner (3 courses)", 80)],
     [("Guests", 76, set(), "4 vegan"), ("Table 3", 4, {A.CRUSTACEANS, A.MOLLUSCS}, "")],
     OrderStatus.APPROVED, PaymentStatus.DEPOSIT_PAID),
    ("kari.kunde@example.com", 2, 40, "Fjordveien 10, 5003 Bergen",
     [("Meeting sandwiches", 25), ("Fish soup with Bergen cod", 15)],
     [("Participants", 40, {A.GLUTEN}, "2 halal")],
     OrderStatus.IN_PREPARATION, PaymentStatus.INVOICED),
    ("ola.kunde@example.com", -10, 45, "Åsane kirke, 5116 Ulset",
     [("Konfirmasjon buffet", 45)],
     [("Family", 45, {A.MILK}, "2 lactose-free")],
     OrderStatus.DELIVERED, PaymentStatus.PAID),
    ("kari.kunde@example.com", 5, 60, "Strandkaien 2, 5013 Bergen",
     [("Traditional julebord buffet", 60)],
     [("Staff", 60, set(), "")],
     OrderStatus.REJECTED, PaymentStatus.NOT_PAID),
    ("ola.kunde@example.com", 30, 12, "Torgallmenningen 1, 5014 Bergen",
     [("Seasonal lunch buffet", 12)],
     [("Guests", 12, set(), "1 vegetarian")],
     OrderStatus.CANCELLED, PaymentStatus.NOT_PAID),
]

# order index, question, answer (None = unanswered)
QUESTIONS = [
    (0, "Can the children's portions be served first?", None),
    (1, "How much is the deposit, and when must it be paid?",
     "The deposit is due 30 days before the wedding. We will send the amount by e-mail."),
    (2, "Can you deliver between 10:45 and 11:00?", None),
]


def seed(repos):
    """Insert the seed data. Returns False (and changes nothing) if data already exists."""
    if repos.categories.list_all():
        return False

    category_ids = {}
    for sort_order, (slug, name) in enumerate(CATEGORIES):
        category_ids[slug] = repos.categories.add(EventCategory(slug, name, sort_order)).id

    items = {}
    for name, description, price, min_order, slugs, allergens, labels, published in FOOD_ITEMS:
        items[name] = repos.food_items.add(FoodItem(
            name, description, price, min_order,
            category_ids=[category_ids[slug] for slug in slugs],
            allergens=allergens, dietary_labels=labels, published=published,
        ))

    users = {}
    for email, name, role in USERS:
        users[email] = repos.users.add(User(email, hash_password(DEMO_PASSWORD), name, role=role))
    admin = users["admin@ektemat.example"]

    orders = []
    for email, days, guests, address, lines, groups, status, payment in ORDERS:
        order = repos.orders.add(Order(
            customer_id=users[email].id,
            event_date=date.today() + timedelta(days=days),
            guest_count=guests,
            delivery_address=address,
            lines=[OrderLine(name, items[name].price_nok, qty, food_item_id=items[name].id) for name, qty in lines],
            guest_groups=[GuestGroup(label, count, allergies, notes) for label, count, allergies, notes in groups],
        ))
        for step in PATH_TO_STATUS[status]:
            order = repos.orders.update_status(order.id, step)
        if payment != PaymentStatus.NOT_PAID:
            order = repos.orders.update_payment_status(order.id, payment)
        orders.append(order)

    for index, text, answer in QUESTIONS:
        order = orders[index]
        question = repos.questions.add(Question(order.id, order.customer_id, text))
        if answer:
            repos.questions.answer(question.id, answer, admin.id)

    return True
