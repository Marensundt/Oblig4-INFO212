"""Application configuration.

Secrets (SECRET_KEY, ANTHROPIC_API_KEY) are read from environment variables,
normally from a local, git-ignored .env file. Never put real values in this file.
"""
import os
import secrets


class Config:
    # A random fallback keeps the app runnable without .env; sessions then reset on restart.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    # Session cookie: not readable from JavaScript, not sent on cross-site POSTs.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Storage implementation chosen in app/models/repositories/factory.py: "neo4j" (default, Oblig 5) or "sqlite".
    STORAGE = (os.environ.get("STORAGE") or "neo4j").strip().lower()

    # File-based SQLite database; None means "instance/ektemat.sqlite" (set in create_app).
    DATABASE = os.environ.get("DATABASE")

    # Neo4j (Oblig 5, the default storage). The password comes from .env only.
    NEO4J_URI = os.environ.get("NEO4J_URI") or "bolt://localhost:7687"
    NEO4J_USER = os.environ.get("NEO4J_USER") or "neo4j"
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE") or "neo4j"

    # Folder for food item pictures; None means "instance/uploads" (set in create_app).
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")

    # Upload limit for food item images (A2): 2 MB.
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    # Optional AI image service (A2, phase 9). Empty means "use the offline placeholder".
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    # Tests never use the development database from .env; tests/conftest.py switches to Neo4j
    # only when TEST_STORAGE=neo4j, with the separate NEO4J_TEST_* settings.
    STORAGE = "sqlite"
    WTF_CSRF_ENABLED = False
    ANTHROPIC_API_KEY = ""
