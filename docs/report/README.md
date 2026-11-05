# Report material (OB4 §5; updated for Oblig 5)

Material for the one PDF report handed in on Mitt UiB.

> **Oblig 5 (2026-11-04):** the application now stores its data in **Neo4j** (default; SQLite still works with `STORAGE=sqlite`). The Oblig 5 report requirements were not available when this was written; the parts below follow the Oblig 4 structure (OB4 §5) and must be checked against the Oblig 5 assignment text. The PDF itself is **not** committed (team rule).
Parts follow OB4 §5; "To be approved" needs an executable app with the listed functionality, MVC code and parts 1–4.

## Part 1 — Front page

| Field | Value |
|---|---|
| Group members | *(fill in: full names and GitHub user names of all four members)* |
| GitHub repository | https://github.com/Marensundt/Oblig4-INFO212 |
| Version to assess | tag **`oblig5`** (created on `main` after the Neo4j PR is merged; `oblig4` stays on the Oblig 4 version) |
| Neo4j included | **Yes** — Neo4j 5 is the default storage (official `neo4j` Python driver, parameterised Cypher); SQLite kept as alternative |

Before submitting: the repository is private, so **invite the course staff as collaborators** (or make it public, see OPEN-1 in `docs/plans/01-implementation-plan.md`).

## Part 2 — Features (name, one line, screenshot)

Start Neo4j (README, “Start Neo4j”), then a fresh database (`flask --app run reset-db --yes`, then `flask --app run run`). Demo logins are in the README.
**Required screenshots** (OB4 §5.2) are marked ★.

| Req | Feature | One-line description | Screenshot: page and state | Login |
|---|---|---|---|---|
| C1 | ★ Menu by event | Published food items as cards grouped by kind of event, each with picture, price, minimum order and allergens. | `/menu` — scroll so one category heading and several cards are visible | none |
| C2 | ★ Shopping cart | Add, change and remove items with an estimated total; quantities below the minimum order are refused with a message. | `/cart` with 2 items; optionally the red message after trying a quantity below the minimum | none |
| C3 | ★ Order form | Log in or register, then send the order with event date, number of guests, delivery address and allergies/diets per guest group; no payment step. | `/account/checkout` with two guest groups filled in (e.g. "Children", 4 guests, Nuts) | customer |
| C3 | Order confirmation | Confirmation with order number, status *submitted* / *not paid*, lines and guest groups. | `/account/checkout/confirmation/<id>` right after sending | customer |
| C4 | ★ My orders | The customer's own orders with current order status and payment status. | `/account/orders` as `kari.kunde@example.com` (several statuses) | customer |
| C5 | ★ Questions | Ask a question about one of my orders and read Ekte Mat's answer under it. | `/account/orders/<id>`: in the seed, `ola.kunde@example.com` has an approved order with an answered question and `kari.kunde@example.com` has orders with questions waiting for an answer | customer |
| A1 | ★ Food item | Add, edit, publish/unpublish and remove food items with every A1 field. | `/admin/food` list and `/admin/food/<id>/edit` form | admin |
| A2 | ★ Image | Upload a picture or write an instruction (offline placeholder or Claude SVG), preview, then save or discard. | `/admin/food/<id>/image`, then the preview page after "Create and preview" | admin |
| A3 | ★ Order list | All orders filterable by status and event date, with customer and allergy flag. | `/admin/orders?status=submitted` or with a date range | admin |
| A3 | ★ Order page | Order details with allergies highlighted; change order status (allowed steps only) and payment status. | `/admin/orders/<id>` of an order with a nut allergy | admin |
| A4 | Questions (admin) | All customer questions, unanswered first, answered from the list or the order page. | `/admin/questions` | admin |
| — | Admin start page | Counts of orders waiting for approval and unanswered questions. | `/admin/` | admin |
| — | Access control | Admin pages only for the admin account; customers see "Access denied", visitors are sent to log in. | `/admin/` as a customer | customer |
| Oblig 5 | ★ Data in Neo4j | Every page above reads and writes Neo4j; the graph shows customers, orders, lines, guest groups, allergens and food items. | Neo4j Browser http://localhost:7474 after placing an order: `MATCH (u:User)-[:PLACED]->(o:Order)-[r]->(n) RETURN u, o, r, n LIMIT 50` | — |
| Oblig 5 | Allergy query | One Cypher pattern finds dishes in an order that contain an allergen a guest group has (graph model note). | Neo4j Browser: the pattern from `docs/design/img/graph-model.png` on an order with a nut allergy | — |

**Food pictures:** the 12 demo items have original SVG illustrations made for this project (no third-party material); sources and licence in `app/models/seed_pictures/README.md`. Mention this in part 2 next to the menu screenshot. Retake the screenshots after `reset-db`, so the menu shows the pictures.

## Part 3 — Software design (diagrams and how each was used)

Diagrams: `docs/design/img/*.png` (sources `docs/design/*.puml`). Use of each, to adapt in the group's own words:

| Concept | File | How it was used (draft) |
|---|---|---|
| User stories with acceptance criteria | `docs/backlog/user-stories.md` | Each phase's acceptance criteria became the definition of done and were turned into named tests (`docs/backlog/traceability.md`). |
| Use case diagram | `use-case.png` | Fixed the system boundary and actors and checked that every A1–A4 / C1–C5 requirement has a use case before building. |
| Domain class diagram | `domain-class.png` | Basis for `app/models/entities.py`, the repository interfaces, the SQLite schema and the Neo4j graph model; constraints became validation rules. |
| Sequence diagram (checkout) | `sequence-checkout.png` | Briefing for Claude Code in phase 6: where validation happens and that order, lines and guest groups are saved in one transaction (one Neo4j transaction since Oblig 5). |
| State machine (order status) | `state-order.png` | Source for `OrderStatus.can_change_to` / `next_statuses`; the admin form only offers allowed steps and tests cover every transition. |
| MVC architecture sketch | `mvc-architecture.png` | Folder structure and layer rules in `CLAUDE.md`; showed in Oblig 4 where Neo4j would replace SQLite, and in Oblig 5 that it did: only `repositories/neo4j/` and `factory.py` were added, no controller changed (NFR-02). |
| Neo4j graph model | `graph-model.png` | Oblig 5: mapping of the domain class diagram to node labels, relationships and constraints; specification for the Neo4j repositories (plan `docs/plans/11-oblig5-neo4j.md`). |

## Part 4 — Did design help?

To be written by the group (short paragraph). Evidence in the repository that can be referred to:
- every larger feature has a committed plan in `docs/plans/` written before the code (phases 1–10);
- acceptance criteria from the user stories were used directly as test names and comments;
- the sequence and state-machine diagrams were given to Claude Code as the specification for phases 6 and 7;
- tests written from the stories caught real mistakes during the build (e.g. phase 7 date filter ignored, phase 10 duplicate form ids);
- places where the agent's first proposal was changed are listed in each plan's "Assumptions to confirm" and in the PR descriptions;
- Oblig 5: because the repository interfaces from the design existed, Neo4j replaced SQLite without changing any controller, and the same 400+ tests run on both storages (only the shared test setup and a few SQLite-file tests were adapted).

## Before submitting — checklist

- [ ] All of A1–A4 and C1–C5 shown in a browser on a fresh database (`tests/test_walkthrough.py` automates the same steps)
- [ ] Screenshots for the ★ rows above taken and placed in the PDF
- [ ] Every group member has commits in the repository (GitHub → Insights → Contributors) — OB4 "every member commits"
- [ ] `pytest` green locally and in GitHub Actions on `main`
- [ ] No secrets: `git grep -nE "sk-ant-|(ANTHROPIC_API_KEY|NEO4J_PASSWORD)\s*=\s*\S"` and the same on `git log -p` return nothing outside `.env.example`
- [ ] Oblig 5: whole test suite green on Neo4j (`TEST_STORAGE=neo4j pytest` on a test server, and the `pytest-neo4j` job in GitHub Actions)
- [ ] Oblig 5: Neo4j screenshots (★ rows above) taken after `reset-db`
- [ ] Tag `oblig5` on the final `main` commit pushed (`git tag -a oblig5 -m "Oblig 5 submission" && git push origin oblig5`); `oblig4` stays as it is
- [ ] Course staff can open the repository
- [ ] PDF contains parts 1–4; assignment PDF and report PDF are **not** committed
