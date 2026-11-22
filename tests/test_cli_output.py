"""Characterisation tests: lock the current output of export/summary
so the Strategy refactoring (Task 3) can be shown to preserve behaviour."""
import json

import pytest

from expense_tracker import storage
from expense_tracker.cli import main
from expense_tracker.models import Expense


@pytest.fixture
def data_file(tmp_path):
    path = tmp_path / "e.json"
    storage.save(
        [
            Expense("2026-11-01", "food", "lunch", 12.5),
            Expense("2026-11-02", "taxi", "ride", 5),
            Expense("2026-11-03", "food", "dinner", 20),
        ],
        path,
    )
    return str(path)


def run(capsys, *argv):
    main(list(argv))
    return capsys.readouterr().out


def test_export_csv(capsys, data_file):
    out = run(capsys, "--file", data_file, "export", "--format", "csv")
    assert out.splitlines() == [
        "date,category,description,amount",
        "2026-11-01,food,lunch,12.5",
        "2026-11-02,taxi,ride,5.0",
        "2026-11-03,food,dinner,20.0",
    ]


def test_export_json(capsys, data_file):
    out = run(capsys, "--file", data_file, "export", "--format", "json")
    assert [e["description"] for e in json.loads(out)] == ["lunch", "ride", "dinner"]


def test_export_md(capsys, data_file):
    out = run(capsys, "--file", data_file, "export", "--format", "md")
    lines = out.splitlines()
    assert lines[0] == "| date | category | description | amount |"
    assert lines[2] == "| 2026-11-01 | food | lunch | 12.5 |"


def test_export_to_file(tmp_path, capsys, data_file):
    target = tmp_path / "out.md"
    run(capsys, "--file", data_file, "export", "--format", "md", "--output", str(target))
    assert target.read_text().startswith("| date |")


@pytest.mark.parametrize(
    "fmt,expected",
    [
        ("csv", ["category,total", "food,32.5", "taxi,5.0"]),
        ("md", ["| category | total |", "|---|---|", "| food | 32.5 |", "| taxi | 5.0 |"]),
    ],
)
def test_summary(capsys, data_file, fmt, expected):
    assert run(capsys, "--file", data_file, "summary", "--format", fmt).splitlines() == expected


def test_summary_json(capsys, data_file):
    out = run(capsys, "--file", data_file, "summary", "--format", "json")
    assert json.loads(out) == {"food": 32.5, "taxi": 5.0}


def test_unknown_format_exits_nonzero(capsys, data_file):
    with pytest.raises(SystemExit) as exc:
        main(["--file", data_file, "export", "--format", "xml"])
    assert exc.value.code != 0
