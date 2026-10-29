"""Customer questions on own orders (OB4 C5; US-18, US-19)."""
import pytest

from app.models.entities import Question, User
from app.models.security import hash_password
from tests.factories import PASSWORD, log_in, make_order


@pytest.fixture
def order(repos, soup, customer):
    return repos.orders.add(make_order(customer.id, soup))


@pytest.fixture
def customer_client(client, customer):
    log_in(client, "kunde@example.com", PASSWORD)
    return client


def ask(client, order_id, text):
    return client.post(f"/account/orders/{order_id}/questions", data={"text": text}, follow_redirects=True)


def test_order_page_has_question_form(customer_client, order):
    page = customer_client.get(f"/account/orders/{order.id}").data.decode()
    assert f'action="/account/orders/{order.id}/questions"' in page
    assert '<label for="text">Your question</label>' in page
    assert "No questions yet." in page


def test_ask_question_shown_with_time_and_waiting(customer_client, repos, order):
    # US-18 AC1, US-19 AC2
    response = ask(customer_client, order.id, "Can we pick up the food ourselves?")
    page = response.data.decode()
    assert response.request.path == f"/account/orders/{order.id}"
    assert "Your question has been sent." in page
    assert "Can we pick up the food ourselves?" in page
    assert "Question asked " in page
    assert "Waiting for an answer" in page
    [question] = repos.questions.list_for_order(order.id)
    assert question.text == "Can we pick up the food ourselves?"


def test_empty_question_rejected(customer_client, repos, order):
    # US-18 AC2
    response = ask(customer_client, order.id, "   ")
    assert response.status_code == 200
    assert "Write your question first." in response.data.decode()
    assert repos.questions.list_for_order(order.id) == []


def test_too_long_question_rejected_and_text_kept(customer_client, repos, order):
    text = "Lang " * 300
    page = ask(customer_client, order.id, text).data.decode()
    assert "at most 1000 characters" in page
    assert "Lang Lang" in page  # the customer does not lose what they wrote
    assert repos.questions.list_for_order(order.id) == []


def test_question_on_other_customers_order_refused(client, repos, order):
    # US-18 AC3
    repos.users.add(User("annen@example.com", hash_password(PASSWORD), "Annen Kunde"))
    log_in(client, "annen@example.com", PASSWORD)
    assert client.post(f"/account/orders/{order.id}/questions", data={"text": "Hi"}).status_code == 404
    assert client.post("/account/orders/999/questions", data={"text": "Hi"}).status_code == 404
    assert repos.questions.list_all() == []


def test_asking_needs_login(client, repos, order):
    response = client.post(f"/account/orders/{order.id}/questions", data={"text": "Hi"})
    assert "/account/login" in response.headers["Location"]
    assert repos.questions.list_all() == []


def test_answer_shown_under_question_with_date(customer_client, repos, admin, order, customer):
    # US-19 AC1
    question = repos.questions.add(Question(order.id, customer.id, "Cancellation terms?"))
    answered = repos.questions.answer(question.id, "Free until 14 days before.", admin.id)
    page = customer_client.get(f"/account/orders/{order.id}").data.decode()
    assert page.index("Cancellation terms?") < page.index("Free until 14 days before.")
    assert f"Answer from Ekte Mat, {answered.answered_at:%d.%m.%Y %H:%M}" in page
    assert "Waiting for an answer" not in page


def test_my_orders_shows_waiting_questions(customer_client, repos, order, customer):
    repos.questions.add(Question(order.id, customer.id, "First?"))
    repos.questions.add(Question(order.id, customer.id, "Second?"))
    assert "2 waiting for an answer" in customer_client.get("/account/orders").data.decode()


def test_question_text_is_escaped(customer_client, repos, order):
    page = ask(customer_client, order.id, "<script>alert(1)</script>").data.decode()
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_question_form_needs_csrf_token(app, repos, order, customer):
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = customer.id
    assert 'name="csrf_token"' in client.get(f"/account/orders/{order.id}").data.decode()
    assert client.post(f"/account/orders/{order.id}/questions", data={"text": "Hi"}).status_code == 400
