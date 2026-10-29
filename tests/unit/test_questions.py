"""Question rules (OB4 C5, A4; US-18, US-20)."""
import pytest

from app.models.entities import User
from app.models.errors import AlreadyAnswered, InvalidQuestion, NotFound
from app.models.questions import MAX_TEXT_LENGTH, answer_question, ask_question
from app.models.security import hash_password
from tests.factories import PASSWORD, make_order


@pytest.fixture
def order(repos, soup, customer):
    return repos.orders.add(make_order(customer.id, soup))


def test_ask_on_own_order(repos, customer, order):
    # US-18 AC1
    question = ask_question(repos, customer, order.id, "  Can we pick up the food ourselves?  ")
    assert question.text == "Can we pick up the food ourselves?"
    assert question.asked_at is not None
    assert question.author_id == customer.id
    assert repos.questions.list_for_order(order.id) == [question]


@pytest.mark.parametrize("text", ["", "   \n "])
def test_empty_question_rejected(repos, customer, order, text):
    # US-18 AC2
    with pytest.raises(InvalidQuestion, match="Write your question"):
        ask_question(repos, customer, order.id, text)
    assert repos.questions.list_for_order(order.id) == []


def test_too_long_question_rejected(repos, customer, order):
    with pytest.raises(InvalidQuestion, match=f"at most {MAX_TEXT_LENGTH}"):
        ask_question(repos, customer, order.id, "x" * (MAX_TEXT_LENGTH + 1))
    ask_question(repos, customer, order.id, "x" * MAX_TEXT_LENGTH)  # exactly the limit is fine


def test_question_on_other_customers_order_refused(repos, order):
    # US-18 AC3
    other = repos.users.add(User("annen@example.com", hash_password(PASSWORD), "Annen Kunde"))
    with pytest.raises(NotFound):
        ask_question(repos, other, order.id, "Hello?")
    with pytest.raises(NotFound):
        ask_question(repos, other, 999, "Hello?")
    assert repos.questions.list_all() == []


def test_answer_stored_with_admin_and_time(repos, customer, admin, order):
    # US-20 AC2
    question = ask_question(repos, customer, order.id, "Cancellation terms?")
    answered = answer_question(repos, admin, question.id, " Free until 14 days before. ")
    assert answered.answer_text == "Free until 14 days before."
    assert answered.answered_by == admin.id
    assert answered.answered_at is not None


def test_empty_answer_rejected(repos, customer, admin, order):
    # US-20 AC3
    question = ask_question(repos, customer, order.id, "Cancellation terms?")
    with pytest.raises(InvalidQuestion, match="Write your answer"):
        answer_question(repos, admin, question.id, "  ")
    assert not repos.questions.get(question.id).is_answered


def test_question_answered_once(repos, customer, admin, order):
    question = ask_question(repos, customer, order.id, "Cancellation terms?")
    answer_question(repos, admin, question.id, "Free until 14 days before.")
    with pytest.raises(AlreadyAnswered):
        answer_question(repos, admin, question.id, "Changed my mind.")
    assert repos.questions.get(question.id).answer_text == "Free until 14 days before."


def test_answer_unknown_question(repos, admin):
    with pytest.raises(NotFound):
        answer_question(repos, admin, 999, "Answer")
