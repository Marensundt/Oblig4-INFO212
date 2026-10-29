# 07 — Plan: phase 7 ★, my orders (C4) and admin orders (A3)

Status: **agreed 2026-10-29** — implements the phase 7 row of `docs/plans/01-implementation-plan.md` (§2, §5, §8) and the order state machine `docs/design/state-order.puml`.
Labels: **[OFFICIAL]** Oblig 4 · **[ASSUMPTION]** our proposal (from `docs/backlog/user-stories.md`).

## Requirements
**[OFFICIAL] A3 Orders:** "A list of all customer orders that can be filtered by status and event date, and a page per order to manage it: order status (submitted → approved → in preparation → delivered, or rejected/cancelled) and payment status (e.g. not paid, deposit paid, invoiced, paid)."
**[OFFICIAL] C4 My orders:** "The customer's own orders with their current status (submitted, approved, delivered, …) and payment status."
Stories: **US-14** list and filter, **US-15** order page and status, **US-16** payment status, **US-17** my orders.

## Scope
| Route | Purpose | Story |
|---|---|---|
| `GET /account/orders` | Customer's own orders: number, event date, guests, total, status, payment status | US-17 AC1, AC3 |
| `GET /account/orders/<id>` | Order page (lines, total, guest groups); other customers' orders → 404 | US-17 AC2 |
| `GET /admin/orders?status=&date_from=&date_to=` | All orders sorted by event date, with customer; filter by status and event-date range | US-14 |
| `GET /admin/orders/<id>` | Order page with customer contact, lines, total, guest groups with allergies highlighted, status and payment forms | US-15 AC1 |
| `POST /admin/orders/<id>/status` | Change order status; only allowed transitions offered and accepted | US-15 AC2–AC4 |
| `POST /admin/orders/<id>/payment` | Set payment status | US-16 AC2 |

Customer routes `@login_required`; admin routes `@admin_required`; POSTs carry a CSRF token. The C3 confirmation page reuses the same order-details partial. Admin start page links to orders and shows how many orders wait for approval. Header gets "My orders" for customers.
Not in scope: questions on orders (C5/A4, phase 8), e-mail notifications.

## Rules
| Rule | Label |
|---|---|
| Status values and main path submitted → approved → in preparation → delivered, or rejected/cancelled | OFFICIAL |
| Rejected only from submitted; cancelled from any non-final state; delivered/rejected/cancelled are final (`OrderStatus.can_change_to`, phase 1) | ASSUMPTION (OPEN-9) |
| Payment status values; set freely by admin | OFFICIAL values; free setting ASSUMPTION |
| Customers only see their own orders; another customer's order gives 404 | OFFICIAL "own orders"; 404 ASSUMPTION |
| Date filter: event date inclusive from/to; "to" before "from" is an error | ASSUMPTION |
| Customers cannot change status or payment in this phase (cancel by customer not required) | ASSUMPTION |

## Design
- Model: no new rules. `OrderStatus.next_statuses` (new, in `enums.py`) lists allowed transitions for the status form; `OrderRepository.update_status` already refuses illegal transitions with `InvalidStatusTransition`. Customer names on the admin list come from `UserRepository.list_customers()`.
- Controllers: `account.orders`, `account.order_detail`; `admin.order_list`, `admin.order_detail`, `admin.order_status`, `admin.order_payment`.
- Forms: `OrderFilterForm` (GET, no CSRF), `OrderStatusForm`, `PaymentStatusForm`.
- Views: `account/orders.html`, `account/order_detail.html`, `admin/orders/list.html`, `admin/orders/detail.html`, shared `_partials/order_details.html`.

## Tests
`tests/controllers/test_account_orders.py`: own orders only, 404 for others, empty state, admin change visible after reload (US-17 AC3).
`tests/controllers/test_admin_orders.py`: list columns and sort, status filter, date range, invalid filter, detail with highlighted allergies, every allowed transition, final states refused, illegal transition refused, payment status set and shown, customer 403 on routes with ids. `tests/unit/test_enums.py`: `next_statuses`.

## Acceptance (01-plan §8)
Own orders only; filters work; illegal transition rejected; admin status change visible to customer; all tests pass.
