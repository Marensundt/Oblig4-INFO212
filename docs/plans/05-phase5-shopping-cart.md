# 05 — Plan: phase 5, shopping cart (C2)

Status: **agreed 2026-10-29** — implements the phase 5 row of `docs/plans/01-implementation-plan.md` (§2, §5, §8). One new assumption: a maximum of 9 999 portions per line.
Labels: **[OFFICIAL]** Oblig 4 · **[ASSUMPTION]** our proposal (from `docs/backlog/user-stories.md`).

## Requirement
**[OFFICIAL] C2 Shopping cart:** "Add, change and remove items, with an estimated total cost. Quantities below an item's minimum order are not accepted."
Stories: **US-08** add items, **US-09** change, remove and see the estimated total.

## Scope
| Route | Purpose | Story |
|---|---|---|
| `POST /cart/add` | "Add to cart" form on every menu card (portions, starts at the minimum order) | US-08 |
| `GET /cart` | Lines with price × portions, estimated total; drops items that are no longer published, with a message | US-09 AC1, AC4 |
| `POST /cart/update` | Change the portions of one line | US-09 AC2 |
| `POST /cart/remove/<item_id>` | Remove one line | US-09 AC3 |

All routes are public (visitors build a cart before logging in); all state changes are POST with CSRF token. The header shows "Cart (n)".
Not in scope: checkout and price snapshot (C3, phase 6).

## Rules
| Rule | Label |
|---|---|
| Quantity below the item's minimum order is rejected with a message naming the minimum; a rejected change keeps the old quantity | OFFICIAL (C2); message wording ASSUMPTION |
| Adding an item that is already in the cart adds the quantities; the sum must meet the minimum | ASSUMPTION (US-08 AC3) |
| At most 9 999 portions per line (stops typing mistakes) | ASSUMPTION (new) |
| Only published items can be added; unpublished or deleted items are removed when the cart is shown, with a message | ASSUMPTION (US-09 AC4) |
| Cart shows current prices; the total is called "estimated" because Ekte Mat confirms the price on approval | OFFICIAL "estimated"; reason ASSUMPTION |
| If an admin raises the minimum after an item was added, the line shows a warning (checkout in phase 6 must re-check) | ASSUMPTION |
| Cart is kept when the visitor logs in (session key `cart` in `account.KEPT_ON_LOGIN`) | ASSUMPTION (US-11 AC2) |

## Design
- Model layer: `app/models/cart.py` — `Cart` ({food_item_id: quantity}, no Flask/DB imports) with `add`, `set_quantity`, `remove`, `refresh(items)`; `CartLine` (item, quantity, `line_total_nok`, `below_minimum`); `estimated_total_nok(lines)`. New errors in `errors.py`: `InvalidQuantity`, `BelowMinimumOrder`, `ItemNotAvailable`.
- Controller: routes in `app/controllers/shop.py`; the cart lives in the Flask session as `{"<id>": qty}`; food items are loaded through `current_app.repos.food_items` only. Form `CartQuantityForm` (item id + portions).
- Views: `shop/cart.html`; add-to-cart form in `_partials/food_card.html`; cart link in `base.html`.

## Tests
`tests/unit/test_cart.py` (minimum, sum on re-add, maximum, unpublished, set/remove, totals, refresh, session data) and `tests/controllers/test_shop_cart.py` (each US-08/US-09 criterion through the routes, invalid input, price change, raised minimum, cart kept on login, CSRF token on the forms).

## Acceptance (01-plan §8)
Below-minimum quantity rejected with a clear message; total correct; all tests pass.
