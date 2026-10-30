# Demo food pictures — sources and licence

All pictures in this folder are **original illustrations made for Ekte Mat Online** (INFO212 Oblig 4).
They were written by hand as SVG code (simple shapes and colours) with Claude Code as the coding agent.
No photographs, third-party images, clip art, icons or fonts were used or traced, so no external
licence or attribution applies. They belong to this student project and fall under the same terms
as the rest of the repository.

| File | Food item |
|---|---|
| `fish-soup.svg` | Fish soup with Bergen cod |
| `lamb-voss.svg` | Slow-cooked lamb from Voss |
| `beetroot-salad.svg` | Beetroot and chickpea salad |
| `rakfisk.svg` | Rakfisk tasting |
| `lunch-buffet.svg` | Seasonal lunch buffet |
| `harvest-menu.svg` | Vegetarian harvest menu |
| `seafood.svg` | Fish and seafood menu |
| `sandwiches.svg` | Meeting sandwiches |
| `confirmation-buffet.svg` | Konfirmasjon buffet |
| `julebord.svg` | Traditional julebord buffet |
| `wedding-dinner.svg` | Wedding served dinner (3 courses) |
| `kids-menu.svg` | Kids menu |

**How they are used:** `flask --app run reset-db --yes` (or `seed-db`) copies each picture into the
upload folder as `seed-<file>` and sets it on the food item (`app/models/seed.py`, `PICTURES`). They pass
the same SVG safety check as uploaded pictures. An admin can replace them on the item's Picture page
(A2); the seed files are never deleted.

**Other images in the repository:** `app/static/img/placeholder.svg` (shown for items without a picture)
and `app/static/img/favicon.svg` are also original SVGs made for this project. The diagrams in
`docs/design/img/` are rendered from the project's own PlantUML sources.
