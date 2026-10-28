from app.models.entities import User
from app.models.enums import Role
from app.models.errors import DataIntegrityError, DuplicateEmail
from app.models.repositories.interfaces import UserRepository
from app.models.repositories.sqlite.database import now_iso, parse_datetime


def _to_user(row):
    return User(
        id=row["id"],
        email=row["email"],
        password_hash=row["password_hash"],
        name=row["name"],
        phone=row["phone"],
        role=Role(row["role"]),
        created_at=parse_datetime(row["created_at"]),
    )


class SqliteUserRepository(UserRepository):
    def __init__(self, db):
        self.db = db

    def add(self, user):
        created_at = now_iso()
        try:
            with self.db.connect() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (email, password_hash, name, phone, role, created_at)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (user.email.strip().lower(), user.password_hash, user.name, user.phone,
                     Role(user.role).value, created_at),
                )
        except DataIntegrityError as error:
            if "users.email" in str(error):
                raise DuplicateEmail(user.email) from error
            raise
        return self.get(cursor.lastrowid)

    def get(self, user_id):
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _to_user(row) if row else None

    def get_by_email(self, email):
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
            ).fetchone()
        return _to_user(row) if row else None

    def list_customers(self):
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM users WHERE role = ? ORDER BY name", (Role.CUSTOMER.value,)
            ).fetchall()
        return [_to_user(row) for row in rows]
