"""M2 — safe CSV/Markdown export: quoting + formula-injection neutralisation (risk R3)."""
import csv
import io
from decimal import Decimal

import pytest

from expense_tracker.exporters import EXPORTERS
from expense_tracker.models import Expense


def rows(text):
    return list(csv.reader(io.StringIO(text)))


def exp(description, category="food"):
    return Expense("2026-11-01", category, description, Decimal("10.00"))


def test_csv_comma_and_quotes_keep_four_columns():
    out = EXPORTERS["csv"].expenses([exp('lunch, "big" one')])
    parsed = rows(out)
    assert [len(r) for r in parsed] == [4, 4]
    assert parsed[1][2] == 'lunch, "big" one'


def test_csv_newline_in_description_stays_one_record():
    parsed = rows(EXPORTERS["csv"].expenses([exp("line1\nline2")]))
    assert len(parsed) == 2


@pytest.mark.parametrize("payload", ['=HYPERLINK("http://evil.example","x")', "+1+1", "-2+3", "@SUM(A1)", "\t=1", "\r=1"])
def test_csv_formula_injection_neutralised(payload):
    parsed = rows(EXPORTERS["csv"].expenses([exp(payload)]))
    cell = parsed[1][2]
    assert cell.startswith("'")
    assert cell[1:] == payload


def test_csv_category_is_sanitised_too():
    parsed = rows(EXPORTERS["csv"].summary({"=cmd": Decimal("1.00")}))
    assert parsed[1][0] == "'=cmd"


def test_csv_plain_text_unchanged():
    assert rows(EXPORTERS["csv"].expenses([exp("lunch")]))[1] == ["2026-11-01", "food", "lunch", "10.00"]


def test_markdown_pipe_and_newline_do_not_break_table():
    out = EXPORTERS["md"].expenses([exp("a|b\nc")])
    row = out.splitlines()[2]
    assert row == "| 2026-11-01 | food | a\\|b c | 10.00 |"
