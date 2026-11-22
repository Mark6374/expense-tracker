# Expense Tracker

A small command-line tool to record personal expenses in a local JSON file.
Standard library only at runtime; Python 3.10+.

## Setup

    python3 -m venv .venv
    .venv/bin/pip install -r requirements-dev.txt
    .venv/bin/pip install -e .

## Usage

    python -m expense_tracker add 2026-11-01 food "lunch" 12.50
    python -m expense_tracker list
    python -m expense_tracker total --category food
    python -m expense_tracker export --format csv --output out.csv
    python -m expense_tracker summary --format md

Data is stored in `expenses.json` in the current directory; override with
`--file PATH` or the `EXPENSES_FILE` environment variable.

## Checks

    .venv/bin/pytest -q
    .venv/bin/ruff check .
    .venv/bin/mypy

## For AI agents

See [AGENTS.md](AGENTS.md).
