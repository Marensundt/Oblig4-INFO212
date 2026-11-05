from app.models.entities import Question
from app.models.errors import DataIntegrityError, NotFound
from app.models.repositories.interfaces import QuestionRepository
from app.models.repositories.neo4j.database import next_ids, now, to_native

# A question with the order it is about, its author and (if answered) the admin who answered
_LOAD = (
    " MATCH (author:User)-[:ASKED]->(q)-[:ABOUT]->(o:Order)"
    " OPTIONAL MATCH (admin:User)-[:ANSWERED]->(q)"
    " RETURN q, o.id AS order_id, author.id AS author_id, admin.id AS answered_by"
)


def _to_question(record):
    node = record["q"]
    return Question(
        id=node["id"],
        order_id=record["order_id"],
        author_id=record["author_id"],
        text=node["text"],
        asked_at=to_native(node["asked_at"]),
        answer_text=node.get("answer_text"),
        answered_by=record["answered_by"],
        answered_at=to_native(node.get("answered_at")),
    )


class Neo4jQuestionRepository(QuestionRepository):
    def __init__(self, db):
        self.db = db

    def add(self, question):
        with self.db.transaction() as tx:
            [question_id] = next_ids(tx, "Question")
            record = tx.run(
                "MATCH (author:User {id: $author_id}), (o:Order {id: $order_id})"
                " CREATE (author)-[:ASKED]->(:Question {id: $id, text: $text, asked_at: $asked_at})-[:ABOUT]->(o)"
                " RETURN count(*) AS created",
                author_id=question.author_id, order_id=question.order_id, id=question_id,
                text=question.text, asked_at=now(),
            ).single()
            if record["created"] == 0:
                raise DataIntegrityError(f"Order {question.order_id} or user {question.author_id} does not exist")
        return self.get(question_id)

    def get(self, question_id):
        with self.db.transaction() as tx:
            questions = self._load(tx, "MATCH (q:Question {id: $id})", id=question_id)
        return questions[0] if questions else None

    def list_for_order(self, order_id):
        with self.db.transaction() as tx:
            return self._load(tx, "MATCH (q:Question)-[:ABOUT]->(:Order {id: $order_id})", order_id=order_id,
                              order_by="q.asked_at, q.id")

    def list_all(self):
        with self.db.transaction() as tx:
            return self._load(tx, "MATCH (q:Question)", order_by="q.answer_text IS NOT NULL, q.asked_at, q.id")

    def answer(self, question_id, text, admin_id):
        with self.db.transaction() as tx:
            record = tx.run(
                "MATCH (q:Question {id: $id})"
                " OPTIONAL MATCH (admin:User {id: $admin_id})"
                " WITH q, admin OPTIONAL MATCH (:User)-[old:ANSWERED]->(q) DELETE old"
                " WITH DISTINCT q, admin"
                " SET q.answer_text = $text, q.answered_at = $answered_at"
                " FOREACH (_ IN CASE WHEN admin IS NULL THEN [] ELSE [1] END | CREATE (admin)-[:ANSWERED]->(q))"
                " RETURN admin IS NOT NULL AS admin_found",
                id=question_id, text=text, answered_at=now(), admin_id=admin_id,
            ).single()
            if record is None:
                raise NotFound(f"Question {question_id}")
            if admin_id is not None and not record["admin_found"]:
                raise DataIntegrityError(f"User {admin_id} does not exist")
        return self.get(question_id)

    def _load(self, tx, match, order_by="q.id", **params):
        # order_by is one of the fixed expressions above, never user input
        return [_to_question(record) for record in tx.run(f"{match}{_LOAD} ORDER BY {order_by}", **params)]
