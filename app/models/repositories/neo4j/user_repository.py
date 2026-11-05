from app.models.entities import User
from app.models.enums import Role
from app.models.errors import DataIntegrityError, DuplicateEmail
from app.models.repositories.interfaces import UserRepository
from app.models.repositories.neo4j.database import next_ids, now, to_native


def _to_user(node):
    return User(
        id=node["id"],
        email=node["email"],
        password_hash=node["password_hash"],
        name=node["name"],
        phone=node.get("phone"),
        role=Role(node["role"]),
        created_at=to_native(node["created_at"]),
    )


class Neo4jUserRepository(UserRepository):
    def __init__(self, db):
        self.db = db

    def add(self, user):
        try:
            with self.db.transaction() as tx:
                [user_id] = next_ids(tx, "User")
                tx.run(
                    "CREATE (:User {id: $id, email: $email, password_hash: $password_hash, name: $name,"
                    " phone: $phone, role: $role, created_at: $created_at})",
                    id=user_id, email=user.email.strip().lower(), password_hash=user.password_hash,
                    name=user.name, phone=user.phone, role=Role(user.role).value, created_at=now(),
                ).consume()
        except DataIntegrityError as error:
            if "email" in str(error):
                raise DuplicateEmail(user.email) from error
            raise
        return self.get(user_id)

    def get(self, user_id):
        with self.db.transaction() as tx:
            record = tx.run("MATCH (u:User {id: $id}) RETURN u", id=user_id).single()
        return _to_user(record["u"]) if record else None

    def get_by_email(self, email):
        with self.db.transaction() as tx:
            record = tx.run("MATCH (u:User {email: $email}) RETURN u", email=email.strip().lower()).single()
        return _to_user(record["u"]) if record else None

    def list_customers(self):
        with self.db.transaction() as tx:
            records = list(tx.run(
                "MATCH (u:User {role: $role}) RETURN u ORDER BY u.name, u.id", role=Role.CUSTOMER.value
            ))
        return [_to_user(record["u"]) for record in records]
