import pytest

from app import create_app
from config import TestConfig


@pytest.fixture
def app(tmp_path):
    """App with test settings and a temporary database path; never touches instance/."""
    return create_app(TestConfig, overrides={"DATABASE": str(tmp_path / "test.sqlite")})


@pytest.fixture
def client(app):
    return app.test_client()
