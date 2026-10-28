# 03 — Plan: phase 1, model layer and SQLite repositories

Status: **approved 2026-10-28** — OPEN-9 and OPEN-10 resolved as in §2; phase 1 owner: Juliadyrset; demo password approved for local testing with synthetic data only (never a production password).
Parent plan: `docs/plans/01-implementation-plan.md` §4, §6, §7, §8 (phase 1 ★).
Models: `docs/design/domain-class.puml`, `docs/design/state-order.puml`, `docs/design/mvc-architecture.puml`.
Labels: **[OFFICIAL]** Oblig 4 · **[DECISION]** agreed · **[ASSUMPTION]** our proposal · **[OPEN]** to decide.

## 1. Goal
Build the model layer that every later phase uses: domain classes, enums with the order-status rules, repository interfaces, SQLite repositories, the schema, a seed script and CLI commands. **No routes, forms or templates** in this phase.

- **[OFFICIAL]** "Models hold the domain classes and all data access"; "only repository classes in the model layer touch it, so that Neo4j can later replace it without changes to controllers or views" (OB4 §3).
- **[OFFICIAL]** "A seed script creates sample food items, an admin and test customers"; "synthetic data only"; README gives the seed command (OB4 §3).
- Stories: **US-22** (seed, README); groundwork for US-01 – US-20.

## 2. Proposed resolution of OPEN-9 and OPEN-10

### OPEN-9 — order-status transitions and payment status
OB4 A3 gives the states and the main path, "submitted → approved → in preparation → delivered, or rejected/cancelled", but not exactly when *rejected* and *cancelled* are allowed.

**Proposal (simplest reading of A3, already drawn in `state-order.puml`):**

| From | Allowed to | Basis |
|---|---|---|
| submitted | approved, rejected, cancelled | OFFICIAL main path; rejected/cancelled from submitted is the most direct reading of "or rejected/cancelled" |
| approved | in_preparation, cancelled | OFFICIAL main path; cancel = ASSUMPTION |
| in_preparation | delivered, cancelled | OFFICIAL main path; cancel = ASSUMPTION |
| delivered, rejected, cancelled | — (final) | ASSUMPTION |

- *Rejected* only from *submitted*: Ekte Mat rejects a request before accepting it. *Cancelled* from any non-final state: either side withdraws an accepted order.
- **Payment status:** any of the four official values (`not_paid`, `deposit_paid`, `invoiced`, `paid`) can be set at any time by the admin; default `not_paid`. No transition rules — A3 says "e.g." and C3 says no payment solution, so we keep it free. [ASSUMPTION]
- Rule lives in one place: `OrderStatus.can_change_to(new)`; the repository refuses illegal changes.

### OPEN-10 — which data-validation rules to enforce
OB4 does not require validation rules beyond the A3 values and the C2 minimum order. Proposal: enforce only rules that are **official** or **follow directly from an official field**, keep the rest as later-phase or optional.

| Rule | Decision | Where / phase | Basis |
|---|---|---|---|
| DV-07 order status in official list | **Enforce** | enum + DB `CHECK`, phase 1 | OFFICIAL A3 |
| DV-08 payment status in official list, default `not_paid` | **Enforce** | enum + DB `CHECK`, phase 1 | OFFICIAL A3 |
| Minimum order quantity ≥ 1 on every item | **Enforce** | DB `CHECK`, phase 1 | needed for OFFICIAL C2 ("below an item's minimum order") |
| Quantity ≥ item minimum order in cart | **Enforce** | `Cart`, phase 5 | OFFICIAL C2 |
| DV-01 guests ≥ 1; guest-group count ≥ 1; line quantity ≥ 1 | **Enforce** | DB `CHECK`, phase 1; form in phase 6 | follows from "number of guests" (C3); cheap; ASSUMPTION |
| DV-03 price > 0 | **Enforce** | DB `CHECK`, phase 1; form in phase 3 | follows from "price in NOK" (A1); ASSUMPTION |
| DV-05 totals computed, never stored | **Enforce** (by design) | `Order.total_nok` property | ASSUMPTION; no extra code |
| DV-06 unique order number | **Enforce** (by design) | DB `UNIQUE`, generated | ASSUMPTION; no extra code |
| DV-12 separate fields per guest group, no names | **Enforce** (by design) | schema | OFFICIAL C3 "per guest group" + GDPR note |
| DV-09 fixed lists for categories, allergens, labels | **Enforce** (by design) | enums + lookup table | follows from A1 fields; ASSUMPTION |
| DV-04 event date in the future | Later | form validation, phase 6 | ASSUMPTION |
| DV-10 ≥ 1 event category per item | Later | form validation, phase 3 | ASSUMPTION (needed for C1 grouping) |
| DV-11 ≥ 1 guest group per order; counts ≤ guests | Later | form validation, phase 6 | ASSUMPTION |
| DV-02 > 400 guests warning | **Not planned** (optional) | only with optional US-24 | ASSUMPTION, not mandatory |
| Performance targets NFR-11/12 | **Not planned** (optional) | — | ASSUMPTION, not mandatory |

**Decision (2026-10-28):** implement the official rules and the essential integrity rules marked *Enforce* (each keeps its OFFICIAL/ASSUMPTION label); rules marked *Later* are built with their forms; *Not planned* rules stay documented as optional only.

After approval, `01-implementation-plan.md` §12 (OPEN-9, OPEN-10) and `data-validation-rules.md` get a "decision" column; rules stay labelled ASSUMPTION unless official.

## 3. Files

```
app/models/
├── __init__.py
├── enums.py              Role, OrderStatus (+ ALLOWED_TRANSITIONS, can_change_to), PaymentStatus,
│                         Allergen (14 EU allergens), DietaryLabel — StrEnum (Python 3.11+)
├── entities.py           dataclasses: User, EventCategory, FoodItem, OrderLine, GuestGroup, Order, Question
├── errors.py             DomainError, InvalidStatusTransition, NotFound, DuplicateEmail
├── security.py           hash_password / check_password (werkzeug.security; already a Flask dependency)
├── seed.py               seed(repos) — synthetic data, inserted through repositories only; idempotent
└── repositories/
    ├── __init__.py
    ├── interfaces.py     abstract classes UserRepository, EventCategoryRepository, FoodItemRepository,
    │                     OrderRepository, QuestionRepository (domain objects in/out, no SQL types)
    ├── factory.py        Repositories (dataclass), build_repositories(config), init_storage(config)
    └── sqlite/
        ├── __init__.py
        ├── database.py   SqliteDatabase(path): connect() context manager (foreign_keys ON, Row factory,
        │                 commit/rollback), init_schema()
        ├── schema.sql
        ├── user_repository.py
        ├── event_category_repository.py
        ├── food_item_repository.py
        ├── order_repository.py
        └── question_repository.py
app/cli.py                flask commands init-db, seed-db, reset-db (call factory/seed — no SQL here)
app/__init__.py           (changed) app.repos = build_repositories(app.config); register CLI commands
```

`Cart`/`CartLine` (session, not stored) are built in phase 5; `ImageService` in phase 9.

### Domain classes (`entities.py`) — from `domain-class.puml`
| Class | Fields | Behaviour |
|---|---|---|
| `User` | id, email, password_hash, name, phone, role, created_at | `is_admin` |
| `EventCategory` | id, slug, name, sort_order | — |
| `FoodItem` | id, name, description, price_nok, min_order_qty, category_ids, allergens, dietary_labels, published, image_filename | — |
| `OrderLine` | id, food_item_id (nullable), item_name, unit_price_nok, quantity | `line_total_nok` |
| `GuestGroup` | id, label, count, allergies, dietary_notes | — (no name field) |
| `Order` | id, order_number, customer_id, event_date, guest_count, delivery_address, status, payment_status, created_at, updated_at, lines, guest_groups | `total_nok` (computed), `change_status(new)` (uses `can_change_to`, raises `InvalidStatusTransition`) |
| `Question` | id, order_id, author_id, text, asked_at, answer_text, answered_by, answered_at | `is_answered` |

`id` is `None` until stored. IDs are plain `int` now; the Neo4j implementation in Oblig 5 can map them to its own IDs inside the repositories [ASSUMPTION].

### Repository methods (`interfaces.py`) — from 01-plan §6
| Repository | Methods |
|---|---|
| `UserRepository` | `add(user) -> User`, `get(id)`, `get_by_email(email)`, `list_customers()` |
| `EventCategoryRepository` | `add(category)`, `list_all()`, `get_by_slug(slug)` |
| `FoodItemRepository` | `add(item)`, `update(item)`, `delete(id)`, `get(id)`, `get_many(ids)`, `list_all()`, `list_published_by_category() -> list[(EventCategory, list[FoodItem])]`, `is_used_in_orders(id)` |
| `OrderRepository` | `add(order) -> Order` (order + lines + guest groups in **one transaction**, generates `order_number`), `get(id)`, `list(status=None, date_from=None, date_to=None)` (sorted by event date), `list_for_customer(user_id)`, `update_status(id, new_status)` (checks transition), `update_payment_status(id, payment_status)` |
| `QuestionRepository` | `add(question)`, `list_for_order(order_id)`, `list_all()` (unanswered first), `answer(id, text, admin_id)` |

Order number format `YY-NNNN` (e.g. `26-0001`), matching the data pack's order IDs [ASSUMPTION].

### Schema (`schema.sql`)
Tables: `users`, `event_categories`, `food_items`, `food_item_categories`, `food_item_allergens`, `food_item_dietary_labels`, `orders`, `order_lines`, `guest_groups`, `guest_group_allergens`, `questions`.
Constraints from §2 only: `CHECK` status and payment-status lists; `price_nok > 0`; `min_order_qty >= 1`; `guest_count >= 1`; `count >= 1`; `quantity >= 1`; `UNIQUE` email, slug, order_number; foreign keys with `ON DELETE CASCADE` for an order's lines/groups/questions and `ON DELETE SET NULL` for `order_lines.food_item_id`. Allergens/labels stored as text values checked against the enum lists. No stored totals.

### CLI commands (`app/cli.py`)
| Command | Does |
|---|---|
| `flask --app run init-db` | Creates the schema in `instance/ektemat.sqlite`; asks for confirmation if tables exist (drops them) |
| `flask --app run seed-db` | Inserts seed data through repositories; does nothing if data already exists (US-22 AC3) |
| `flask --app run reset-db` | init-db (no prompt with `--yes`) + seed-db |

## 4. Seed data (synthetic only) [OFFICIAL: food items, admin, test customers]
- **Event categories (6):** birthday, confirmation, wedding, conference, julebord [OFFICIAL examples from C1] + corporate lunch [ASSUMPTION, from kick-off notes].
- **Food items (12):** the table in 01-plan §7 (names/prices from the data pack; min orders, categories, allergens = ASSUMPTION). Rakfisk unpublished.
- **Users:** `admin@ektemat.example` (admin), `kari.kunde@example.com` and `ola.kunde@example.com` (customers). Demo password `ektemat-demo` for all, documented in README as **local demo only, synthetic data, never a production password**; stored hashed.
- **Orders (6)**, one per order status, with different payment statuses, 1–3 lines and 1–2 guest groups each (e.g. "Adults" 40 / "Children" 10 with nuts).
- **Questions (3):** 1 answered, 2 unanswered.
- No text copied from the customer e-mails; all names fictional and with `example` domains.

## 5. Tests
| File | Covers |
|---|---|
| `tests/unit/test_enums.py` | every allowed and every forbidden status transition (table in §2); final states |
| `tests/unit/test_entities.py` | `Order.total_nok`, `OrderLine.line_total_nok`, `Order.change_status` raises on illegal change, `Question.is_answered`, password hashing |
| `tests/repositories/test_user_repository.py` | add/get/get_by_email; duplicate email refused |
| `tests/repositories/test_food_item_repository.py` | round trip incl. categories/allergens/labels; update; delete; `list_published_by_category` (unpublished hidden, item in 2 categories appears twice); `is_used_in_orders`; `price_nok = 0` and `min_order_qty = 0` refused by DB |
| `tests/repositories/test_order_repository.py` | add with lines + groups in one transaction (rollback if a line is invalid); unique order numbers; filters by status and date range; `list_for_customer`; `update_status` legal/illegal; `update_payment_status`; status outside list refused by DB |
| `tests/repositories/test_question_repository.py` | add, list for order, unanswered first, answer |
| `tests/test_seed.py` | counts (6 categories, 12 items, 1 admin, ≥ 2 customers, 6 orders covering all statuses); idempotent; e-mails only on `example` domains |
| `tests/test_cli.py` | `reset-db --yes` creates and seeds a temp DB (Flask CLI runner) |
| `tests/test_persistence.py` | data written by one app instance is read by a new app instance on the same file (restart) |
| `tests/test_smoke.py` (existing) | `sqlite3` still only in `repositories/sqlite/` |

All repository tests use a temporary database (`tmp_path`). Expected size: ~50 tests.

## 6. Acceptance criteria (from 01-plan §8, phase 1)
1. `flask --app run reset-db --yes` creates `instance/ektemat.sqlite` with the seed data; restarting the app keeps the data.
2. Every repository method has at least one test; all tests pass locally and in GitHub Actions (3.11, 3.13).
3. `sqlite3` is imported only in `app/models/repositories/sqlite/` (existing test).
4. Controllers and templates are unchanged apart from `app/__init__.py` wiring.
5. README and CLAUDE.md list the seed commands and demo logins.

## 7. Documentation updates in the same branch
- `README.md`: "Seed the database" section and demo accounts.
- `CLAUDE.md`: seed command; rule "use `current_app.repos`, never open the database in controllers".
- `docs/plans/01-implementation-plan.md` §12: OPEN-9 and OPEN-10 marked resolved with the decisions from §2.
- `docs/backlog/data-validation-rules.md`: decision column (enforce now / later / not planned).
- `docs/design/domain-class.puml`: re-render only if the model changes during implementation.

## 8. Commits (branch `feature/1-model-layer`)
1. Add enums and domain entities (+ unit tests)
2. Add repository interfaces and SQLite database helper with schema
3. Add SQLite repositories (+ repository tests)
4. Add seed data and CLI commands (+ seed/CLI/persistence tests)
5. Update README, CLAUDE.md and plans with phase 1 decisions

Commit 0 is this plan (plan mode: commit the agreed plan before building). Owner [DECISION]: **Juliadyrset** (S1 role for phase 1). Every member must commit from their own account [OFFICIAL "Every member commits"]; other members take later phases.

## 9. Out of scope for phase 1
Login/register (phase 2), any page or form, cart (phase 5), image service (phase 9), Neo4j (Oblig 5).
