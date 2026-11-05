# 11 — Plan: Neo4j as alternative storage (Oblig 5)

Status: **draft 2026-11-04** — to be agreed by the group before merge.
Labels: **[OFFICIAL]** Oblig 5 · **[ASSUMPTION]** our proposal.

## Goal
**[OFFICIAL]** Store the Ekte Mat data in Neo4j instead of SQLite, using the official Neo4j Python driver.
**[DECISION 2026-11-04]** Neo4j is the default storage; SQLite keeps working with `STORAGE=sqlite`. Tests use SQLite unless `TEST_STORAGE=neo4j`. Only the
repository layer changes: controllers, views, domain rules and the seed script are untouched (the point of the
repository interfaces from phase 1).

## Configuration (environment variables, never in code)
| Variable | Default | Meaning |
|---|---|---|
| `STORAGE` | `neo4j` | `neo4j` or `sqlite` (chosen in `app/models/repositories/factory.py`) |
| `NEO4J_URI` | `bolt://localhost:7687` | Bolt address |
| `NEO4J_USER` | `neo4j` | User name |
| `NEO4J_PASSWORD` | *(empty)* | Password; empty means "no authentication" (only for servers started with `NEO4J_AUTH=none`) |
| `NEO4J_DATABASE` | `neo4j` | Database name (Community Edition has only `neo4j`) |

## Graph model
```
(:User)-[:PLACED]->(:Order)-[:HAS_LINE]->(:OrderLine)-[:OF_ITEM]->(:FoodItem)
(:Order)-[:HAS_GUEST_GROUP]->(:GuestGroup)-[:ALLERGIC_TO]->(:Allergen)
(:FoodItem)-[:IN_CATEGORY]->(:EventCategory)
(:FoodItem)-[:CONTAINS]->(:Allergen)
(:FoodItem)-[:HAS_LABEL]->(:DietaryLabel)
(:User)-[:ASKED]->(:Question)-[:ABOUT]->(:Order)
(:User)-[:ANSWERED]->(:Question)
```
- **Allergens and dietary labels are nodes** (one per enum value, created by `init-db`), so food items and guest
  groups share the same `:Allergen` node. That makes "which ordered dishes contain an allergen a guest group has?"
  a single graph pattern (useful later for A3).
- **Integer ids** as before (URLs such as `/admin/food/<int:id>` stay the same): one `(:Counter {name})` node per
  label, incremented inside the same transaction. Order numbers (`YY-NNNN`) use a counter per year.
- Unique constraints: `id` on every label, `User.email`, `EventCategory.slug`, `Order.order_number`,
  `Counter.name`, `Allergen.code`, `DietaryLabel.code`.
- Totals are not stored (DV-05). Deleting a food item removes only its `OF_ITEM` relationships; order lines keep
  name and price (same as `ON DELETE SET NULL` in SQLite).
- Value rules that SQLite enforced with `CHECK` (price > 0, min order ≥ 1, guests ≥ 1, line quantity ≥ 1,
  group count ≥ 1, references that must exist) are checked in the Neo4j repositories and raise
  `DataIntegrityError`. Community Edition has no property-value constraints.
- `init-db` deletes all Ekte Mat data, (re)creates constraints, allergen/label nodes and a `(:EkteMatSchema)` marker;
  repositories raise `StorageNotInitialised` until the marker exists (same 503 page as SQLite).
- Server down or wrong password → new `StorageUnavailable` domain error (503 page / CLI message), never a driver
  exception in a controller. **[DECISION 2026-11-04]** The message is a branch in `errors/database.html`, the only
  view file this change touches; NFR-02 is updated to allow it as an exception (no controller and no page that
  shows or edits data changes).

## Code
- `app/models/repositories/neo4j/`: `database.py` (driver, unit of work, schema, error mapping) and one
  repository per interface. All Cypher is parameterised (`$name`); only fixed query fragments are composed.
- `factory.py`: chooses SQLite or Neo4j from `STORAGE`.
- `seed.py` unchanged — it already uses repositories only, so `reset-db` seeds Neo4j the same way.

## Tests
- Default `pytest` runs on SQLite as before (no Neo4j needed). Neo4j-independent tests for the factory and
  connection errors always run.
- `TEST_STORAGE=neo4j pytest` runs **the whole suite** (repositories, controllers, walkthrough) against the server
  in `NEO4J_TEST_URI` / `NEO4J_TEST_USER` / `NEO4J_TEST_PASSWORD`. **Every test wipes that database.** Tests that
  are about the SQLite file itself are marked `sqlite_only`; Neo4j-specific tests are marked `neo4j`.
- GitHub Actions: a second job with a `neo4j:5` service container (`NEO4J_AUTH=none`, no password needed).

## Not in scope
Removing SQLite. Migrating data from an existing SQLite file to Neo4j (`reset-db` seeds fresh synthetic data).
