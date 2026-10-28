from app.models.repositories.factory import storage_is_initialised


def test_reset_db_creates_and_seeds(app):
    result = app.test_cli_runner().invoke(args=["reset-db", "--yes"])
    assert result.exit_code == 0, result.output
    assert "Seeded synthetic sample data." in result.output
    assert len(app.repos.food_items.list_all()) == 12


def test_init_db_asks_before_deleting_data(app):
    runner = app.test_cli_runner()
    runner.invoke(args=["reset-db", "--yes"])
    result = runner.invoke(args=["init-db"], input="n\n")
    assert result.exit_code != 0  # aborted
    assert len(app.repos.food_items.list_all()) == 12


def test_seed_db_requires_initialised_database(app):
    assert not storage_is_initialised(app.config)
    result = app.test_cli_runner().invoke(args=["seed-db"])
    assert result.exit_code != 0
    assert "init-db" in result.output


def test_seed_db_twice_does_not_duplicate(app):
    runner = app.test_cli_runner()
    runner.invoke(args=["init-db", "--yes"])
    runner.invoke(args=["seed-db"])
    result = runner.invoke(args=["seed-db"])
    assert "nothing seeded" in result.output
    assert len(app.repos.orders.list()) == 6
