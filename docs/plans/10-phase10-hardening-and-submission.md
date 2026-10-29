# 10 — Plan: phase 10, hardening, walkthrough and submission preparation

Status: **agreed 2026-10-29** — implements the phase 10 row of `docs/plans/01-implementation-plan.md` (§8, §10, §11).
Labels: **[OFFICIAL]** Oblig 4 · **[ASSUMPTION]** our proposal.

## Goal
**[OFFICIAL] To be approved:** "the application should be executable and provides the functionalities listed in the project description. The code follows MVC, and the report contains parts 1–4." Phase 10 checks that, fixes what is missing and prepares the material for the report and the tag `oblig4`.

## Tasks
| Task | Result |
|---|---|
| Error pages | 500 page added (403, 404, 413 and "database missing" exist) |
| Escaping review | No `|safe` / `Markup` in templates; user text is auto-escaped (tests for menu, questions) |
| Accessibility pass (NFR-16) | Automated test over every page for every role: `lang`, exactly one `h1`, every visible form field has a label, every image has `alt` |
| Walkthrough | The manual walkthrough from 01-plan §8 as an automated end-to-end test on a freshly seeded database, plus one run of the README commands (`reset-db`, `run`) against a scratch database |
| Diagrams | MVC sketch updated (model-layer rule modules, picture storage); consistency check in `docs/design/README.md` re-dated |
| Docs | `CLAUDE.md` final (layout, rules as actually followed), README final, `traceability.md` test names corrected |
| Secret check | `git grep` for key patterns on the working tree and the whole history; `test_no_secrets.py` and `test_smoke.py` checks |
| Report material | `docs/report/README.md`: front-page facts, one-liner per feature, screenshot checklist with URLs and demo logins, design section pointers. The report PDF itself stays outside the repository |
| Tag `oblig4` | Created on `main` **after** this phase is merged, and pushed only when the group says so |

## Not in scope
Optional "going further" features (phase 11). Writing report part 4 ("Did design help?") — the group's own reflection.

## Acceptance (01-plan §8)
All A1–A4 and C1–C5 demonstrated by the walkthrough; full test run green; report material complete except the group's own text and screenshots; tag pushed after merge.
