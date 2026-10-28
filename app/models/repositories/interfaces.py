"""Storage-agnostic repository interfaces.

Implementations take and return domain objects only (never rows, SQL or Cypher), so the
SQLite implementations can be replaced by Neo4j in Oblig 5 without touching controllers or views.
"""
from abc import ABC, abstractmethod


class UserRepository(ABC):
    @abstractmethod
    def add(self, user):
        """Store a new user and return it with id. Raises DuplicateEmail."""

    @abstractmethod
    def get(self, user_id):
        """Return the user or None."""

    @abstractmethod
    def get_by_email(self, email):
        """Return the user with this e-mail (case-insensitive) or None."""

    @abstractmethod
    def list_customers(self):
        """Return all users with role customer."""


class EventCategoryRepository(ABC):
    @abstractmethod
    def add(self, category):
        """Store a new category and return it with id."""

    @abstractmethod
    def list_all(self):
        """Return all categories sorted by sort_order, then name."""

    @abstractmethod
    def get_by_slug(self, slug):
        """Return the category or None."""


class FoodItemRepository(ABC):
    @abstractmethod
    def add(self, item):
        """Store a new food item (with categories, allergens, labels) and return it with id."""

    @abstractmethod
    def update(self, item):
        """Replace all stored fields of an existing item. Raises NotFound."""

    @abstractmethod
    def delete(self, item_id):
        """Delete the item. Raises NotFound."""

    @abstractmethod
    def get(self, item_id):
        """Return the item or None."""

    @abstractmethod
    def get_many(self, item_ids):
        """Return the existing items among item_ids."""

    @abstractmethod
    def list_all(self):
        """Return all items, published or not, sorted by name."""

    @abstractmethod
    def list_published_by_category(self):
        """Return [(EventCategory, [FoodItem, ...]), ...] for categories with published items (C1)."""

    @abstractmethod
    def is_used_in_orders(self, item_id):
        """Return True if any order line refers to the item."""


class OrderRepository(ABC):
    @abstractmethod
    def add(self, order):
        """Store order, lines and guest groups in one transaction; generate order_number."""

    @abstractmethod
    def get(self, order_id):
        """Return the order with lines and guest groups, or None."""

    @abstractmethod
    def list(self, status=None, date_from=None, date_to=None):
        """Return orders filtered by status and event-date range, sorted by event date (A3)."""

    @abstractmethod
    def list_for_customer(self, customer_id):
        """Return the customer's own orders, sorted by event date (C4)."""

    @abstractmethod
    def update_status(self, order_id, new_status):
        """Change the order status. Raises NotFound or InvalidStatusTransition."""

    @abstractmethod
    def update_payment_status(self, order_id, payment_status):
        """Set the payment status. Raises NotFound."""


class QuestionRepository(ABC):
    @abstractmethod
    def add(self, question):
        """Store a new question and return it with id."""

    @abstractmethod
    def list_for_order(self, order_id):
        """Return the order's questions, oldest first (C5)."""

    @abstractmethod
    def list_all(self):
        """Return all questions, unanswered first, then oldest first (A4)."""

    @abstractmethod
    def answer(self, question_id, text, admin_id):
        """Store the answer. Raises NotFound."""
