"""Admin reads and answers questions (OB4 A4; US-20) and the C5 round trip."""
import re

import pytest

from app.models.entities import Question
from tests.factories import PASSWORD, log_in, make_order


@pytest.fixture
def order(repos, soup, customer):
    return repos.orders.add(make_order(customer.id, soup))


@pytest.fixture
def admin_client(client, admin):
    log_in(client, "admin@example.com", PASSWORD)
    return client


def test_list_unanswered_first_with_order_link_and_customer(admin_client, repos, admin, customer, order):
    # US-20 AC1
    old = repos.questions.add(Question(order.id, customer.id, "Answered one"))
    repos.questions.answer(old.id, "Yes.", admin.id)
    repos.questions.add(Question(order.id, customer.id, "Open one"))
    page = admin_client.get("/admin/questions").data.decode()
    assert page.index("Open one") < page.index("Answered one")
    assert f'<a href="/admin/orders/{order.id}">Order {order.order_number}</a>' in page
    assert "Test Kunde" in page
    assert page.count('class="form answer-form"') == 1  # only the unanswered one has a form


def test_answer_from_list(admin_client, repos, admin, customer, order):
    # US-20 AC2
    question = repos.questions.add(Question(order.id, customer.id, "Cancellation terms?"))
    response = admin_client.post(f"/admin/questions/{question.id}/answer",
                                 data={"text": "Free until 14 days before."}, follow_redirects=True)
    assert response.request.path == "/admin/questions"
    assert "The answer has been sent." in response.data.decode()
    stored = repos.questions.get(question.id)
    assert stored.answer_text == "Free until 14 days before."
    assert stored.answered_by == admin.id and stored.answered_at is not None


def test_answer_from_order_page_returns_there(admin_client, repos, customer, order):
    question = repos.questions.add(Question(order.id, customer.id, "Cancellation terms?"))
    page = admin_client.get(f"/admin/orders/{order.id}").data.decode()
    assert "Cancellation terms?" in page
    assert 'name="from_order" value="1"' in page
    response = admin_client.post(f"/admin/questions/{question.id}/answer",
                                 data={"text": "Free.", "from_order": "1"})
    assert response.headers["Location"] == f"/admin/orders/{order.id}#questions"


def test_empty_answer_not_stored(admin_client, repos, customer, order):
    # US-20 AC3
    question = repos.questions.add(Question(order.id, customer.id, "Cancellation terms?"))
    page = admin_client.post(f"/admin/questions/{question.id}/answer", data={"text": "  "},
                             follow_redirects=True).data.decode()
    assert "Answer not saved. Write your answer first." in page
    assert not repos.questions.get(question.id).is_answered


def test_already_answered_not_changed(admin_client, repos, admin, customer, order):
    question = repos.questions.add(Question(order.id, customer.id, "Cancellation terms?"))
    repos.questions.answer(question.id, "First answer.", admin.id)
    page = admin_client.post(f"/admin/questions/{question.id}/answer", data={"text": "Second"},
                             follow_redirects=True).data.decode()
    assert "already been answered" in page
    assert repos.questions.get(question.id).answer_text == "First answer."


def test_unknown_question_is_404(admin_client, repos):
    assert admin_client.post("/admin/questions/999/answer", data={"text": "Hi"}).status_code == 404


def test_customer_cannot_answer(client, repos, customer, order):
    question = repos.questions.add(Question(order.id, customer.id, "Cancellation terms?"))
    log_in(client, "kunde@example.com", PASSWORD)
    assert client.post(f"/admin/questions/{question.id}/answer", data={"text": "Me"}).status_code == 403
    assert not repos.questions.get(question.id).is_answered


def test_empty_list(admin_client, repos):
    assert "No questions yet." in admin_client.get("/admin/questions").data.decode()


def test_dashboard_counts_unanswered(admin_client, repos, admin, customer, order):
    repos.questions.add(Question(order.id, customer.id, "One"))
    answered = repos.questions.add(Question(order.id, customer.id, "Two"))
    repos.questions.answer(answered.id, "Yes.", admin.id)
    page = admin_client.get("/admin/").data.decode()
    assert "1 unanswered question<" in page


def test_question_answer_round_trip(client, repos, customer, admin, order):
    # 01-plan §8 phase 8 acceptance: customer asks → admin answers → customer reads
    log_in(client, "kunde@example.com", PASSWORD)
    client.post(f"/account/orders/{order.id}/questions", data={"text": "Can we pick up ourselves?"})
    client.post("/account/logout")

    log_in(client, "admin@example.com", PASSWORD)
    page = client.get("/admin/questions").data.decode()
    question_id = int(re.search(r'/admin/questions/(\d+)/answer', page).group(1))
    assert "Can we pick up ourselves?" in page
    client.post(f"/admin/questions/{question_id}/answer", data={"text": "Yes, from Bryggen 1."})
    client.post("/account/logout")

    log_in(client, "kunde@example.com", PASSWORD)
    page = client.get(f"/account/orders/{order.id}").data.decode()
    assert "Can we pick up ourselves?" in page and "Yes, from Bryggen 1." in page
    assert "Waiting for an answer" not in page


def test_seeded_questions(admin_client, repos):
    from app.models.seed import seed
    seed(repos)
    page = admin_client.get("/admin/questions").data.decode()
    unanswered = sum(not q.is_answered for q in repos.questions.list_all())
    assert page.count('class="form answer-form"') == unanswered
