"""Demo food pictures are part of the seed, so a fresh clone shows a complete menu (C1 "each card shows picture")."""
import os

from app.models.images import check_svg
from app.models.seed import FOOD_ITEMS, PICTURES, SEED_PICTURES_DIR, seed


def test_every_seed_item_has_its_own_picture_file():
    names = {item[0] for item in FOOD_ITEMS}
    assert set(PICTURES) == names
    files = {path.name for path in SEED_PICTURES_DIR.glob("*.svg")}
    assert files == set(PICTURES.values())  # no missing and no unused files
    assert len(set(PICTURES.values())) == len(PICTURES)


def test_seed_pictures_are_safe_svgs_with_a_title():
    for name in PICTURES.values():
        data = (SEED_PICTURES_DIR / name).read_bytes()
        check_svg(data)
        assert b"<title>" in data, name
        assert len(data) < 20_000, name


def test_seed_with_storage_sets_pictures(app, repos):
    assert seed(repos, app.images)
    folder = app.config["UPLOAD_FOLDER"]
    for item in repos.food_items.list_all():
        assert item.image_filename == f"seed-{PICTURES[item.name]}"
        assert os.path.isfile(os.path.join(folder, item.image_filename))


def test_menu_shows_pictures_not_placeholders(app, client, repos):
    seed(repos, app.images)
    page = client.get("/menu").data.decode()
    assert "placeholder.svg" not in page
    assert 'src="/uploads/seed-fish-soup.svg" alt="Fish soup with Bergen cod"' in page
    picture = client.get("/uploads/seed-fish-soup.svg")
    assert picture.status_code == 200 and picture.mimetype == "image/svg+xml"


def test_seed_without_storage_keeps_items_without_pictures(repos):
    # Repository-only callers (e.g. tests) get no files written
    seed(repos)
    assert all(item.image_filename is None for item in repos.food_items.list_all())


def test_reset_db_installs_pictures(app):
    result = app.test_cli_runner().invoke(args=["reset-db", "--yes"])
    assert result.exit_code == 0, result.output
    assert all(item.image_filename for item in app.repos.food_items.list_all())
    assert len([f for f in os.listdir(app.config["UPLOAD_FOLDER"]) if f.startswith("seed-")]) == 12
