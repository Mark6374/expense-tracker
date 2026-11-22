import json
import os

from .models import Expense

DEFAULT_PATH = os.environ.get("EXPENSES_FILE", "expenses.json")


def load(path=DEFAULT_PATH):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return [Expense.from_dict(d) for d in data]


def save(expenses, path=DEFAULT_PATH):
    with open(path, "w") as f:
        json.dump([e.to_dict() for e in expenses], f, indent=2)
