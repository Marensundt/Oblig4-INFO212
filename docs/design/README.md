# Design models — Ekte Mat Online

PlantUML sources (text, version-controlled). Rendered images go in `img/` and are used in report part 3 (OB4 §5).
All diagrams use `!pragma layout smetana`, so they render with Java + `plantuml.jar` only (no Graphviz, no external rendering service).

| Diagram | File | Scope / source | How it is used |
|---|---|---|---|
| Use case diagram | `use-case.puml` | All Must stories of A1–A4, C1–C5 (UC-01 – UC-17) | Agreeing the system boundary and actors; checking that every official requirement has a use case; splitting work between students |
| Domain class diagram | `domain-class.puml` | Entities from `user-stories.md`, constraints from `data-validation-rules.md` | Basis for the model layer (`app/models/entities.py`), repository interfaces, the SQLite schema and the Neo4j graph model (Oblig 5) |
| Sequence diagram | `sequence-checkout.puml` | C3 submit order (US-11, US-12, US-13) through the MVC layers | Briefing Claude Code for phase 6; shows validation points and the single repository transaction (Cypher on Neo4j since Oblig 5) |
| State machine | `state-order.puml` | Order status from OB4 A3 (US-15) | Source for `OrderStatus.can_change_to()` and its tests |
| MVC architecture sketch | `mvc-architecture.puml` | OB4 §3; 01-plan §3, §6 | Folder structure and layer rules in CLAUDE.md; shows the storage swap point (`factory.py`, Neo4j default, SQLite alternative) |
| Neo4j graph model | `graph-model.puml` | Oblig 5; `docs/plans/11-oblig5-neo4j.md`; mapped from `domain-class.puml` | Node labels, properties, relationship types and constraints implemented in `app/models/repositories/neo4j/` |

## Rendering (local only)
`tools/` is git-ignored; each team member downloads the jar once from the official release page (https://github.com/plantuml/plantuml/releases). Used 2026-10-28: **v1.2026.9**, Java 8 build `plantuml-java8-1.2026.9.jar` (needs Java 8+), saved as `tools/plantuml.jar`. With Java 11+ the standard `plantuml-1.2026.9.jar` also works.

```
java -jar tools/plantuml.jar -checkonly docs/design/*.puml   # syntax check
java -jar tools/plantuml.jar -tpng -o img docs/design/*.puml # render to docs/design/img/
```

Rendered PNGs in `img/` are committed so the report and GitHub can show them without PlantUML.

## Visual verification (2026-10-28)
All five diagrams pass `-checkonly` and were inspected after rendering: all elements, labels and multiplicities are visible; no overlapping text. Known cosmetic issue: in `use-case.png` the Admin → UC-04 and Admin → UC-14 lines take long routes around the boundary (layout engine limitation; semantics correct).

## Consistency check (2026-10-28)

| Check (Lab 7 Task 3) | Result |
|---|---|
| Every use case traces to ≥ 1 user story | ✔ UC-01 – UC-17 each list their OB4 ID and story |
| Every Must story with user interaction has a use case | ✔ US-01 – US-20. US-21 (admin access) and US-22 (seed/README) are quality/technical stories → covered by NFR-05 and NFR-09, not use cases |
| Every entity in the sequence diagram exists in the class diagram | ✔ Cart, Order, GuestGroup (plus User, FoodItem via repositories). View/controller/repository participants are MVC elements from `mvc-architecture.puml`, not domain classes |
| No implementation classes in the domain model | ✔ No controllers, repositories or DTOs. `Cart` is a domain concept (C2) marked `<<session>>` |
| Multiplicities plausible | ✔ Order has 1 delivery address, ≥ 1 order line, ≥ 1 guest group; FoodItem in ≥ 1 category (US-01 AC3); a question is answered by 0..1 admin |
| State machine matches OB4 A3 | ✔ All six official states; main path submitted → approved → in_preparation → delivered; rejected/cancelled. Extra transitions marked ASSUMPTION |
| Validation rules visible in models | ✔ DV-01, DV-03, DV-04, DV-05, DV-06, DV-07, DV-08, DV-11 as constraints in the class diagram / validation note |

**Differences to 01-plan §4 (to update after review):** `CartLine` added (the plan only had a session dict); `Question.answeredBy` modelled as association to `User`; `FoodItem.unit` dropped (all prices are per person in the data pack).

**Not modelled (deliberately):** company accounts, ingredients/suppliers, capacity, payments — Should/Won't items (`user-stories.md` E6, W-01 – W-10).

## Check against the code (2026-10-29, phase 10)

| Diagram | Matches the code? |
|---|---|
| Use case | ✔ Every use case has a working page; `tests/test_walkthrough.py` runs them end to end |
| Domain class | ✔ Same classes, attributes and constraints as `app/models/entities.py` and `enums.py` (analysis model: no technical ids or foreign keys); constraints enforced in `cart.py`, `ordering.py`, `questions.py` and the SQLite schema |
| Sequence (checkout) | ✔ Updated in phase 6: `validate()` is `place_order()` in `app/models/ordering.py` |
| State machine | ✔ `ALLOWED_TRANSITIONS` in `app/models/enums.py`; the admin status form only offers `OrderStatus.next_statuses` |
| MVC architecture | ✔ Updated in phase 10: domain-rule modules, `ImageStorage` and `instance/uploads` added; controllers reach the database only through repository interfaces (`tests/test_smoke.py`) |

## Oblig 5: Neo4j (2026-11-04)

| Diagram | Change | Matches the code? |
|---|---|---|
| Graph model (new) | Node labels, properties, 11 relationship types, unique constraints; allergens and dietary labels as shared nodes | ✔ Same labels, relationship types and constraints as `app/models/repositories/neo4j/` (`CONSTRAINTS` in `database.py`); `tests/repositories/test_neo4j_database.py` checks constraints and graph patterns |
| MVC architecture | Neo4j is the default storage (solid), SQLite the alternative (dashed); `factory.py` chooses by `STORAGE` | ✔ `app/models/repositories/factory.py`; no controller changed (NFR-02); `tests/test_storage_selection.py` |
| Sequence (checkout) | Database participant is Neo4j (or SQLite); repository calls shown as Cypher | ✔ `Neo4jUserRepository.get_by_email`, `Neo4jFoodItemRepository.get_many`, `Neo4jOrderRepository.add` (one transaction) |
| Domain class, use case, state machine | Unchanged: storage-independent | ✔ |

All six diagrams pass `-checkonly`; the three changed ones were re-rendered and inspected. Known cosmetic issue: in `graph-model.png` a few multiplicities sit close to their arrowheads (e.g. at ASKED/ANSWERED; layout engine limitation, labels still readable).

**Mapping domain model → graph:** every domain class is a node label; associations become relationships (`Order.customer` → `PLACED`, `OrderLine.foodItem` → `OF_ITEM`, `Question.answeredBy` → `ANSWERED`); the enums `Allergen` and `DietaryLabel` become shared nodes instead of value lists, so allergy questions are graph patterns. Technical ids and counters exist only in the graph, not in the analysis model.
