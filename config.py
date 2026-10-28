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

    # Storage implementation chosen in app/models/repositories/factory.py (Neo4j in Oblig 5).
    STORAGE = "sqlite"

    # File-based SQLite database; None means "instance/ektemat.sqlite" (set in create_app).
    DATABASE = os.environ.get("DATABASE")

    # Folder for food item pictures; None means "instance/uploads" (set in create_app).
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")

    # Upload limit for food item images (A2): 2 MB.
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    # Optional AI image service (A2, phase 9). Empty means "use the offline placeholder".
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    WTF_CSRF_ENABLED = False
    ANTHROPIC_API_KEY = ""
