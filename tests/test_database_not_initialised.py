"""Regression: a fresh clone without `reset-db` shows a helpful page instead of a 500 error."""
import pytest

from app.models.errors import StorageNotInitialised


def test_repository_raises_domain_error_without_schema(app):
    # The sqlite3 error must not leak out of the model layer (OB4 §3, Neo4j-ready)
    with pytest.raises(StorageNotInitialised):
        app.repos.food_items.list_published_by_category()


@pytest.mark.parametrize("path", ["/menu", "/account/login"])
def test_pages_explain_how_to_initialise_database(app, path):
    app.config["PROPAGATE_EXCEPTIONS"] = False  # behave like the real server
    client = app.test_client()
    response = client.get(path) if path == "/menu" else client.post(
        path, data={"email": "kari@example.com", "password": "whatever"}
    )
    assert response.status_code == 503
    page = response.data.decode()
    assert "The database is not set up yet" in page
    assert "flask --app run reset-db --yes" in page


@pytest.mark.sqlite_only
def test_other_database_errors_are_not_hidden(app, repos):
    # Only "no such table" is translated; real SQL errors still surface
    import sqlite3

    from app.models.repositories.sqlite.database import SqliteDatabase

    with pytest.raises(sqlite3.OperationalError):
        with SqliteDatabase(app.config["DATABASE"]).connect() as conn:
            conn.execute("SELEC 1")
