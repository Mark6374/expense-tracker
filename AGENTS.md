# AGENTS.md — instructions for AI coding agents

This file is the single source of truth for any AI agent (Claude Code, Codex, Copilot, etc.)
working in this repository. `CLAUDE.md` only imports this file.

## 1. Purpose
`expense-tracker` is a small, local-only command-line tool that records personal expenses
in a JSON file and prints totals, summaries and exports (CSV / JSON / Markdown).
There is no server, no network access and no production deployment.

## 2. Architecture
| Path | Responsibility |
|---|---|
| `expense_tracker/cli.py` | argparse entry point; one `cmd_*` function per sub-command |
| `expense_tracker/models.py` | `Expense` dataclass and (de)serialisation |
| `expense_tracker/storage.py` | load/save the JSON data file |
| `expense_tracker/exporters.py` | output formats (Strategy registry) — add new formats here only |
| `expense_tracker/__main__.py` | enables `python -m expense_tracker` |
| `tests/` | pytest suite; one file per module |
| `docs/` | assignment report and captured command evidence |

Data flow: `cli` → `storage.load()` → list[`Expense`] → business function → `EXPORTERS[fmt]` / print → `storage.save()`.
Runtime code uses the Python standard library only.

## 3. Setup (macOS / Linux, Python ≥ 3.10)
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pip install -e .
```

## 4. Safe commands (allowed without asking)
```bash
.venv/bin/pytest -q                      # tests — must pass before any commit
.venv/bin/ruff check .                   # lint
.venv/bin/mypy expense_tracker           # type check
.venv/bin/python -m expense_tracker --file /tmp/<scratch>.json <cmd>   # manual runs on a scratch file
git status / git diff / git log          # read-only git
```
Always pass `--file` pointing to a temporary file when running the CLI manually —
never read or write the user's real `expenses.json`.

## 5. Coding conventions
- Python 3.10+, type hints on all public functions, `ruff` defaults (incl. import sorting).
- Money is `decimal.Decimal`, never `float`.
- Business logic must not print; only `cli.py` talks to stdout/stderr.
- User errors → clear message on stderr + non-zero exit code, never a traceback.
- Keep changes small and focused; one concern per commit, imperative commit message.

## 6. Test expectations
- Every bug fix or new behaviour comes with a pytest test that fails without the change.
- Use `tmp_path` for files; tests must not touch the working directory or the network.
- The acceptance criteria in `docs/REPORT.md` §1.3 must stay green.

## 7. Forbidden actions (never do these)
- Adding, printing, or committing secrets, tokens, credentials or real personal data.
- Any deployment, publishing (`twine upload`, `pip publish`), or pushing to a remote.
- Destructive commands: `rm -rf`, `git reset --hard`, `git push --force`, `git clean -fdx`,
  rewriting history, deleting tags (`baseline`, `final`), deleting `docs/evidence/`.
- Adding, removing or upgrading dependencies (in `pyproject.toml` or `requirements*.txt`)
  without an explicit human review.
- Network access from code or tests; disabling or skipping tests to make a run pass.
- Editing files outside this repository.

## 8. Review gates
1. Agent runs pytest + ruff + mypy and shows the real output (no summarised or invented results).
2. Agent presents the diff and a short change summary with risk notes.
3. A human reviews and approves the diff **before** it is committed/merged.
4. Dependency changes, data-format changes and anything in §7 require explicit human approval.
