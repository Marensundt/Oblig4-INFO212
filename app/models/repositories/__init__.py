"""Repositories: the only code that touches storage (OB4 §3).

Controllers use `current_app.repos` (see factory.py) and never open the database themselves.
"""
