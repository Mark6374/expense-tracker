from __future__ import annotations

import argparse
import sys
from decimal import Decimal

from . import storage
from .exporters import EXPORTERS
from .models import Expense, ValidationError


def total(expenses: list[Expense], category: str | None = None) -> Decimal:
    return sum(
        (e.amount for e in expenses if category is None or e.category == category),
        Decimal("0.00"),
    )


def summarize(expenses: list[Expense]) -> dict[str, Decimal]:
    by_cat: dict[str, Decimal] = {}
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, Decimal("0.00")) + e.amount
    return by_cat


def cmd_add(args: argparse.Namespace) -> None:
    new = Expense(args.date, args.category, args.description, args.amount)  # validates
    expenses = storage.load(args.file)
    expenses.append(new)
    storage.save(expenses, args.file)
    print("Added.")


def cmd_list(args: argparse.Namespace) -> None:
    for e in storage.load(args.file):
        print(f"{e.date}  {e.category:<12} {e.amount:>10}  {e.description}")


def cmd_total(args: argparse.Namespace) -> None:
    print(f"Total: {total(storage.load(args.file), args.category)}")


def cmd_export(args: argparse.Namespace) -> None:
    out = EXPORTERS[args.format].expenses(storage.load(args.file))
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as f:
            f.write(out)
    else:
        print(out)


def cmd_summary(args: argparse.Namespace) -> None:
    print(EXPORTERS[args.format].summary(summarize(storage.load(args.file))))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="expense-tracker")
    p.add_argument("--file", default=storage.DEFAULT_PATH)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("date", help="YYYY-MM-DD")
    a.add_argument("category")
    a.add_argument("description")
    a.add_argument("amount", help="positive number, max 2 decimals, e.g. 12.50")
    a.set_defaults(func=cmd_add)

    sub.add_parser("list").set_defaults(func=cmd_list)

    t = sub.add_parser("total")
    t.add_argument("--category")
    t.set_defaults(func=cmd_total)

    e = sub.add_parser("export")
    e.add_argument("--format", default="csv", choices=sorted(EXPORTERS))
    e.add_argument("--output")
    e.set_defaults(func=cmd_export)

    s = sub.add_parser("summary")
    s.add_argument("--format", default="md", choices=sorted(EXPORTERS))
    s.set_defaults(func=cmd_summary)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (ValidationError, storage.StorageError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
