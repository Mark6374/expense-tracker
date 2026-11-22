"""Output formats (Strategy pattern).

Each format is one class implementing the ``Exporter`` protocol. The CLI looks the
format up in ``EXPORTERS`` instead of branching on the format name, so adding a new
format means adding one class and one registry entry — no edits to ``cli.py``.
"""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Protocol

from .models import Expense


class Exporter(Protocol):
    def expenses(self, items: list[Expense]) -> str: ...

    def summary(self, totals: dict[str, Decimal]) -> str: ...


class CsvExporter:
    def expenses(self, items: list[Expense]) -> str:
        lines = ["date,category,description,amount"]
        lines += [f"{e.date},{e.category},{e.description},{e.amount}" for e in items]
        return "\n".join(lines)

    def summary(self, totals: dict[str, Decimal]) -> str:
        return "\n".join(["category,total"] + [f"{c},{t}" for c, t in totals.items()])


class JsonExporter:
    def expenses(self, items: list[Expense]) -> str:
        return json.dumps([e.to_dict() for e in items], indent=2)

    def summary(self, totals: dict[str, Decimal]) -> str:
        return json.dumps({c: str(t) for c, t in totals.items()}, indent=2)


class MarkdownExporter:
    def expenses(self, items: list[Expense]) -> str:
        lines = ["| date | category | description | amount |", "|---|---|---|---|"]
        lines += [f"| {e.date} | {e.category} | {e.description} | {e.amount} |" for e in items]
        return "\n".join(lines)

    def summary(self, totals: dict[str, Decimal]) -> str:
        lines = ["| category | total |", "|---|---|"]
        lines += [f"| {c} | {t} |" for c, t in totals.items()]
        return "\n".join(lines)


EXPORTERS: dict[str, Exporter] = {
    "csv": CsvExporter(),
    "json": JsonExporter(),
    "md": MarkdownExporter(),
}
