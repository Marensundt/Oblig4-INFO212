"""Choosing the storage (Oblig 5): Neo4j by default, SQLite with STORAGE=sqlite. No Neo4j server needed here."""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from app.models.errors import StorageUnavailable
from app.models.repositories.factory import build_repositories, describe_storage
from app.models.repositories.neo4j.food_item_repository import Neo4jFoodItemRepository
from app.models.repositories.sqlite.food_item_repository import SqliteFoodItemRepository
from tests.factories import make_app

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
NEO4J = {"STORAGE": "neo4j", "NEO4J_URI": "bolt://localhost:7687", "NEO4J_USER": "neo4j",
         "NEO4J_PASSWORD": "", "NEO4J_DATABASE": "neo4j", "DATABASE": "unused.sqlite"}
# Nothing listens on port 1, so the connection is refused at once
UNREACHABLE = {**NEO4J, "NEO4J_URI": "bolt://127.0.0.1:1"}


def test_neo4j_is_the_default():
    # Building the repositories does not connect yet
    repos = build_repositories({**NEO4J, "STORAGE": None})
    assert isinstance(repos.food_items, Neo4jFoodItemRepository)


def test_config_default_is_neo4j():
    # Config without STORAGE in the environment (as in a fresh clone without .env)
    env = {key: value for key, value in os.environ.items() if key != "STORAGE"}
    result = subprocess.run([sys.executable, "-c", "import config; print(config.Config.STORAGE, config.TestConfig.STORAGE)"],
                            cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    assert result.stdout.split() == ["neo4j", "sqlite"]  # tests stay on SQLite unless TEST_STORAGE=neo4j


def test_sqlite_selected_by_config():
    repos = build_repositories({"STORAGE": "sqlite", "DATABASE": "unused.sqlite"})
    assert isinstance(repos.food_items, SqliteFoodItemRepository)


def test_neo4j_selected_by_config():
    repos = build_repositories(NEO4J)
    assert isinstance(repos.food_items, Neo4jFoodItemRepository)
    assert describe_storage(NEO4J) == "Neo4j database 'neo4j' at bolt://localhost:7687"


def test_unknown_storage_refused():
    with pytest.raises(ValueError, match="Unknown STORAGE"):
        build_repositories({"STORAGE": "mongodb"})


def test_unreachable_neo4j_raises_domain_error():
    with pytest.raises(StorageUnavailable):
        build_repositories(UNREACHABLE).food_items.list_all()


def test_unreachable_neo4j_shows_503_page(tmp_path):
    app = make_app(tmp_path, **UNREACHABLE)
    app.config["PROPAGATE_EXCEPTIONS"] = False  # behave like the real server
    response = app.test_client().get("/menu")
    assert response.status_code == 503
    assert "The database cannot be reached" in response.data.decode()


def test_unreachable_neo4j_cli_message(tmp_path):
    app = make_app(tmp_path, **UNREACHABLE)
    result = app.test_cli_runner().invoke(args=["reset-db", "--yes"])
    assert result.exit_code != 0
    assert "Cannot reach Neo4j at bolt://127.0.0.1:1" in result.output
    assert "Traceback" not in result.output


def test_neo4j_driver_only_in_neo4j_repositories():
    # OB4 §3 / NFR-02: only repository classes touch storage, also with Neo4j
    allowed = APP_DIR / "models" / "repositories" / "neo4j"
    driver_import = re.compile(r"^\s*(from|import)\s+neo4j\b", re.M)
    offenders = [
        path.relative_to(ROOT)
        for path in APP_DIR.rglob("*.py")
        if allowed not in path.parents and driver_import.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_neo4j_password_not_in_config_source():
    # The password is read from the environment (.env) only
    source = (ROOT / "config.py").read_text(encoding="utf-8")
    assert re.search(r'NEO4J_PASSWORD = os\.environ\.get\("NEO4J_PASSWORD", ""\)', source)
