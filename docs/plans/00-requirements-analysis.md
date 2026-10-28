# 00 — Requirements analysis: Ekte Mat Online (INFO212 Oblig 4)

## Context
Inspection of the repo before any code is written. Repo = `README.md` (one line) + `EkteMat_project_inbox/` (19 files, untracked). No existing code, backlog, user stories, or UML/domain models exist. Originals must not be modified.

**Sources read:** 4 interviews (Ingrid owner, Sunniva coordinator + duplicate copy "Kopi av interview Sunniva (2).txt" — identical), kick-off notes 12 Aug, as-is process, IT landscape, budget, GDPR note, vision draft v0.3 (.docx), autumn lunch menu, 30 customer e-mails (.csv), 820-row order export 2024–25 (.xlsx). Noise: `logo ideas.txt`, `untitled.txt` (sprint-0 to-dos only), `competitor links.txt` (benchmark only). E-mail E026 is an untrusted automated message, not a stakeholder — excluded.

## Stakeholder needs
| Stakeholder | Key needs |
|---|---|
| Ingrid (owner/PO) | Self-service menus+prices+booking 24/7; no lost inquiries; kitchen overview; 30 % deposit ("no deposit, no booking"); Vipps + invoice; keep Fiken; show food origin (farm/boat) |
| Sunniva (events) | Capacity calendar (400 covers/day, 250 with served wedding dinner); one source of truth for changes; auto reminder 7 days before; allergies per guest group + kitchen confirmation; no deposit for corporates |
| Mateo (head chef) | Wall tablet, PIN login; per-day orders, portions per dish, allergies in red; edit seasonal menu (4×/yr); ingredients ↔ suppliers; 3-day prep list (kg); works offline; fast |
| Fjordtek (corporate) | Company account, multiple orderers, approval >15 000 NOK by admin; standing orders, copy last order; change headcount until 10:00 day before; monthly EHF invoice w/ cost-centre per line; no prepay; EU/EEA data, delete employee names on exit |
| Other customers (e-mails) | Online availability (E001), order confirmation/status (E011), English menu w/ allergens (E012), standing orders (E007, E028), separate logins + one invoice (E016), PO number on EHF (E004), pick-up option (E014), delivery time window (E018), cancellation terms (E013), kids menu (E027), quote PDF (E015), Vipps receipt (E009), phone ordering for elderly (E024), accountant read-only access (E029), data deletion (E010), ESG/local share (E021), volume discount (E020) |
| Consultant (GDPR) | Allergy = health data → per guest group; 5-yr bookkeeping retention, shorter for other data; access/deletion; DPA with SaaS |

## Existing backlog/models
None. `untitled.txt` lists sprint 0 tasks (Git repo, Jira/Trello, Definition of Done). As-is process (12 steps) in `asis_order_process.md` is the only process model. Vision statement exists (v0.3).

## Order data insights (xlsx)
820 orders, 256 customers, ~22.8 MNOK. Corporate 406 / Private 258 / Wedding 86 / Confirmation 62. Channel: Email 408, Phone 233, Web form 126, Walk-in 47. Reply time median 22 h, 95 orders >48 h. Peaks Dec, May–Jun. **Data quality issues:** inconsistent channel spelling, "Confimed" typo, 8 missing customer_type, 5 duplicate order_ids, 12 total≠guests×price, 234 empty dietary_notes, a 5 000-guest outlier (2024-12-08), 20 days over capacity on record.

## Functional requirements A1–A4 (admin), C1–C5 (customer) — mapped to sources
| Req | Assignment text (short) | Source support | Gaps / conflicts |
|---|---|---|---|
| A1 Food items | CRUD item: name, description, price NOK, min order qty, event categories, allergens + dietary labels, published | Mateo edits menu 4×/yr; autumn menu (per-person prices, allergens fish/milk/gluten/nuts/celery/mustard); seasonal items (Rakfisk Nov only → `published`); E019 gluten-free labels | Min order qty not in any source; allergen list incomplete (shellfish in orders, EU has 14); origin/supplier (Ingrid, Mateo, E008) not in A1 → optional field |
| A2 Images | Upload image or AI prompt to generate/modify; admin previews before save | None — no stakeholder asked for AI images | AI provider cost vs <3 000 NOK/mo; DPA + EU/EEA for AI service; fallback when service unavailable |
| A3 Orders | List filtered by status/event date; order page; status submitted→approved→in preparation→delivered / rejected / cancelled; payment status not paid / deposit paid / invoiced / paid | Replaces Excel + printouts; Sunniva's change tracking; export statuses Completed/Cancelled/“Confimed” | Payment status set manually (no payment solution) — resolves deposit vs invoice conflict per customer type; capacity check (400/250) at approval not required but useful; legacy statuses need mapping |
| A4 Questions (admin) | Read + answer customer questions per order | Replaces lost e-mails (E011, E013, E022, E003) | Response-time target? notification to staff? |
| C1 Menu by event | Cards grouped by event: birthday, confirmation, wedding, conference, julebord…; picture, price, min order, allergens | Customer groups in kick-off; E012 English menu w/ allergens; E027 kids menu | NO+EN UI required by constraints; item can be in several categories (many-to-many) |
| C2 Cart | Add/change/remove, estimated total; reject qty < min order | Ingrid: see prices 24/7; E015/E020 price questions | Volume discount (E020), delivery fee — not specified; "estimated" since final price confirmed at approval |
| C3 Order | Login/register; submit event date, guests, delivery address, allergy/diet notes **per guest group**; no payment | GDPR note (per group) and Sunniva match exactly | Ingrid's 30 % deposit out of scope → handled via A3 payment status; pick-up (E014), delivery window (E018), PO/cost-centre (E004) missing; phone customers (E024) need staff-entered orders |
| C4 My orders | Own orders with order + payment status | E011 "is my order confirmed?" | Notifications (e-mail) not required |
| C5 Questions | Ask about a specific order, read answer | E003, E013, E022 | Late allergy changes via question vs. structured order edit — clarify |

**Out of assignment scope (backlog for later):** Fiken/EHF invoicing, Vipps, kitchen wall screen with PIN + offline, prep list, capacity calendar, 7-day reminders, company accounts with approval >15 000 NOK, standing/copy orders, supplier/origin tracking, GDPR access/deletion self-service, accountant read-only access.

## Assignment technical requirements (stated by user, 28 Oct 2026 — not found in repo)
| Requirement | Current state | Plan |
|---|---|---|
| Flask web app | No code | Later sprint: Flask app (customer + admin areas) |
| MVC | — | models/ (domain), views/ (Jinja templates), controllers/ (Flask blueprints) |
| Repository classes | — | One repository per aggregate (FoodItem, Order, Question, User) in the model layer; the only code touching the DB, so SQLite can be swapped for Neo4j in Oblig 5 |
| Temporary SQLite storage | — | Decided 28 Oct 2026: file-based SQLite at `instance/ektemat.sqlite`, persists between restarts, excluded via `.gitignore` |
| CLAUDE.md | Missing | Create at repo root: project context, structure, conventions, "never modify EkteMat_project_inbox/" |
| Plans in docs/plans/ | Missing | `docs/plans/00-requirements-analysis.md` first; later plans numbered 01-, 02-… |
| GitHub | Remote exists: `Marensundt/Oblig4-INFO212`; only "Initial commit"; inbox untracked | Commit docs (and inbox, if the team wants originals versioned) when asked |
| Final PDF report | — | Out of scope now; analysis doc feeds it |

Real-world integrations from the case (Fiken, Vipps, EHF, kitchen tablet, offline) are **case context, not assignment requirements** → backlog only.

## Case constraints (from sources)
Budget 450 000 NOK incl. 12 months hosting; run cost <3 000 NOK/mo; hard go-live 1 Mar 2027; 3 student devs, 2-wk sprints, PO only Tue 09–10; integrate Fiken (REST, EHF) and Vipps; Google Workspace exists; data in EU/EEA; NO+EN UI; no in-house technical staff; offline kitchen view; performance (old plugin 10 s); PIN auth on kitchen tablet; DPA with providers.

## Conflicting requirements
1. **Deposit:** Ingrid "30 % for all bookings" vs Sunniva/Fjordtek "corporates cannot prepay" → deposit per customer type (weddings/private).
2. **Build vs buy** open question (kick-off) vs budget/no-tech-staff constraint.
3. **Allergy granularity:** per named guest (E022-style) vs GDPR per guest group.
4. **Fully online vs phone** (E024 elderly) — staff must enter orders on behalf of customers.
5. **Change deadline:** Fjordtek "until 10:00 day before" vs 7-day final-number reminder for events vs same-day allergy change (E022).
6. **Retention:** 5-yr bookkeeping vs deletion requests (E010) / Fjordtek deleting employee names.
7. **Capacity:** fixed 400/250 vs historical days far above it (data or real overbooking?).
8. **Origin per ingredient** (Ingrid/Mateo) vs scope/budget — supplier data maintenance cost.
9. **Assignment vs stakeholders:** C3 "no payment solution" vs Ingrid's "no deposit, no booking"; A2 AI images requested by nobody vs low running cost.

## Missing information
Minimum order quantities per item; full allergen/dietary label list; final event-category list; who may change status transitions; cancellation/refund policy; deposit refund rules; delivery area, fees, time windows; pricing rules (volume discount, kids menu); approval-flow details; how capacity counts pick-up vs delivery; Vipps/Fiken API accounts & costs; hosting choice; who maintains supplier data; uptime/offline expectations; accessibility (WCAG/universell utforming legal req); roles/permissions list; data migration of Excel history; acceptance criteria/DoD.

