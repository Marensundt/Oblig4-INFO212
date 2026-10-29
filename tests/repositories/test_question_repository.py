import pytest

from app.models.entities import Question
from app.models.errors import NotFound
from tests.factories import make_order


@pytest.fixture
def order(repos, soup, customer):
    return repos.orders.add(make_order(customer.id, soup))


def test_add_and_list_for_order(repos, order, customer):
    question = repos.questions.add(Question(order.id, customer.id, "What are your cancellation terms?"))
    assert question.id is not None
    assert question.asked_at is not None
    assert not question.is_answered
    assert repos.questions.list_for_order(order.id) == [question]


def test_answer(repos, order, customer, admin):
    question = repos.questions.add(Question(order.id, customer.id, "Can you deliver at 10:45?"))
    answered = repos.questions.answer(question.id, "Yes, between 10:45 and 11:00.", admin.id)
    assert answered.is_answered
    assert answered.answered_by == admin.id
    assert answered.answered_at is not None
    with pytest.raises(NotFound):
        repos.questions.answer(999, "x", admin.id)


def test_list_all_unanswered_first(repos, order, customer, admin):
    first = repos.questions.add(Question(order.id, customer.id, "First"))
    second = repos.questions.add(Question(order.id, customer.id, "Second"))
    repos.questions.answer(first.id, "Answer", admin.id)
    assert [q.id for q in repos.questions.list_all()] == [second.id, first.id]


def test_get(repos, order, customer):
    question = repos.questions.add(Question(order.id, customer.id, "Can we pick up ourselves?"))
    assert repos.questions.get(question.id) == question
    assert repos.questions.get(999) is None
