from __future__ import annotations

import json
import os
from pathlib import Path

from .models import Expense, ValidationError

PathLike = str | Path
DEFAULT_PATH = os.environ.get("EXPENSES_FILE", "expenses.json")


class StorageError(Exception):
    """Raised when the data file cannot be read."""


def load(path: PathLike = DEFAULT_PATH) -> list[Expense]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise StorageError(f"data file {path} is not valid JSON ({exc.msg}, line {exc.lineno})") from None
    if not isinstance(data, list):
        raise StorageError(f"data file {path} is not valid: expected a JSON list")
    try:
        return [Expense.from_dict(d) for d in data]
    except ValidationError as exc:
        raise StorageError(f"data file {path} is not valid: {exc}") from None


def save(expenses: list[Expense], path: PathLike = DEFAULT_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in expenses], f, indent=2)
