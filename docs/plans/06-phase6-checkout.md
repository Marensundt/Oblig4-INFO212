# 06 — Plan: phase 6 ★, checkout and order placement (C3)

Status: **agreed 2026-10-29** — implements the phase 6 row of `docs/plans/01-implementation-plan.md` (§2, §5, §8) and follows `docs/design/sequence-checkout.puml`.
Labels: **[OFFICIAL]** Oblig 4 · **[ASSUMPTION]** our proposal (from `docs/backlog/user-stories.md`, `docs/backlog/data-validation-rules.md`).

## Requirement
**[OFFICIAL] C3 Order:** "Log in (or register) and submit the order: event date, number of guests, delivery address, and allergy and dietary notes per guest group. No payment solution is needed."
Stories: **US-11 AC2** (login and back to checkout with the cart), **US-12** submit an order, **US-13** allergies and diets per guest group. Login and registration themselves were built in phase 2.

## Scope
| Route | Purpose | Story |
|---|---|---|
| `GET/POST /account/checkout` | Order form with cart summary and estimated total; `@login_required` with return to checkout; empty cart → menu; unavailable items or raised minimum → cart | US-11 AC2, US-12, US-13 |
| `GET /account/checkout/confirmation/<order_id>` | Order number, status, payment status, lines, guest groups; only the customer's own order (else 404) | US-12 AC1, US-13 AC1 |

The cart page gets a "Continue to order" button. Admin accounts cannot place orders (ASSUMPTION: orders belong to customers, DV-10).
Not in scope: my orders list (C4, phase 7/8), questions (C5), e-mail confirmation.

## Rules (checked in `app/models/ordering.py`)
| Rule | Label |
|---|---|
| Order stored with status *submitted* and payment status *not paid*; no payment step | OFFICIAL (A3 values, C3) |
| Every cart line still published and ≥ its minimum order | OFFICIAL (C2) |
| Event date after today (DV-04) | ASSUMPTION |
| Number of guests ≥ 1 (DV-01) | ASSUMPTION |
| Delivery address required | ASSUMPTION |
| ≥ 1 guest group (DV-11), at most 20; each with a name and ≥ 1 guest | ASSUMPTION |
| Sum of group counts ≤ number of guests (groups may describe only guests with special needs) | ASSUMPTION (US-13 AC2) |
| No field for guests' names | ASSUMPTION from GDPR note (US-13 AC3) |
| Item name and price copied onto order lines (price snapshot) | ASSUMPTION (US-02 AC2) |
| Order, lines and guest groups saved in one transaction; cart emptied only after saving | ASSUMPTION |

## Design
- Model: `app/models/ordering.py` — `check_cart(repos, cart)` and `place_order(repos, customer, cart, …, today=None)` raising `InvalidOrder(errors)` (new in `errors.py`) with a message per field. The repository `OrderRepository.add()` from phase 1 is unchanged.
- Controller: `account.checkout` and `account.confirmation`; the session cart helpers move to `app/controllers/cart_session.py` so `shop` and `account` share them.
- Form: `CheckoutForm` with `FieldList(FormField(GuestGroupForm))`. `app/static/js/checkout.js` adds and removes guest-group rows; without JavaScript the "Add another guest group" button adds a row on the server.
- Views: `account/checkout.html`, `account/confirmation.html`.
- Design model: the sequence diagram note now names `place_order()` as the `validate()` step.

## Tests
`tests/unit/test_ordering.py` (each rule, price snapshot, all errors at once) and `tests/controllers/test_account_checkout.py` (anonymous → login → back with cart; register → back; form fields without name/payment fields; empty cart; valid order saved with lines and groups, cart emptied, confirmation; past date, guests 0, group sum too large, missing fields re-rendered with input kept; add-group without JS; unpublished item; admin refused; other customer's confirmation 404; CSRF).

## Acceptance (01-plan §8)
Order stored as *submitted* / *not paid* with guest-group allergies; invalid input re-rendered; cart cleared; all tests pass.
