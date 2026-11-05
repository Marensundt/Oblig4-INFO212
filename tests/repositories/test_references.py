"""References to stored objects must exist (foreign keys in SQLite, checks in the Neo4j repositories)."""
from dataclasses import replace

import pytest

from app.models.entities import FoodItem, OrderLine, Question
from app.models.errors import DataIntegrityError
from tests.factories import make_order


def test_food_item_with_missing_category_refused(repos, categories):
    with pytest.raises(DataIntegrityError):
        repos.food_items.add(FoodItem("Soup", "", 100, 1, category_ids=[categories["wedding"].id, 999]))
    assert repos.food_items.list_all() == []


def test_order_for_missing_customer_refused(repos, soup):
    with pytest.raises(DataIntegrityError):
        repos.orders.add(make_order(999, soup))
    assert repos.orders.list() == []


def test_order_line_for_missing_food_item_refused(repos, soup, customer):
    order = make_order(customer.id, soup)
    order.lines.append(OrderLine("Ghost dish", 100, 1, food_item_id=999))
    with pytest.raises(DataIntegrityError):
        repos.orders.add(order)
    assert repos.orders.list() == []


def test_order_line_without_food_item_allowed(repos, soup, customer):
    order = replace(make_order(customer.id, soup), lines=[OrderLine("Custom dish", 100, 1)])
    assert repos.orders.add(order).lines[0].food_item_id is None


def test_question_about_missing_order_refused(repos, customer):
    with pytest.raises(DataIntegrityError):
        repos.questions.add(Question(999, customer.id, "Anyone there?"))
    assert repos.questions.list_all() == []


def test_answer_by_missing_user_refused(repos, soup, customer):
    order = repos.orders.add(make_order(customer.id, soup))
    question = repos.questions.add(Question(order.id, customer.id, "When?"))
    with pytest.raises(DataIntegrityError):
        repos.questions.answer(question.id, "Soon", 999)
    assert not repos.questions.get(question.id).is_answered
