"""Output formats (Strategy pattern).

Each format is one class implementing the ``Exporter`` protocol. The CLI looks the
format up in ``EXPORTERS`` instead of branching on the format name, so adding a new
format means adding one class and one registry entry — no edits to ``cli.py``.
"""
from __future__ import annotations

import csv
import io
import json
from decimal import Decimal
from typing import Protocol

from .models import Expense


class Exporter(Protocol):
    def expenses(self, items: list[Expense]) -> str: ...

    def summary(self, totals: dict[str, Decimal]) -> str: ...


# Cells starting with these characters are interpreted as formulas by Excel /
# LibreOffice / Google Sheets (CSV injection, OWASP). Prefixing "'" forces text.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_cell(value: str) -> str:
    return "'" + value if value.startswith(_FORMULA_PREFIXES) else value


def _csv(rows: list[list[str]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")  # quotes , " and newlines
    writer.writerows(rows)
    return buf.getvalue().rstrip("\n")


class CsvExporter:
    def expenses(self, items: list[Expense]) -> str:
        rows = [["date", "category", "description", "amount"]]
        rows += [[e.date, _safe_cell(e.category), _safe_cell(e.description), str(e.amount)] for e in items]
        return _csv(rows)

    def summary(self, totals: dict[str, Decimal]) -> str:
        return _csv([["category", "total"]] + [[_safe_cell(c), str(t)] for c, t in totals.items()])


class JsonExporter:
    def expenses(self, items: list[Expense]) -> str:
        return json.dumps([e.to_dict() for e in items], indent=2)

    def summary(self, totals: dict[str, Decimal]) -> str:
        return json.dumps({c: str(t) for c, t in totals.items()}, indent=2)


def _md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


class MarkdownExporter:
    def expenses(self, items: list[Expense]) -> str:
        lines = ["| date | category | description | amount |", "|---|---|---|---|"]
        lines += [
            f"| {e.date} | {_md_cell(e.category)} | {_md_cell(e.description)} | {e.amount} |"
            for e in items
        ]
        return "\n".join(lines)

    def summary(self, totals: dict[str, Decimal]) -> str:
        lines = ["| category | total |", "|---|---|"]
        lines += [f"| {_md_cell(c)} | {t} |" for c, t in totals.items()]
        return "\n".join(lines)


EXPORTERS: dict[str, Exporter] = {
    "csv": CsvExporter(),
    "json": JsonExporter(),
    "md": MarkdownExporter(),
}
