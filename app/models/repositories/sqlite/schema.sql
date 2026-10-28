-- Ekte Mat Online — SQLite schema (docs/design/domain-class.puml)
-- Constraints: OFFICIAL = Oblig 4 A3/C2; others are the essential rules agreed in docs/plans/03 §2 (ASSUMPTION).

PRAGMA foreign_keys = OFF;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS guest_group_allergens;
DROP TABLE IF EXISTS guest_groups;
DROP TABLE IF EXISTS order_lines;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS food_item_dietary_labels;
DROP TABLE IF EXISTS food_item_allergens;
DROP TABLE IF EXISTS food_item_categories;
DROP TABLE IF EXISTS food_items;
DROP TABLE IF EXISTS event_categories;
DROP TABLE IF EXISTS users;
PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name          TEXT NOT NULL,
    phone         TEXT,
    role          TEXT NOT NULL CHECK (role IN ('customer', 'admin')),
    created_at    TEXT NOT NULL
);

CREATE TABLE event_categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slug       TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE food_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    description    TEXT NOT NULL DEFAULT '',
    price_nok      INTEGER NOT NULL CHECK (price_nok > 0),            -- DV-03 (ASSUMPTION)
    min_order_qty  INTEGER NOT NULL CHECK (min_order_qty >= 1),       -- needed for C2 (OFFICIAL)
    published      INTEGER NOT NULL DEFAULT 0 CHECK (published IN (0, 1)),
    image_filename TEXT
);

CREATE TABLE food_item_categories (
    food_item_id INTEGER NOT NULL REFERENCES food_items(id) ON DELETE CASCADE,
    category_id  INTEGER NOT NULL REFERENCES event_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (food_item_id, category_id)
);

CREATE TABLE food_item_allergens (
    food_item_id INTEGER NOT NULL REFERENCES food_items(id) ON DELETE CASCADE,
    allergen     TEXT NOT NULL CHECK (allergen IN ('gluten', 'crustaceans', 'eggs', 'fish', 'peanuts',
                 'soy', 'milk', 'nuts', 'celery', 'mustard', 'sesame', 'sulphites', 'lupin', 'molluscs')),
    PRIMARY KEY (food_item_id, allergen)
);

CREATE TABLE food_item_dietary_labels (
    food_item_id INTEGER NOT NULL REFERENCES food_items(id) ON DELETE CASCADE,
    label        TEXT NOT NULL CHECK (label IN ('vegetarian', 'vegan', 'gluten_free', 'lactose_free',
                 'halal', 'kids_friendly')),
    PRIMARY KEY (food_item_id, label)
);

CREATE TABLE orders (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number     TEXT NOT NULL UNIQUE,                            -- DV-06
    customer_id      INTEGER NOT NULL REFERENCES users(id),
    event_date       TEXT NOT NULL,
    guest_count      INTEGER NOT NULL CHECK (guest_count >= 1),       -- DV-01 (ASSUMPTION)
    delivery_address TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'approved',
                     'in_preparation', 'delivered', 'rejected', 'cancelled')),           -- DV-07 (OFFICIAL)
    payment_status   TEXT NOT NULL DEFAULT 'not_paid' CHECK (payment_status IN ('not_paid',
                     'deposit_paid', 'invoiced', 'paid')),                                -- DV-08 (OFFICIAL)
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);
CREATE INDEX idx_orders_event_date ON orders(event_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_customer ON orders(customer_id);

-- No stored totals: totals are computed from lines (DV-05).
CREATE TABLE order_lines (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id       INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    food_item_id   INTEGER REFERENCES food_items(id) ON DELETE SET NULL,
    item_name      TEXT NOT NULL,
    unit_price_nok INTEGER NOT NULL CHECK (unit_price_nok > 0),
    quantity       INTEGER NOT NULL CHECK (quantity >= 1)
);

-- Per guest group, never per named guest (OB4 C3; GDPR note). DV-12.
CREATE TABLE guest_groups (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id      INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    label         TEXT NOT NULL,
    count         INTEGER NOT NULL CHECK (count >= 1),
    dietary_notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE guest_group_allergens (
    guest_group_id INTEGER NOT NULL REFERENCES guest_groups(id) ON DELETE CASCADE,
    allergen       TEXT NOT NULL CHECK (allergen IN ('gluten', 'crustaceans', 'eggs', 'fish', 'peanuts',
                   'soy', 'milk', 'nuts', 'celery', 'mustard', 'sesame', 'sulphites', 'lupin', 'molluscs')),
    PRIMARY KEY (guest_group_id, allergen)
);

CREATE TABLE questions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    author_id   INTEGER NOT NULL REFERENCES users(id),
    text        TEXT NOT NULL,
    asked_at    TEXT NOT NULL,
    answer_text TEXT,
    answered_by INTEGER REFERENCES users(id),
    answered_at TEXT
);
