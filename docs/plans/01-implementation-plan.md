# 01 — Implementation plan: Ekte Mat Online (Flask, MVC, repositories)

Status: **proposed — awaiting approval** (rev. 3, 28 Oct 2026 — linked to backlog and design models)
Inputs: official assignment *INFO212 Oblig 4 — Building Ekte Mat Online with Claude Code* (kept local in git-ignored `docs/assignment/`), `CLAUDE.md`, `docs/plans/00-requirements-analysis.md`, `EkteMat_project_inbox/` (read only).
Backlog and models (replacing the uncompleted Lab 7 deliverables, see `docs/plans/02-backlog-and-design-plan.md`): `docs/backlog/` (stakeholders, user stories US-01 – US-31 with acceptance criteria, non-functional requirements, proposed data-validation rules, conflicts, traceability) and `docs/design/` (use case, domain class, sequence, order state machine, MVC architecture — PlantUML + PNG).

**Labels used in this plan**
- **[OFFICIAL]** — stated in the assignment PDF.
- **[DECISION]** — decided by the team/product owner in this project.
- **[ASSUMPTION]** — our proposal; not required, can be changed.
- **[OPEN]** — ambiguity or missing information; must be resolved (see §12).

## 1. Goals and scope

- **[OFFICIAL]** Build a working first version of Ekte Mat Online: a customer site (C1–C5) and an admin panel (A1–A4), with Claude Code as coding agent and GitHub as shared workspace. Group of 2–4; **every member commits**.
- **[OFFICIAL]** Start from the data pack and the Lab 7 backlog and models. Extra features are allowed if we can **name the stakeholder need** each serves.
- **[OFFICIAL]** Process matters: plan, build, test, review — and judge whether the agent's work is right.
- **[DECISION]** Four students, each committing and pushing from their **own GitHub account**.
- **[DECISION]** Storage: SQLite now; **Neo4j is not included in Oblig 4** (report front page: "Neo4j: no"). Repository classes are designed so Neo4j can replace SQLite in Oblig 5.

### Optional "going further" features [OFFICIAL list, not planned for the first version]
| Feature | Stakeholder need | Plan |
|---|---|---|
| Kitchen view of the day's orders, allergies highlighted | Mateo (head chef) | Candidate if time allows (phase 11) |
| Check against daily kitchen capacity (≈400 / 250 with served wedding) | Sunniva (event coordinator) | Candidate (phase 11) |
| Company accounts that can copy last week's order | Fjordtek (corporate customer) | Not planned |
| Origin of the food on every card | Ingrid (owner) | Not planned |
| Norwegian/English interface | Constraint in IT landscape; E012 | Candidate (phase 11) |

Other case needs (Vipps, Fiken/EHF, reminders, offline kitchen, GDPR self-service) remain backlog items from `00-requirements-analysis.md`.

### Key design decisions
| Decision | Choice | Label |
|---|---|---|
| Backend | Flask | [OFFICIAL] |
| Architecture | MVC; three layers visible in folder structure | [OFFICIAL] |
| Views | Jinja2 templates (server-rendered HTML, CSS, a little JavaScript) | [OFFICIAL] option; choice of Jinja2 over JSON API + React/Vue is [ASSUMPTION] |
| Controllers | Flask routes in blueprints **shop**, **account**, **admin** | [OFFICIAL] example names; adopted as [DECISION] |
| Data access | Only repository classes in the model layer touch storage | [OFFICIAL] |
| Temporary store | File-based SQLite `instance/ektemat.sqlite`, git-ignored | [OFFICIAL] allows SQLite/JSON; file-based SQLite is [DECISION] |
| Domain objects | Python `dataclasses` + `Enum`s, no ORM | [ASSUMPTION] (keeps Neo4j switch simple) |
| App factory | `create_app()` | [ASSUMPTION] (testability) |
| Forms / CSRF | Flask-WTF | [ASSUMPTION] |
| Auth | Flask session + Werkzeug password hashing; roles `customer` / `admin` | Customer login [OFFICIAL]; admin login is [ASSUMPTION] — see [OPEN-2] |
| Cart | Flask session `{item_id: qty}` | [ASSUMPTION] |
| Money | Whole NOK as `int` | [ASSUMPTION] |
| Secrets | API keys only via environment variables (`.env`, git-ignored; `.env.example` committed) | No Claude API key in repo is [OFFICIAL] |
| Data | Synthetic data only | [OFFICIAL] |
| Dependencies | `Flask`, `Flask-WTF`, `python-dotenv`, `pytest`; optional `anthropic` for A2 | [ASSUMPTION] |

## 2. Requirement → implementation task mapping [OFFICIAL requirements A1–A4, C1–C5]

Stories, use cases, tests and report screenshots per requirement: `docs/backlog/traceability.md`. Acceptance criteria in `docs/backlog/user-stories.md` are the definition of done for each phase.

| Req | Stories | Use cases |
|---|---|---|
| A1 | US-01 – US-03 | UC-10 |
| A2 | US-04, US-05 | UC-11 – UC-13 |
| A3 | US-14 – US-16 | UC-14 – UC-16 |
| A4 | US-20 | UC-17 |
| C1 | US-06 | UC-01 |
| C2 | US-08, US-09 | UC-02 |
| C3 | US-10 – US-13 | UC-03 – UC-06 |
| C4 | US-17 | UC-07 |
| C5 | US-18, US-19 | UC-08, UC-09 |

| Req | Official text (short) | Tasks | Model / repository | Controller | Templates | Phase |
|---|---|---|---|---|---|---|
| **A1 Food items** | Add, edit, remove: name, description, price NOK, min order qty, event categories, allergens + dietary labels, published | Admin list (published + drafts); create/edit/delete form; validation (price > 0, min order ≥ 1, ≥ 1 category) [ASSUMPTION; OPEN-10] — done in phase 3, see `docs/plans/04`; items used in orders cannot be deleted, only unpublished [ASSUMPTION] | `FoodItem`, `EventCategory`, `Allergen`, `DietaryLabel`; `FoodItemRepository`, `EventCategoryRepository` | admin | `admin/food/list.html`, `admin/food/form.html` | 3 |
| **A2 Images** | Upload a picture, **or** write an instruction an AI agent/image service uses to create or modify it; admin previews before saving | (a) upload JPG/PNG/WebP/SVG ≤ 2 MB; (b) instruction → `ImageService`; (c) preview page with *Save* / *Discard*; only *Save* updates the item | `FoodItem.image_filename`; `ImageService` interface; `ImageStorage` | admin | `admin/food/image.html`, `admin/food/image_preview.html` | 9 |
| **A3 Orders** | List filterable by status and event date; page per order; order status submitted → approved → in preparation → delivered, or rejected/cancelled; payment status (e.g. not paid, deposit paid, invoiced, paid) | List with status + date-range filter; detail page (lines, guest groups, allergies highlighted, total); change order status (allowed transitions only) and payment status | `Order`, `OrderLine`, `GuestGroup`, `OrderStatus`, `PaymentStatus`; `OrderRepository` | admin | `admin/orders/list.html`, `admin/orders/detail.html` | 7 |
| **A4 Questions** | Read and answer customers' questions about their orders | Question list (unanswered first, link to order); answer form | `Question`; `QuestionRepository` | admin | `admin/questions/list.html` + thread on order page | 8 |
| **C1 Menu by event** | Cards grouped by event (birthday, confirmation, wedding, conference, julebord, …); card: picture, price, min order, allergens | Public menu of published items grouped by category (item may appear in several); placeholder image if none; "add to cart" | `FoodItemRepository.list_published_by_category()` | shop | `shop/menu.html`, `_partials/food_card.html` | 4 |
| **C2 Shopping cart** | Add, change, remove; estimated total; quantities below minimum not accepted | `Cart` model (pure logic); add/update/remove; total; reject qty < min order; drop items no longer published | `Cart` | shop | `shop/cart.html` | 5 |
| **C3 Order** | Log in (or register) and submit: event date, number of guests, delivery address, allergy and dietary notes **per guest group**; no payment solution | Login-gated checkout with return URL; register; order form with dynamic guest-group rows; validation; save order as `submitted` / `not_paid` in one transaction; price snapshot; clear cart; confirmation | `User`, `Order`, `GuestGroup`; `UserRepository`, `OrderRepository.add()` | account | `account/login.html`, `account/register.html`, `account/checkout.html`, `account/confirmation.html` | 2, 6 |
| **C4 My orders** | Customer's own orders with current status and payment status | List + detail; only own orders (others → 404) | `OrderRepository.list_for_customer()` | account | `account/orders.html`, `account/order_detail.html` | 7 |
| **C5 Questions** | Ask a question about a specific order and read the answer | Question form + thread on own order page | `QuestionRepository.add()`, `list_for_order()` | account | `account/order_detail.html` | 8 |

**Order status state machine** (`docs/design/state-order.puml`) — states [OFFICIAL]; exact transitions [ASSUMPTION]:
`submitted → approved → in_preparation → delivered`; `submitted → rejected`; `submitted | approved | in_preparation → cancelled`. `delivered`, `rejected`, `cancelled` are final. Enforced in the model (`OrderStatus.can_change_to()`), drawn as a state machine diagram for the report.
**Payment status** — values [OFFICIAL, "e.g."]: `not_paid`, `deposit_paid`, `invoiced`, `paid`; set manually by admin, no transition rules [ASSUMPTION].

## 3. Folder structure — three MVC layers visible [OFFICIAL]

```
Oblig4-INFO212/
├── CLAUDE.md                    # project briefing [OFFICIAL]
├── README.md                    # install, seed, run, test commands [OFFICIAL]
├── requirements.txt
├── .env.example                 # names of env vars, no values (e.g. ANTHROPIC_API_KEY=)
├── config.py                    # Config / TestConfig
├── run.py
├── app/
│   ├── __init__.py              # create_app(): config, repositories, blueprints, CLI commands
│   ├── models/                  # ── MODEL: domain classes + all data access ──
│   │   ├── entities.py          # User, EventCategory, FoodItem, Order, OrderLine, GuestGroup, Question
│   │   ├── enums.py             # Role, OrderStatus (+ transitions), PaymentStatus, Allergen, DietaryLabel
│   │   ├── cart.py              # Cart rules (min order, totals) — no Flask/DB imports
│   │   ├── image_service.py     # ImageService interface + Placeholder / Claude-SVG implementations
│   │   ├── seed.py              # synthetic seed data, inserted via repositories
│   │   └── repositories/
│   │       ├── interfaces.py    # abstract repository classes (storage-agnostic)
│   │       ├── factory.py       # build_repositories(config) — the single swap point for Neo4j
│   │       └── sqlite/          # ONLY place that imports sqlite3 / contains SQL
│   │           ├── connection.py  schema.sql
│   │           ├── user_repository.py  food_item_repository.py  event_category_repository.py
│   │           └── order_repository.py  question_repository.py
│   ├── controllers/             # ── CONTROLLER: Flask blueprints ──
│   │   ├── shop.py              # C1 menu, C2 cart
│   │   ├── account.py           # login/register, C3 checkout, C4 my orders, C5 questions
│   │   ├── admin.py             # A1 food items, A2 images, A3 orders, A4 questions
│   │   ├── decorators.py        # login_required, admin_required
│   │   └── forms.py             # WTForms classes
│   ├── views/
│   │   └── templates/           # ── VIEW: Jinja2 ──
│   │       ├── base.html  _partials/  errors/
│   │       ├── shop/  account/
│   │       └── admin/food/  admin/orders/  admin/questions/
│   └── static/css/  static/js/  static/img/placeholder.svg
├── instance/                    # git-ignored: ektemat.sqlite, uploads/
├── tests/
│   ├── conftest.py              # app/client fixtures with temp DB; login helpers
│   ├── unit/  repositories/  controllers/
└── docs/
    ├── plans/                   # 00-, 01-, 02- … one committed plan per larger feature [OFFICIAL]
    └── report/                  # diagrams + screenshots for the PDF (PDF itself built outside repo)
```

If `admin.py` grows too large, it may be split into a package `controllers/admin/` with one module per area, still registered as the single `admin` blueprint [ASSUMPTION].

**Layer rules** [OFFICIAL in substance]: controllers handle HTTP, forms and redirects and call repositories through `current_app.repos`; templates only render; domain rules (status transitions, cart rules, totals) live in `app/models/`; only `app/models/repositories/sqlite/` touches the database. Replacing SQLite with Neo4j must require **no changes to controllers or views** [OFFICIAL].

## 4. Models

The domain model is **`docs/design/domain-class.puml`** (rendered `docs/design/img/domain-class.png`). Fields required by OB4 A1/A3/C3 are [OFFICIAL]; everything else, including constraints in `{ }`, is [ASSUMPTION]. Implementation adds technical IDs (`id`, foreign keys) that the analysis model omits.

| Entity | Fields (implementation view) |
|---|---|
| `User` | id, email (unique), password_hash, name, phone, role (`customer`/`admin`), created_at |
| `EventCategory` | id, slug, name, sort_order — seed: birthday, confirmation, wedding, conference, julebord [OFFICIAL examples] + corporate lunch [ASSUMPTION] |
| `FoodItem` | id, name, description, price_nok, min_order_qty, category_ids, allergens, dietary_labels, published, image_filename |
| `Cart` / `CartLine` | session-held; lines of (food_item_id, quantity); computed estimated total |
| `Order` | id, order_number, customer_id, event_date, guest_count, delivery_address, status, payment_status, created_at, updated_at, lines, guest_groups, `total_nok` (computed) |
| `OrderLine` | id, order_id, food_item_id (nullable), item_name (snapshot), unit_price_nok (snapshot), quantity |
| `GuestGroup` | id, order_id, label, count, allergies, dietary_notes — **no guest names** (GDPR note in data pack) |
| `Question` | id, order_id, author_id, text, created_at, answer_text, answered_by (→ User), answered_at |

Changes from rev. 2 (after domain modelling): `CartLine` added; `FoodItem.unit` dropped (all data-pack prices are per person); `OrderLine.food_item_id` nullable so deleted items do not break order history; `answered_by` is a reference to the admin user.
Allergens: the 14 EU allergens [ASSUMPTION]. Dietary labels: vegetarian, vegan, gluten-free, lactose-free, halal, kids-friendly [ASSUMPTION].

## 5. Routes

| Method + path | Blueprint | Access | Req |
|---|---|---|---|
| `GET /` → `/menu`; `GET /menu` | shop | public | C1 |
| `GET /cart`; `POST /cart/add`, `/cart/update`, `/cart/remove/<item_id>` | shop | public | C2 |
| `GET /uploads/<filename>` | shop | public | C1/A2 |
| `GET/POST /account/register`, `/account/login`; `POST /account/logout` | account | public | C3 |
| `GET/POST /account/checkout`; `GET /account/checkout/confirmation/<order_id>` | account | customer | C3 |
| `GET /account/orders`; `GET /account/orders/<id>`; `POST /account/orders/<id>/questions` | account | customer (own) | C4, C5 |
| `GET /admin` (dashboard: new orders, unanswered questions) | admin | admin | A3/A4 |
| `GET /admin/food`; `GET/POST /admin/food/new`, `/admin/food/<id>/edit`; `POST /admin/food/<id>/delete` | admin | admin | A1 |
| `GET/POST /admin/food/<id>/image`; `GET …/image/preview`; `POST …/image/save`, `…/image/discard` | admin | admin | A2 |
| `GET /admin/orders?status=&from=&to=`; `GET /admin/orders/<id>`; `POST /admin/orders/<id>/status`, `/payment` | admin | admin | A3 |
| `GET /admin/questions`; `POST /admin/questions/<id>/answer` | admin | admin | A4 |

All state-changing routes are `POST` with CSRF token [ASSUMPTION].

## 6. Repositories [OFFICIAL principle; method list ASSUMPTION]

| Repository | Methods |
|---|---|
| `UserRepository` | `get(id)`, `get_by_email(email)`, `add(user)` |
| `EventCategoryRepository` | `list_all()`, `get_by_slug(slug)` |
| `FoodItemRepository` | `list_all()`, `list_published_by_category()`, `get(id)`, `get_many(ids)`, `add(item)`, `update(item)`, `delete(id)`, `is_used_in_orders(id)` |
| `OrderRepository` | `add(order)` (one transaction), `get(id)`, `list(status, date_from, date_to)`, `list_for_customer(user_id)`, `update_status(id, status)`, `update_payment_status(id, status)`, `next_order_number()` |
| `QuestionRepository` | `add(question)`, `list_for_order(order_id)`, `list_all(unanswered_first=True)`, `answer(id, text, admin_id)` |

Interfaces are abstract classes that accept and return domain objects only (never `sqlite3.Row`, never SQL or Cypher). `factory.build_repositories(config)` returns a `Repositories` object attached to the app. **Neo4j path (Oblig 5):** add `repositories/neo4j/` implementing the same interfaces, switch in `factory.py`, and run the same repository test suite against it.

## 7. Temporary SQLite database and seed data

- **[OFFICIAL]** A temporary store (SQLite or JSON) is fine; only repositories touch it; Neo4j replaces it later.
- **[DECISION]** File-based SQLite at `instance/ektemat.sqlite`: data persists between restarts; the file is git-ignored and can be deleted and recreated from code at any time.
- Schema `schema.sql`: `users`, `event_categories`, `food_items`, `food_item_categories`, `food_item_allergens`, `food_item_dietary_labels`, `orders`, `order_lines`, `guest_groups`, `guest_group_allergens`, `questions`; foreign keys on. CHECK constraints for the official status and payment-status values (OB4 A3), plus the **proposed** rules in `docs/backlog/data-validation-rules.md` (DV-01 – DV-12, [ASSUMPTION]) once the team has confirmed them — DV-02 (400 guests) is optional.
- CLI commands [ASSUMPTION names]: `flask --app run init-db`, `flask --app run seed-db`, `flask --app run reset-db`. Seeding goes through the repositories, so it will also work with Neo4j.
- **[OFFICIAL]** Seed script creates **sample food items, an admin and test customers**; **synthetic data only**.
- Tests use a temporary database per test and never touch `instance/`.

Seed food items — names/prices from the data pack (autumn menu + order export); **minimum orders, categories and allergens are [ASSUMPTION]** (not in the data pack; to confirm with the Lab 7 backlog):

| Item | Price NOK | Min order | Categories | Allergens / labels | Published |
|---|---|---|---|---|---|
| Fish soup with Bergen cod | 189 | 10 | conference, corporate lunch | fish, milk, gluten, celery | yes |
| Slow-cooked lamb from Voss, barley risotto | 245 | 10 | birthday, confirmation, conference | gluten, milk, celery | yes |
| Beetroot & chickpea salad, Hardanger goat cheese | 165 | 10 | conference, corporate lunch, birthday | milk, mustard / vegetarian | yes |
| Rakfisk tasting (Nov only) | 210 | 10 | julebord | fish | **no** |
| Seasonal lunch buffet | 229 | 8 | corporate lunch, birthday | gluten, milk | yes |
| Vegetarian harvest menu | 245 | 10 | conference, birthday, confirmation | gluten, nuts / vegetarian | yes |
| Fish & seafood menu | 495 | 20 | wedding, birthday, conference | fish, crustaceans, molluscs, milk | yes |
| Meeting sandwiches | 129 | 6 | corporate lunch, conference | gluten, milk, eggs, mustard | yes |
| Konfirmasjon buffet | 395 | 25 | confirmation | gluten, milk, eggs | yes |
| Traditional julebord buffet | 595 | 20 | julebord | gluten, milk, fish, mustard, celery | yes |
| Wedding served dinner (3 courses) | 875 | 40 | wedding | gluten, milk, nuts | yes |
| Kids menu (need from e-mail E027) | 149 | 5 | birthday, confirmation, wedding | gluten, milk / kids-friendly | yes |

Users: one admin (`admin@ektemat.example`) and two test customers; demo passwords documented in README for local use only. Orders: ~6 demo orders covering every order and payment status, with guest groups and 3 questions (2 unanswered). No data copied from the e-mail export.

## 8. Implementation phases

**[OFFICIAL] Plan mode:** every larger feature is planned before it is built, and the agreed plan is **committed to `docs/plans/`** before implementation starts. Phases marked ★ get their own plan file (`02-…`, `03-…`).

A phase is **done** when the acceptance criteria of its stories (`docs/backlog/user-stories.md`, mapped in `docs/backlog/traceability.md`) pass as automated tests, `pytest` is green, and the PR is reviewed and merged. The acceptance criteria column below summarises them. Performance targets (NFR-11, NFR-12) are optional [ASSUMPTION] and not part of any phase's definition of done.

| # | Phase | Main tasks | Tests | Acceptance criteria |
|---|---|---|---|---|
| **0** | Project setup | `requirements.txt`, `config.py`, `run.py`, `create_app`, empty `shop`/`account`/`admin` blueprints, `base.html`, `.env.example`, README skeleton, `pytest` + `conftest.py`, PR template; update CLAUDE.md "Run and test" | smoke test: app starts, `/` responds | Fresh clone → install → run shows a page; `pytest` passes |
| **1** ★ | Model layer + DB | entities, enums + status transitions, repository interfaces, SQLite repositories, schema, seed, `init-db`/`seed-db`/`reset-db` | unit: transitions; repository round-trip tests for every method on temp DB | `reset-db` creates DB with seed data; data survives restart; `sqlite3` imported only in `repositories/sqlite/` |
| **2** | Auth + layout | register, login, logout, hashing, decorators, navigation, flash messages, 403/404 pages | login/logout; wrong password; customer on `/admin` → 403; anonymous → login redirect | Customer and admin can log in; customer cannot reach admin |
| **3** ★ | A1 Food items | admin CRUD, validation, categories/allergens/labels, unpublish | create/edit/delete; invalid input rejected; delete blocked if used in orders | Admin manages every A1 field; changes persist |
| **4** | C1 Menu by event | menu grouped by category, cards, allergen badges, placeholder image | only published shown; multi-category item shown in each group; card fields present | Menu matches seed; unpublished item disappears |
| **5** | C2 Cart | `Cart` model, add/update/remove, total, min-order validation | `Cart` unit tests; route tests incl. qty below minimum | Below-minimum quantity rejected with a clear message; total correct |
| **6** ★ | C3 Checkout | login-gated checkout, order form, guest-group rows (small JS), validation (future date, guests ≥ 1, group counts ≤ guests), one-transaction save, confirmation | anonymous → login → back; valid order saved with lines + groups; invalid input re-rendered; cart cleared | Order stored as `submitted` / `not_paid` with guest-group allergies |
| **7** ★ | C4 My orders + A3 Admin orders | customer list/detail; admin list with filters, detail, status + payment updates | own orders only; filters; illegal transition rejected | Admin status change visible to customer |
| **8** | A4 + C5 Questions | ask on own order; admin list + answer; dashboard counts | no questions on others' orders; empty text rejected; answer visible | Question → answer round trip works |
| **9** ★ | A2 Images | upload with type/size checks; `ImageService` with `PlaceholderImageService` (offline default) and `ClaudeSvgImageService` (creates/modifies an SVG from an instruction; enabled only if `ANTHROPIC_API_KEY` is set in the environment); preview → save/discard | upload valid/invalid; generate → discard leaves item unchanged; save updates item; AI service mocked in tests | Admin can upload or generate/modify an image, preview it, and only saved images appear in C1; **no API key in the repository** |
| **10** | Hardening + submission | error pages, escaping review, accessibility pass, README final (install/seed/run/test), CLAUDE.md final, diagrams, screenshots, secret check, tag `oblig4` | full test run; manual walkthrough (below) on a freshly seeded DB | All A1–A4, C1–C5 demonstrated; report parts 1–4 complete; tag pushed |
| 11 | Optional extras | from the "going further" list, each with named stakeholder need and its own plan | per feature | Only if phases 0–10 are done |

**Manual walkthrough (phase 10):** reset DB → browse menu by event (C1) → add items, try below-minimum quantity (C2) → register and check out with two guest groups incl. a nut allergy (C3) → see `submitted / not paid` (C4) → ask a question (C5) → admin creates an item and adds a generated image after preview (A1, A2) → admin approves the order and sets `deposit paid` (A3) → admin answers (A4) → customer sees the updates.

## 9. Team workflow on GitHub (four students)

- **[OFFICIAL]** Every member commits to the GitHub repository.
- **[DECISION]** Each of the four students makes meaningful commits and pushes **from their own GitHub account** (own name/e-mail in `git config`, matching their GitHub account).

**Ownership** [ASSUMPTION] — each student owns a vertical slice through model, view and controller, so every student's history shows real code, templates and tests:

| Student | Primary ownership | Phases |
|---|---|---|
| S1 | Project setup, model layer, SQLite repositories, seed data, CLI, README | 0, 1 |
| S2 | Auth, admin food items, images | 2, 3, 9 |
| S3 | Customer menu, cart, checkout | 4, 5, 6 |
| S4 | Customer + admin orders, questions | 7, 8 |
| All | Hardening, diagrams, screenshots, report | 10 |

S1 merges `entities.py`, `enums.py` and `interfaces.py` first (day 1–2); others build against these interfaces, using in-memory fakes in tests until the SQLite repositories are merged.

**Workflow rules** [ASSUMPTION]:
1. `main` stays deployable; no direct pushes — pull request + review by another student. (Branch protection on a private repo may need a paid plan; if unavailable, follow the rule by agreement.)
2. One GitHub issue per task; one branch per issue: `feature/<phase>-<short-name>`.
3. Small, focused commits with tests, imperative messages (`Add min-order check to Cart`).
4. Every plan file is committed by the student who owns the feature, before the implementation PR.
5. Pair work: `Co-authored-by:` trailer. AI-assisted commits: Claude co-author trailer.
6. Review checklist: layer rules respected, tests added, no secrets, CLAUDE.md still true.
7. Before submission, check GitHub *Insights → Contributors*: all four members visible.

## 10. Working with Claude Code, report and submission

### Claude Code [OFFICIAL]
- **`CLAUDE.md`** — project briefing: what the system is, the MVC layout, how to run and test, team rules. **Short and true**; updated whenever these change.
- **Plan mode** — plan every larger feature before building; commit the agreed plan to `docs/plans/`.

### Optional AI documentation [ASSUMPTION — not required by the assignment]
- Claude co-author trailer on AI-assisted commits.
- Short "Claude Code use" note in each plan file (what the agent proposed, what we changed).
- These provide material for report part 4 but are not graded items.

### Report — one PDF on Mitt UiB [OFFICIAL]
| Part | Content | Plan task (phase 10) |
|---|---|---|
| 1 Front page | Group members; GitHub link; **tag of the version to assess (`oblig4`)**; Neo4j included: **no** | Create and push tag `oblig4`; give course staff access to the private repo |
| 2 Features | Name + one-line description of each feature, with screenshots of at least: **customer** menu, cart, order form, my orders, questions; **admin** food item, image, order list, order page | Screenshot checklist in `docs/report/`; one-liners from §2 |
| 3 Software design | Design concepts used, with diagrams and 1–2 sentences on how each was used | Drafts exist: user stories (`docs/backlog/user-stories.md`), use-case, domain class, sequence (C3 checkout), **order state machine**, MVC architecture (`docs/design/`, usage notes in `docs/design/README.md`). Update diagrams if the code deviates. |
| 4 Did design help? | Short paragraph on whether software-design knowledge helped build the product and steer Claude Code | Written by the group at the end |

**To be approved [OFFICIAL]:** executable application, the listed functionality, code follows MVC, report contains parts 1–4.
The PDF report and the assignment PDF are kept **outside the repository** [DECISION].

## 11. Security and secrets

- **[OFFICIAL]** The repository must not contain a Claude API key.
- `.env` (git-ignored) holds `ANTHROPIC_API_KEY` and `SECRET_KEY`; `.env.example` lists the names only.
- Before each PR and before tagging: `git grep -nE "sk-ant-|ANTHROPIC_API_KEY\s*=\s*\S"` must return nothing outside `.env.example` [ASSUMPTION].
- Without a key, A2 falls back to the offline placeholder service, so the app always runs.

## 12. Open issues and ambiguities

| ID | Issue | Current handling |
|---|---|---|
| **OPEN-1** | Repository access: the PDF says "public, private and shared with the course staff" — contradictory. **Checked 28 Oct 2026: `Marensundt/Oblig4-INFO212` is private** (not visible via the public GitHub API). | Most likely meaning: public, *or* private and shared with course staff. Do **not** change visibility; before submission, invite the course staff as collaborators or confirm the rule with the TA. |
| **OPEN-2** | "Only customer login pages are fine" — ambiguous: simple login is sufficient, or no admin login needed? | Plan keeps an admin role with login (protects A1–A4); confirm with TA. |
| ~~OPEN-3~~ **resolved 2026-10-28** | Lab 7 backlog and models were not completed by the group. | Replaced by `docs/backlog/` and `docs/design/` (plan 02), using Lab 7 as guidance and Oblig 4 as priority. §2 and §4 now link to them. |
| **OPEN-4** | A2 "AI agent or image service": Claude cannot output bitmap images. | Proposed: Claude writes/modifies an **SVG** from the instruction [ASSUMPTION]; placeholder service as offline default. Confirm before phase 9. |
| **OPEN-5** | Deadline: "see Mitt UiB". | Team to fill in and back-plan phases. |
| **OPEN-6** | Seed minimum orders, categories and allergens are not in the data pack. | Marked [ASSUMPTION] in §7; confirm against Lab 7 backlog. |
| **OPEN-7** | Case says 3 developers; our group has 4. | Plan uses 4 (assignment allows 2–4). |
| **OPEN-8** | Should `EkteMat_project_inbox/` (data pack) be committed? | Not yet decided; currently untracked. |
| ~~OPEN-9~~ **resolved 2026-10-28** | Exact order-status transitions and payment-status rules. | Decided in `docs/plans/03` §2 and implemented in `app/models/enums.py`: official states and main path [OFFICIAL]; rejected only from submitted, cancelled from any non-final state, final states fixed, payment status set freely [ASSUMPTION]. |
| ~~OPEN-10~~ **resolved 2026-10-28** | Which data-validation rules to enforce. | Decided in `docs/plans/03` §2: official rules (A3 values, C2 minimum order) and essential integrity rules enforced in phase 1; form rules later (phases 3, 6); DV-02 and NFR-11/12 optional, not planned. Decision column in `docs/backlog/data-validation-rules.md`. |

## 13. Checklist for this plan

Every A1–A4 and C1–C5 row in §2 has a phase and acceptance criteria in §8; folder structure shows models/views/controllers; only `repositories/sqlite/` touches storage; report parts 1–4 have tasks; no step modifies `EkteMat_project_inbox/` or commits the assignment PDF or any API key.
