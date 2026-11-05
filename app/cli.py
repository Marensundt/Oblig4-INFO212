"""Flask CLI commands: init-db, seed-db, reset-db. No storage code here — only factory and seed."""
import functools

import click
from flask import current_app

from app.models.errors import StorageUnavailable
from app.models.repositories.factory import describe_storage, init_storage, storage_is_initialised
from app.models.seed import seed


def _storage_errors(command):
    """Show "cannot reach Neo4j" as a short message instead of a traceback."""
    @functools.wraps(command)
    def wrapper(*args, **kwargs):
        try:
            return command(*args, **kwargs)
        except StorageUnavailable as error:
            raise click.ClickException(f"{error}. Is the server running, and are NEO4J_* in .env correct?")
    return wrapper


def _init(yes):
    if storage_is_initialised(current_app.config) and not yes:
        click.confirm("The database already exists. Delete all data and recreate it?", abort=True)
    init_storage(current_app.config)
    click.echo(f"Initialised database {describe_storage(current_app.config)}")


def _seed():
    if seed(current_app.repos, current_app.images):
        click.echo("Seeded synthetic sample data.")
    else:
        click.echo("Database already contains data; nothing seeded.")


def register_cli(app):
    @app.cli.command("init-db")
    @click.option("--yes", is_flag=True, help="Do not ask before deleting existing data.")
    @_storage_errors
    def init_db(yes):
        """Create empty tables (deletes existing data)."""
        _init(yes)

    @app.cli.command("seed-db")
    @_storage_errors
    def seed_db():
        """Insert synthetic sample data (food items, an admin, test customers, orders)."""
        if not storage_is_initialised(current_app.config):
            raise click.ClickException("Run `flask --app run init-db` first.")
        _seed()

    @app.cli.command("reset-db")
    @click.option("--yes", is_flag=True, help="Do not ask before deleting existing data.")
    @_storage_errors
    def reset_db(yes):
        """init-db followed by seed-db."""
        _init(yes)
        _seed()
