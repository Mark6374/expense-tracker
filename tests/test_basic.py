from expense_tracker import storage
from expense_tracker.cli import total
from expense_tracker.models import Expense


def test_add_and_load(tmp_path):
    path = tmp_path / "e.json"
    storage.save([Expense("2026-11-01", "food", "lunch", 12.5)], path)
    loaded = storage.load(path)
    assert loaded[0].description == "lunch"
    assert loaded[0].amount == 12.5


def test_total_by_category():
    items = [
        Expense("2026-11-01", "food", "lunch", 10),
        Expense("2026-11-02", "taxi", "ride", 5),
        Expense("2026-11-03", "food", "dinner", 20),
    ]
    assert total(items) == 35
    assert total(items, "food") == 30
