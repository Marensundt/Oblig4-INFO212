# Ekte Mat Online

INFO212 Obligatory assignment 4: a Flask web application for the fictional Bergen caterer Ekte Mat AS, with a customer site (menu, cart, orders, questions) and an admin panel (food items, images, orders, questions). All data is synthetic.

Architecture: Model–View–Controller with Flask. See `CLAUDE.md` and `docs/plans/01-implementation-plan.md`.

## Requirements
- Python **3.11 or newer**
- Git

## Install
```bash
git clone https://github.com/Marensundt/Oblig4-INFO212.git
cd Oblig4-INFO212
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # optional: set SECRET_KEY; never commit .env
```

## Seed the database
```bash
flask --app run reset-db --yes     # create instance/ektemat.sqlite and add synthetic sample data
```
Separate steps: `flask --app run init-db` (empty tables; asks before deleting data) and `flask --app run seed-db` (adds sample data once; running it again changes nothing).

The seed creates 6 event categories, 12 food items, 6 orders (one in each order status) with guest groups, 3 questions, and these **demo accounts**:

| Role | E-mail | Password |
|---|---|---|
| Admin | `admin@ektemat.example` | `ektemat-demo` |
| Customer | `kari.kunde@example.com` | `ektemat-demo` |
| Customer | `ola.kunde@example.com` | `ektemat-demo` |

> The demo password is for **local testing with synthetic data only**. Never use it as a real or production password.

The database file is not under version control; delete it or run `reset-db` at any time to start again.

## Run
```bash
flask --app run run
```
Open http://127.0.0.1:5000

The start page is the **menu** (`/menu`): published food items as cards grouped by kind of event, each with picture, price, minimum order and allergens. No login is needed to browse.

Each card has an **Add to cart** form. The **cart** (`/cart`) lists the items with price × portions and an estimated total; you can change portions or remove items. Quantities below an item's minimum order are rejected with a message. The cart is kept in your browser session, also when you log in.

From the cart, **Continue to order** (`/account/checkout`) asks you to log in or register and then shows the order form: event date, number of guests, delivery address and one or more guest groups with allergies and dietary notes (no guest names). There is no payment step; the order is saved as *submitted* / *not paid* and you see a confirmation with the order number.

Log in at http://127.0.0.1:5000/account/login with a demo account (see above), or register a new customer account at `/account/register`. The admin panel (`/admin/`) is only available to the admin account; customers get "Access denied".

As admin you can manage the food items at `/admin/food`: add, edit, publish/unpublish and delete (items that are part of an order can only be unpublished).

## Test
```bash
pytest
```
Tests also run automatically on GitHub (Actions) for every pull request and push to `main`, on Python 3.11 and 3.13.

## Project structure
```
app/
  models/            model layer: domain classes, enums, seed data
    repositories/    interfaces + sqlite/ implementations (the only code that touches the database)
  views/templates/   view layer: Jinja2 templates
  controllers/       controller layer: blueprints shop, account, admin
  static/            CSS and JavaScript
tests/               pytest tests
docs/plans/          agreed plans (one per larger feature)
docs/backlog/        user stories, acceptance criteria, NFRs, traceability
docs/design/         UML diagrams (PlantUML + PNG)
```
