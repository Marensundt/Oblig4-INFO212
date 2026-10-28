import pytest

from app.models.entities import EventCategory
from app.models.errors import DataIntegrityError


def test_list_all_sorted(repos, categories):
    assert [c.slug for c in repos.categories.list_all()] == ["birthday", "wedding", "conference"]


def test_get_by_slug(repos, categories):
    assert repos.categories.get_by_slug("wedding") == categories["wedding"]
    assert repos.categories.get_by_slug("missing") is None


def test_duplicate_slug_refused(repos, categories):
    with pytest.raises(DataIntegrityError):
        repos.categories.add(EventCategory("wedding", "Wedding again"))
