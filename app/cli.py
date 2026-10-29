"""Flask CLI commands: init-db, seed-db, reset-db. No storage code here — only factory and seed."""
import click
from flask import current_app

from app.models.repositories.factory import init_storage, storage_is_initialised
from app.models.seed import seed


def _init(yes):
    if storage_is_initialised(current_app.config) and not yes:
        click.confirm("The database already exists. Delete all data and recreate it?", abort=True)
    init_storage(current_app.config)
    click.echo(f"Initialised database {current_app.config['DATABASE']}")


def _seed():
    if seed(current_app.repos, current_app.images):
        click.echo("Seeded synthetic sample data.")
    else:
        click.echo("Database already contains data; nothing seeded.")


def register_cli(app):
    @app.cli.command("init-db")
    @click.option("--yes", is_flag=True, help="Do not ask before deleting existing data.")
    def init_db(yes):
        """Create empty tables (deletes existing data)."""
        _init(yes)

    @app.cli.command("seed-db")
    def seed_db():
        """Insert synthetic sample data (food items, an admin, test customers, orders)."""
        if not storage_is_initialised(current_app.config):
            raise click.ClickException("Run `flask --app run init-db` first.")
        _seed()

    @app.cli.command("reset-db")
    @click.option("--yes", is_flag=True, help="Do not ask before deleting existing data.")
    def reset_db(yes):
        """init-db followed by seed-db."""
        _init(yes)
        _seed()
