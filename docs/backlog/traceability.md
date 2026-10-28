# Traceability matrix

Links every official Oblig 4 requirement to stories, use cases, domain classes, implementation phases (`docs/plans/01-implementation-plan.md` §8), tests and report screenshots (OB4 §5 part 2).
Sources: OB4 = official assignment; stories in `user-stories.md`; UC in `docs/design/use-case.puml`; classes in `docs/design/domain-class.puml`; NFR in `non-functional.md`; DV in `data-validation-rules.md`.
"Tests" are planned test modules (to be created in the phases; none exist yet).

## 1. Functional requirements (OB4 §2, minimum — all Must)

| OB4 | Stories | Use cases | Domain classes | Phase | Planned tests | Report screenshot (OB4 §5.2) |
|---|---|---|---|---|---|---|
| A1 Food items | US-01, US-02, US-03 | UC-10 | FoodItem, EventCategory, Allergen, DietaryLabel | 3 | `tests/controllers/test_admin_food.py`, `tests/repositories/test_food_item_repository.py` | Admin: food item page |
| A2 Images | US-04, US-05 | UC-11, UC-12, UC-13 | FoodItem.imageFile (+ ImageService, model layer) | 9 | `tests/controllers/test_admin_images.py`, `tests/unit/test_image_service.py` | Admin: image page |
| A3 Orders | US-14, US-15, US-16 | UC-14, UC-15, UC-16 | Order, OrderLine, GuestGroup, OrderStatus, PaymentStatus | 7 | `tests/controllers/test_admin_orders.py`, `tests/unit/test_order_status.py` | Admin: order list, order page |
| A4 Questions | US-20 | UC-17 | Question, User | 8 | `tests/controllers/test_admin_questions.py` | (shown on admin order page) |
| C1 Menu by event | US-06 | UC-01 | FoodItem, EventCategory | 4 | `tests/controllers/test_shop_menu.py` | Customer: menu |
| C2 Shopping cart | US-08, US-09 | UC-02 | Cart, CartLine, FoodItem | 5 | `tests/unit/test_cart.py`, `tests/controllers/test_shop_cart.py` | Customer: cart |
| C3 Order | US-10, US-11, US-12, US-13 | UC-03, UC-04, UC-05, UC-06 | User, Order, OrderLine, GuestGroup | 2, 6 | `tests/controllers/test_account_auth.py`, `tests/controllers/test_account_checkout.py` | Customer: order form |
| C4 My orders | US-17 | UC-07 | Order, OrderStatus, PaymentStatus | 7 | `tests/controllers/test_account_orders.py` | Customer: my orders |
| C5 Questions | US-18, US-19 | UC-08, UC-09 | Question | 8 | `tests/controllers/test_account_questions.py` | Customer: questions |

Clause-level coverage (each part of each requirement → acceptance criterion): see the coverage table in `user-stories.md`.

## 2. Technical and process requirements (OB4 §3–§5)

| OB4 requirement | Covered by | Phase | Evidence |
|---|---|---|---|
| §3 MVC with Flask; three layers visible in folders | NFR-01; `mvc-architecture.puml`; 01-plan §3 | 0 | Folder structure; report part 3 |
| §3 Blueprints (e.g. shop, account, admin) | NFR-01; 01-plan §3, §5 | 0 | `app/controllers/` |
| §3 Only repository classes in the model layer touch storage; Neo4j can replace it without changing controllers/views | NFR-02; `mvc-architecture.puml`; `domain-class.puml` | 1 | grep check in tests; review |
| §3 Front end HTML/CSS/JS | 01-plan §1 (Jinja2 templates) | 0–10 | `app/views/templates/`, `app/static/` |
| §3 No Claude API key in the repository | NFR-03; US-05 AC4; NFR-19 | 0, 9, 10 | Secret search before PRs and tag |
| §3 Customer login | US-10, US-11; NFR-04 | 2 | Auth tests |
| §3 Synthetic data only; seed script with food items, admin, test customers | US-22; NFR-08 | 1 | Seed script; README |
| §3 README: install, seed, run, test | US-22; NFR-09 | 0, 10 | README walkthrough by every member |
| §4 CLAUDE.md (system, MVC layout, run/test, team rules; short and true) | `CLAUDE.md` | 0, 10 (keep updated) | File in repo |
| §4 Plan every larger feature; commit agreed plan to `docs/plans/` | 00-, 01-, 02-plans; ★ phases in 01-plan §8 | all | `docs/plans/` history |
| Group: every member commits | 01-plan §9 | all | GitHub Insights → Contributors |
| §5.1 Front page: members, repo link, tag `oblig4`, Neo4j yes/no | 01-plan §10 (Neo4j: no) | 10 | Report |
| §5.2 Features with screenshots (9 screens) | Column "Report screenshot" in table 1 | 10 | Report |
| §5.3 Software design with diagrams and how each was used | `docs/design/README.md`; user stories | done (draft) | Report |
| §5.4 Did design help? | — | 10 | Report paragraph |
| Approval: executable app, functionality, MVC, report parts 1–4 | All of the above | 10 | Manual walkthrough (01-plan §8) |

## 3. Optional "going further" (OB4 §2) — Should

| OB4 idea | Story | Stakeholder need | Phase |
|---|---|---|---|
| Kitchen view with allergies highlighted (Mateo) | US-23 | INT-M | 11 (optional) |
| Check against daily kitchen capacity (Sunniva) | US-24 (+ optional DV-02) | INT-S | 11 (optional) |
| Company accounts that copy last week's order (Fjordtek) | US-25 | INT-F | not planned |
| Origin of the food on every card (Ingrid) | US-27 | INT-I | not planned |
| Norwegian/English interface | US-26; NFR-17 | IT | 11 (optional) |

## 4. Proposed rules and targets (ASSUMPTION — not Oblig 4 requirements)

| Item | Where | Status |
|---|---|---|
| Data-validation rules DV-01 – DV-12 | `data-validation-rules.md` | Proposed; confirm before phase 1. DV-02 (400 guests) optional |
| Performance targets (2 s, 1 s, 5 000 orders) | NFR-11, NFR-12 | Proposed targets, not mandatory |
| Extra order-status transitions (cancel from approved/in_preparation) | `state-order.puml`, US-15 AC4 | Proposed; confirm with PO |
| Admin login | US-21, NFR-05 | Proposed (OB4 §3 ambiguous) |
