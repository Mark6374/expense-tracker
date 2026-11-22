"""M1 — money as Decimal + input validation + clear errors (risks R1/R2)."""
import json
from decimal import Decimal

import pytest

from expense_tracker import storage
from expense_tracker.cli import main, total
from expense_tracker.models import Expense


def run(argv, capsys):
    try:
        main(argv)
        code = 0
    except SystemExit as exc:
        code = exc.code
    out = capsys.readouterr()
    return code, out.out, out.err


def test_total_is_exact_to_the_cent(tmp_path, capsys):
    f = str(tmp_path / "e.json")
    run(["--file", f, "add", "2026-11-01", "a", "x", "0.1"], capsys)
    run(["--file", f, "add", "2026-11-01", "a", "y", "0.2"], capsys)
    _, out, _ = run(["--file", f, "total"], capsys)
    assert out.strip() == "Total: 0.30"


def test_total_function_returns_decimal():
    items = [Expense("2026-11-01", "a", "x", Decimal("0.10")),
             Expense("2026-11-01", "a", "y", Decimal("0.20"))]
    assert total(items) == Decimal("0.30")


@pytest.mark.parametrize("amount", ["abc", "-50", "0", "nan", "inf", "1.234", "12,50"])
def test_invalid_amount_rejected_without_traceback(tmp_path, capsys, amount):
    f = tmp_path / "e.json"
    code, _, err = run(["--file", str(f), "add", "2026-11-01", "food", "x", amount], capsys)
    assert code == 1
    assert err.startswith("error:")
    assert "Traceback" not in err
    assert not f.exists()  # nothing was saved


@pytest.mark.parametrize("date", ["2026-13-45", "yesterday", ""])
def test_invalid_date_rejected(tmp_path, capsys, date):
    code, _, err = run(["--file", str(tmp_path / "e.json"), "add", date, "food", "x", "5"], capsys)
    assert code == 1
    assert "date" in err


def test_corrupt_data_file_gives_clear_error(tmp_path, capsys):
    f = tmp_path / "e.json"
    f.write_text("{not json")
    code, _, err = run(["--file", str(f), "list"], capsys)
    assert code == 1
    assert err.startswith("error:") and "not valid" in err


def test_record_with_missing_field_gives_clear_error(tmp_path, capsys):
    f = tmp_path / "e.json"
    f.write_text('[{"date": "2026-11-01", "category": "a"}]')
    code, _, err = run(["--file", str(f), "list"], capsys)
    assert code == 1
    assert err.startswith("error:")


def test_amount_round_trips_exactly(tmp_path):
    f = tmp_path / "e.json"
    storage.save([Expense("2026-11-01", "a", "x", Decimal("0.10"))], f)
    assert json.loads(f.read_text())[0]["amount"] == "0.10"
    assert storage.load(f)[0].amount == Decimal("0.10")


def test_legacy_float_amounts_still_load(tmp_path):
    f = tmp_path / "e.json"
    f.write_text('[{"date": "2026-11-01", "category": "a", "description": "x", "amount": 12.5}]')
    assert storage.load(f)[0].amount == Decimal("12.50")
