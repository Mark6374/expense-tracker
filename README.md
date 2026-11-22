# Expense Tracker

A small command-line tool to record personal expenses in a local JSON file.

## Install

    pip install -r requirements.txt

## Usage

    python -m expense_tracker add 2026-11-01 food "lunch" 12.50
    python -m expense_tracker list
    python -m expense_tracker total --category food
    python -m expense_tracker export --format csv --output out.csv
    python -m expense_tracker report

## Tests

    pytest
