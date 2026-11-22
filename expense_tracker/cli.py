import argparse
import json
import sys

from . import storage
from .models import Expense


def total(expenses, category=None):
    t = 0.0
    for e in expenses:
        if category is None or e.category == category:
            t += e.amount
    return t


def cmd_add(args):
    expenses = storage.load(args.file)
    expenses.append(Expense(args.date, args.category, args.description, float(args.amount)))
    storage.save(expenses, args.file)
    print("Added.")


def cmd_list(args):
    for e in storage.load(args.file):
        print(f"{e.date}  {e.category:<12} {e.amount:>10}  {e.description}")


def cmd_total(args):
    print(f"Total: {total(storage.load(args.file), args.category)}")


def cmd_export(args):
    expenses = storage.load(args.file)
    if args.format == "csv":
        lines = ["date,category,description,amount"]
        for e in expenses:
            lines.append(f"{e.date},{e.category},{e.description},{e.amount}")
        out = "\n".join(lines)
    elif args.format == "json":
        out = json.dumps([e.to_dict() for e in expenses], indent=2)
    elif args.format == "md":
        lines = ["| date | category | description | amount |", "|---|---|---|---|"]
        for e in expenses:
            lines.append(f"| {e.date} | {e.category} | {e.description} | {e.amount} |")
        out = "\n".join(lines)
    else:
        print("unknown format")
        sys.exit(1)
    if args.output:
        with open(args.output, "w") as f:
            f.write(out)
    else:
        print(out)


def cmd_summary(args):
    expenses = storage.load(args.file)
    by_cat = {}
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, 0) + e.amount
    if args.format == "csv":
        print("category,total")
        for c, t in by_cat.items():
            print(f"{c},{t}")
    elif args.format == "json":
        print(json.dumps(by_cat, indent=2))
    elif args.format == "md":
        print("| category | total |")
        print("|---|---|")
        for c, t in by_cat.items():
            print(f"| {c} | {t} |")
    else:
        print("unknown format")
        sys.exit(1)


def main(argv=None):
    p = argparse.ArgumentParser(prog="expense-tracker")
    p.add_argument("--file", default=storage.DEFAULT_PATH)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("date")
    a.add_argument("category")
    a.add_argument("description")
    a.add_argument("amount")
    a.set_defaults(func=cmd_add)

    sub.add_parser("list").set_defaults(func=cmd_list)

    t = sub.add_parser("total")
    t.add_argument("--category")
    t.set_defaults(func=cmd_total)

    e = sub.add_parser("export")
    e.add_argument("--format", default="csv")
    e.add_argument("--output")
    e.set_defaults(func=cmd_export)

    s = sub.add_parser("summary")
    s.add_argument("--format", default="md")
    s.set_defaults(func=cmd_summary)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
