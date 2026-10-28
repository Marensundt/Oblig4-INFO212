from app.models.entities import Question
from app.models.errors import NotFound
from app.models.repositories.interfaces import QuestionRepository
from app.models.repositories.sqlite.database import now_iso, parse_datetime


def _to_question(row):
    return Question(
        id=row["id"],
        order_id=row["order_id"],
        author_id=row["author_id"],
        text=row["text"],
        asked_at=parse_datetime(row["asked_at"]),
        answer_text=row["answer_text"],
        answered_by=row["answered_by"],
        answered_at=parse_datetime(row["answered_at"]),
    )


class SqliteQuestionRepository(QuestionRepository):
    def __init__(self, db):
        self.db = db

    def add(self, question):
        with self.db.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO questions (order_id, author_id, text, asked_at) VALUES (?, ?, ?, ?)",
                (question.order_id, question.author_id, question.text, now_iso()),
            )
            row = conn.execute("SELECT * FROM questions WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _to_question(row)

    def list_for_order(self, order_id):
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM questions WHERE order_id = ? ORDER BY asked_at, id", (order_id,)
            ).fetchall()
        return [_to_question(row) for row in rows]

    def list_all(self):
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM questions ORDER BY answer_text IS NOT NULL, asked_at, id"
            ).fetchall()
        return [_to_question(row) for row in rows]

    def answer(self, question_id, text, admin_id):
        with self.db.connect() as conn:
            cursor = conn.execute(
                "UPDATE questions SET answer_text = ?, answered_by = ?, answered_at = ? WHERE id = ?",
                (text, admin_id, now_iso(), question_id),
            )
            if cursor.rowcount == 0:
                raise NotFound(f"Question {question_id}")
            row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
        return _to_question(row)
