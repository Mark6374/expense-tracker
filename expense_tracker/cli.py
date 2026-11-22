import argparse

from . import storage
from .exporters import EXPORTERS
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
    out = EXPORTERS[args.format].expenses(storage.load(args.file))
    if args.output:
        with open(args.output, "w") as f:
            f.write(out)
    else:
        print(out)


def summarize(expenses):
    by_cat = {}
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, 0) + e.amount
    return by_cat


def cmd_summary(args):
    print(EXPORTERS[args.format].summary(summarize(storage.load(args.file))))


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
    e.add_argument("--format", default="csv", choices=sorted(EXPORTERS))
    e.add_argument("--output")
    e.set_defaults(func=cmd_export)

    s = sub.add_parser("summary")
    s.add_argument("--format", default="md", choices=sorted(EXPORTERS))
    s.set_defaults(func=cmd_summary)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
