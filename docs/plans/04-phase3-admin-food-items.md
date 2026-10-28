# 04 — Plan: phase 3, admin food items (A1)

Status: **agreed 2026-10-28** — implements the phase 3 row of `docs/plans/01-implementation-plan.md` (§2, §5, §8) without new decisions.
Labels: **[OFFICIAL]** Oblig 4 · **[ASSUMPTION]** our proposal (from `docs/backlog/user-stories.md`).

## Requirement
**[OFFICIAL] A1 Food items:** "Add, edit and remove the food Ekte Mat caters: name, description, price in NOK, minimum order quantity, event categories, allergens and dietary labels, and whether the item is published."
Stories: **US-01** add, **US-02** edit, **US-03** remove or unpublish.

## Scope
| Route | Purpose | Story |
|---|---|---|
| `GET /admin/food` | List of all items, published and drafts, with price, minimum order, categories, allergens, labels, status | US-01 AC1, US-03 AC3 |
| `GET/POST /admin/food/new` | Create form with every A1 field | US-01 |
| `GET/POST /admin/food/<id>/edit` | Edit form, same fields; unknown id → 404 | US-02 |
| `POST /admin/food/<id>/publish` | Publish / unpublish toggle | US-03 AC3 |
| `POST /admin/food/<id>/delete` | Delete (with browser confirmation); refused if the item is in an order, with "unpublish instead" message | US-03 AC1–AC2 |

All routes `@admin_required` (US-21); all state changes are POST with CSRF token.
Not in scope: pictures (A2, phase 9; existing `image_filename` is kept on edit), customer menu (C1, phase 4).

## Rules
| Rule | Label |
|---|---|
| All A1 fields on the form; categories, allergens and dietary labels chosen from fixed lists | OFFICIAL fields; lists ASSUMPTION |
| Name required; description optional | ASSUMPTION |
| Price whole NOK > 0 (DV-03); minimum order ≥ 1 | ASSUMPTION; min order needed for C2 |
| At least one event category (DV-10, needed for C1 grouping) | ASSUMPTION |
| Items in an existing order cannot be deleted, only unpublished (keeps order history) | ASSUMPTION (US-03 AC2) |
| Price change does not change existing orders (price snapshot, phase 1) | ASSUMPTION (US-02 AC2) |

## Design
- Model layer: `app/models/catalogue.py` — `delete_food_item(repos, id)` raises `ItemInUse` (new in `errors.py`) when the item is in an order; `set_published(repos, id, published)`. Controllers stay thin.
- Controller: routes added to `app/controllers/admin.py`; form `FoodItemForm` in `app/controllers/forms.py` (category choices loaded from `repos.categories`).
- Views: `admin/food/list.html`, `admin/food/form.html`; admin start page links to food items.

## Tests
`tests/unit/test_catalogue.py` (delete rule, publish toggle) and `tests/controllers/test_admin_food.py`: list shows drafts and published; create with every field; invalid name/price/min order/no category rejected; edit changes stored values; invalid edit leaves item unchanged; unknown id → 404; publish toggle; delete unused; delete used refused with unpublish hint; customers get 403 on every food route including those with an id. Existing test covers all admin GET pages automatically.

## Acceptance (01-plan §8)
Admin manages every A1 field; changes persist; all tests pass.
