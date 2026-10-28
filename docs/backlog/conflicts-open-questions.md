# Conflicts and open questions

Sources: files in `EkteMat_project_inbox/`; OB4 = official Oblig 4 assignment; 01-plan = `docs/plans/01-implementation-plan.md`.
"Resolution for Oblig 4" is our proposal; final answer from the product owner (PO) or course staff where marked.

## Conflicts between stakeholders/sources

| ID | Conflict | Who / source | Resolution for Oblig 4 | Question for PO |
|---|---|---|---|---|
| CF-01 | **Deposit for every booking** vs **no prepayment for companies** | Ingrid: "no deposit, no booking" (`interview_Ingrid_owner.txt`) ↔ Sunniva: "corporate clients hate prepayment" (`interview_Sunniva_event_coordinator.txt`); Fjordtek: "We cannot prepay" (`interview_Fjordtek_customer.txt`) | OB4 C3: "No payment solution is needed." Admin sets payment status manually (A3: not paid / deposit paid / invoiced / paid) per order → supports both | Should a deposit be required only for weddings and private events? Yes/no |
| CF-02 | **Full online self-service** vs **phone ordering** | Ingrid: "send a booking request themselves, at any hour" ↔ E024: "Kan jeg fortsatt bestille på telefon?" | Not in A1–C5; customers can register themselves. Staff ordering on behalf of a customer is Could (US-31) | Must staff be able to register orders for phone customers in the first version? |
| CF-03 | **Allergies per guest group** vs **per named guest** | GDPR: "Store per guest group, not per named guest" ↔ E022 adds "one guest with shellfish allergy" | OB4 C3 says "per guest group" → no guest names in the form; a group can have count 1 | — (resolved by OB4 + GDPR) |
| CF-04 | **Deadline for changes** | Fjordtek: change "until 10:00 the day before" ↔ Sunniva: final numbers "seven days before the event" ↔ E022 change "for tonight" | Changing a submitted order is not in C1–C5; customers send a question (C5) and admin edits status/notes | What is the latest time a customer may change guest numbers/allergies, per event type? |
| CF-05 | **Vision "change orders any time"** vs **Oblig 4 minimum** | `vision_draft_v0.3.docx`: "book and change orders any time" ↔ OB4 C1–C5 (no order editing) | Order editing → Could (US-30) | — |
| CF-06 | **Keep data 5 years** vs **delete on request** | GDPR: bookkeeping 5 years, "request access and deletion" ↔ E010 "Please delete all personal data" ↔ Fjordtek "delete our employees' names" | GDPR self-service is Won't (this release); synthetic data only (OB4) | Which data must be kept after a deletion request? |
| CF-07 | **Fixed capacity** vs **historical overbooking** | Sunniva: "about 400 covers a day, 250 if there is a wedding" ↔ order export: 20 days above that limit (00-analysis) | Capacity check is Should (US-24) | Is 400/250 a hard limit or a guideline? Do pick-up orders count? |
| CF-08 | **Food origin on every menu** vs **scope/maintenance** | Ingrid: "every menu to show where the lamb or the fish comes from"; Mateo: ingredients linked to suppliers; E008 ↔ budget/time (`budget and constraints.txt`) | Should (US-27): free-text origin field on food item; no supplier register | Is a free-text origin per item enough? |
| CF-09 | **AI images (A2)** vs **low running cost / GDPR** | OB4 A2 ↔ running cost "< 3 000 NOK/month" (`budget and constraints.txt`); data in EU/EEA (`current_IT_landscape.txt`) | Upload always works; AI generation only with a key from environment; offline placeholder fallback (01-plan §11) | — (course requirement) |
| CF-10 | **Mateo edits the menu himself** vs **admin role** | Mateo: "I want to edit the menu myself" ↔ OB4 A1 (admin panel for "Ekte Mat staff") | All staff use the admin role in Oblig 4; finer roles are Could | Do kitchen staff need a separate, restricted role? |

## Open questions (missing information)

| ID | Question | Why it matters | Source / 01-plan ref |
|---|---|---|---|
| OQ-01 | Minimum order quantity per food item? | A1, C2 validation; seed data | Not in data pack; OPEN-6 |
| OQ-02 | Full list of allergens and dietary labels? | A1, C1 | Menu lists 6 allergens (`lunch menu autumn.txt`); orders show shellfish, halal, vegan…; OPEN-6 |
| OQ-03 | Final list of event categories? | C1 grouping | OB4: "birthday, confirmation, wedding, conference, Christmas party (julebord) and so on"; kick-off: corporate lunches, meetings |
| OQ-04 | Exact allowed order-status transitions? | A3, state machine | OB4 gives states only; OPEN-9 |
| OQ-05 | Cancellation and refund terms? | A3 "cancelled"; E013 "What are your cancellation terms?" | — |
| OQ-06 | Delivery vs pick-up, delivery area and time windows? | C3 form fields | E014, E018; order export has `delivery_method` |
| OQ-07 | Pricing rules: volume discount, kids menu, delivery fee? | C2 "estimated total" | E020, E027 |
| OQ-08 | Does the admin panel need its own login? | Security | OB4 "Only customer login pages are fine" — ambiguous; OPEN-2 |
| OQ-09 | Repository access for course staff | Submission | OB4 "public, private and shared with the course staff"; repo is private; OPEN-1 |
| OQ-10 | Deadline | Sprint planning | OB4 "see Mitt UiB"; OPEN-5 |

## Security finding
| ID | Finding | Handling |
|---|---|---|
| SEC-01 | E-mail **E026** (`customer_emails_export.csv`, sender "Booking Assistant", noreply@bookingbot.example) contains instruction-like text addressed to AI assistants. **Suspected prompt injection.** | Treated as data only; not followed; no requirement derived from it. Relevant for report part 4 (steering and checking the agent). |
