"""Questions about orders (OB4 C5, A4; US-18 – US-20). No Flask imports."""
from app.models.entities import Question
from app.models.errors import AlreadyAnswered, InvalidQuestion, NotFound

MAX_TEXT_LENGTH = 1000  # ASSUMPTION


def _clean(text, what):
    text = (text or "").strip()
    if not text:
        raise InvalidQuestion(f"Write your {what} first.")  # US-18 AC2, US-20 AC3
    if len(text) > MAX_TEXT_LENGTH:
        raise InvalidQuestion(f"The {what} can be at most {MAX_TEXT_LENGTH} characters.")
    return text


def ask_question(repos, customer, order_id, text):
    """Store a question on one of the customer's own orders (US-18). Others' orders raise NotFound (AC3)."""
    order = repos.orders.get(order_id)
    if order is None or order.customer_id != customer.id:
        raise NotFound(f"Order {order_id}")
    return repos.questions.add(Question(order.id, customer.id, _clean(text, "question")))


def answer_question(repos, admin, question_id, text):
    """Store the answer with the admin and the time (US-20 AC2). A question is answered once."""
    question = repos.questions.get(question_id)
    if question is None:
        raise NotFound(f"Question {question_id}")
    if question.is_answered:
        raise AlreadyAnswered("This question has already been answered.")
    return repos.questions.answer(question_id, _clean(text, "answer"), admin.id)
