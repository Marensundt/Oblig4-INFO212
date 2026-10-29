# 09 — Plan: phase 9 ★, food item images (A2)

Status: **agreed 2026-10-29** — implements the phase 9 row of `docs/plans/01-implementation-plan.md` (§2, §5, §8) and closes **OPEN-4** with the approach proposed there.
Labels: **[OFFICIAL]** Oblig 4 · **[ASSUMPTION]** our proposal (from `docs/backlog/user-stories.md`).

## Requirement
**[OFFICIAL] A2 Images:** "Upload a picture for each item, or write an instruction that an AI agent or image service uses to create or modify the picture. The admin previews the result before it is saved."
Stories: **US-04** upload a picture, **US-05** create or modify a picture from an instruction.

## Decision (OPEN-4)
Claude cannot output bitmap images, so the AI service asks Claude to **write or modify an SVG** from the instruction **[ASSUMPTION]**. Two implementations behind one `ImageService` interface:
- `PlaceholderImageService` — offline default: draws a simple SVG card with the item name and the instruction. Used when no API key is set and in all tests.
- `ClaudeSvgImageService` — calls the Claude API (`anthropic` SDK, model `claude-opus-5-5`, server-side refusal fallback) only if `ANTHROPIC_API_KEY` is set in the environment (`.env`, git-ignored). Mocked in tests.
"Modify" sends the current SVG with the instruction; raster pictures (JPG/PNG/WebP) can only be replaced.

## Scope
| Route | Purpose | Story |
|---|---|---|
| `GET /admin/food/<id>/image` | Current picture, upload form, instruction form (new / modify current) | US-04, US-05 |
| `POST /admin/food/<id>/image/upload` | Upload JPG/PNG/WebP/SVG ≤ 2 MB → pending picture | US-04 |
| `POST /admin/food/<id>/image/generate` | Instruction → image service → pending picture | US-05 |
| `GET /admin/food/<id>/image/preview` | Preview of the pending picture next to the current one, with Save / Discard | OFFICIAL "previews before it is saved" |
| `GET /admin/food/<id>/image/pending` | The pending file itself (admin only) | — |
| `POST /admin/food/<id>/image/save`, `…/discard` | Save: item uses the picture (old file removed). Discard: pending file deleted, item unchanged | — |

All routes `@admin_required`, POSTs with CSRF. The food list and edit form link to the picture page. Only saved pictures appear in C1.

## Rules (in `app/models/images.py`)
| Rule | Label |
|---|---|
| File types JPG, PNG, WebP, SVG; extension **and** file content must match | ASSUMPTION |
| Max 2 MB per upload (`MAX_CONTENT_LENGTH`) | ASSUMPTION |
| SVGs (uploaded or generated) are refused if they contain scripts, event handlers, `foreignObject`, external links or DOCTYPE/entities | ASSUMPTION (security, NFR) |
| Stored file names are generated (`item-<id>-<random>.<ext>`), never the uploaded name | ASSUMPTION |
| Pictures are served with `Content-Security-Policy: default-src 'none'` and `nosniff` | ASSUMPTION (security) |
| Instruction required, max 500 characters | ASSUMPTION |
| No API key in the repository; a test scans tracked files for key patterns | OFFICIAL (§3 security basics) |

## Design
- Model: `app/models/images.py` (validation, `ImageStorage` for pending and saved files, `ImageError`), `app/models/image_service.py` (`ImageService`, `PlaceholderImageService`, `ClaudeSvgImageService`, `build_image_service(config)`). The pending picture is remembered in the session (`pending_image`: item id + file name).
- Controller: routes in `admin.py`; forms `ImageUploadForm`, `ImageInstructionForm`. `create_app` attaches `app.image_service` and `app.images`.
- Views: `admin/food/image.html`, `admin/food/image_preview.html`.
- Dependency: `anthropic==2.3.0` in `requirements.txt`; imported only by `ClaudeSvgImageService`.

## Tests
`tests/unit/test_images.py` (types, content check, SVG safety, storage), `tests/unit/test_image_service.py` (placeholder output; Claude service with a fake client: request fields, SVG extraction, refusal, API error, unsafe SVG; factory chooses placeholder without key), `tests/controllers/test_admin_images.py` (upload valid/invalid/too large, generate → preview → discard leaves item unchanged, save updates item and menu, modify sends current SVG, raster cannot be modified, customer 403, pending only for admin, CSP header), `tests/test_no_secrets.py`.

## Acceptance (01-plan §8)
Admin can upload or generate/modify an image, preview it, and only saved images appear in C1; no API key in the repository; all tests pass.
