"""Customer accounts: registration and login (OB4 C3 "Log in (or register)"; US-10, US-11)."""
from app.models.entities import User
from app.models.enums import Role
from app.models.security import check_password, hash_password

MIN_PASSWORD_LENGTH = 8  # ASSUMPTION: not specified in Oblig 4


def register_customer(repos, name, email, password, phone=None):
    """Create a customer account. Raises DuplicateEmail if the e-mail is already registered.

    Registration always creates role customer; admin accounts come from the seed script.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name.strip(),
        phone=(phone or "").strip() or None,
        role=Role.CUSTOMER,
    )
    return repos.users.add(user)


def authenticate(repos, email, password):
    """Return the user if e-mail and password match, otherwise None (no hint which one was wrong)."""
    user = repos.users.get_by_email(email)
    if user is None or not check_password(user.password_hash, password):
        return None
    return user
