"""Model layer: domain classes, domain rules and all data access.

Only repository classes in app/models/repositories/ may touch the database,
so SQLite can later be replaced by Neo4j without changing controllers or views.
Implemented in phase 1 (docs/plans/01-implementation-plan.md).
"""
