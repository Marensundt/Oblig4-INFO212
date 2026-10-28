"""Phase 0 smoke tests: the skeleton starts, routes respond and the MVC layout is in place."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"


def test_app_uses_test_config(app, tmp_path):
    assert app.config["TESTING"] is True
    assert app.config["DATABASE"] == str(tmp_path / "test.sqlite")


def test_root_redirects_to_menu(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/menu")


def test_menu_page(client, repos):
    response = client.get("/menu")
    assert response.status_code == 200
    assert b"<h1>Menu</h1>" in response.data


def test_account_page_requires_login(client):
    response = client.get("/account/")
    assert response.status_code == 302
    assert "/account/login" in response.headers["Location"]


def test_admin_page_requires_login(client):
    response = client.get("/admin/")
    assert response.status_code == 302
    assert "/account/login" in response.headers["Location"]


def test_unknown_page_returns_404_template(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert b"Page not found" in response.data


def test_three_blueprints_registered(app):
    # OB4 §3: controllers are Flask routes grouped in blueprints (shop, account, admin)
    assert set(app.blueprints) == {"shop", "account", "admin"}


def test_mvc_layers_visible_in_folder_structure():
    # OB4 §3: the three layers must be visible in the folder structure (NFR-01)
    assert (APP_DIR / "models").is_dir()
    assert (APP_DIR / "views" / "templates").is_dir()
    assert (APP_DIR / "controllers").is_dir()


def test_sqlite_only_in_repositories():
    # OB4 §3: only repository classes in the model layer touch storage (NFR-02)
    allowed = APP_DIR / "models" / "repositories" / "sqlite"
    offenders = [
        path.relative_to(ROOT)
        for path in APP_DIR.rglob("*.py")
        if allowed not in path.parents and "sqlite3" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_no_api_keys_in_source():
    # OB4 §3: the project must not include a Claude API key (NFR-03)
    key_pattern = re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")
    skip = {".git", ".venv", "venv", "tools", "instance", "docs", "EkteMat_project_inbox"}
    offenders = []
    for path in ROOT.rglob("*"):
        if path.is_file() and not skip.intersection(path.relative_to(ROOT).parts):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if key_pattern.search(text):
                offenders.append(path.relative_to(ROOT))
    assert offenders == []
