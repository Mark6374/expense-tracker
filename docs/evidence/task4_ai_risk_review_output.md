# Task 4 — AI sub-agent output (verbatim, unverified at time of receipt)

> Raw model output. Classification (confirmed / plausible / unsupported) was done afterwards
> by human-directed verification — see `task4_verification.txt` and `docs/REPORT.md` §4.

I read every file you listed, plus CLAUDE.md (its only content is `@AGENTS.md`), expense_tracker.egg-info/SOURCES.txt and .pytest_cache/v/cache/lastfailed (which contains `{}`). I ran nothing beyond reading files. Every "confirm" step below is a command or check a human would run. Paths are relative to the repository root.

1. Money is stored and added as binary float
   Category: correctness
   Cause → event → consequence: amounts are parsed with `float()` and added up in float → the user records amounts like 0.10 + 0.20 → totals print as `0.30000000000000004` and accumulate rounding error. This also contradicts AGENTS.md §5, which says "Money is `decimal.Decimal`, never `float`".
   Where:
   - expense_tracker/models.py:9 `amount: float` and :16 `float(d["amount"])`
   - expense_tracker/cli.py:9-13 `total()` (`t = 0.0; t += e.amount`), :18 `float(args.amount)`, :44 `summarize()`
   - Exporters print the raw float repr (exporters.py:24, 28, 42, 47), e.g. `5.0`
   - tests/test_cli_output.py:36-37 and :62-63 lock in the `5.0` / `20.0` float formatting, so moving to Decimal will break these characterisation tests.
   Confirm: `.venv/bin/python -m expense_tracker --file /tmp/s.json add 2026-11-01 a x 0.1 && .venv/bin/python -m expense_tracker --file /tmp/s.json add 2026-11-01 a y 0.2 && .venv/bin/python -m expense_tracker --file /tmp/s.json total` should print `Total: 0.30000000000000004`.
   Confidence: high

2. No input validation; user errors end in raw tracebacks
   Category: correctness
   Cause → event → consequence: no validation or exception handling in the CLI → the user types a bad amount, a bad date or a hand-edited data file → they get a Python traceback instead of a clear stderr message (violates AGENTS.md §5, "never a traceback"), or bad data is silently saved.
   Where:
   - cli.py:18 `float(args.amount)` raises ValueError on input like "12,50"
   - It also accepts "nan", "inf" and negative amounts; a NaN total then spreads into every total
   - cli.py:58 the date is any string, never checked as ISO
   - storage.py:13 `json.load` raises JSONDecodeError on a corrupt file
   - models.py:16 `from_dict` raises KeyError on a missing field
   - cli.py:80 `args.func(args)` has no try/except
   - No test covers any of these error paths.
   Confirm: `.venv/bin/python -m expense_tracker --file /tmp/s.json add 2026-11-01 food x abc` (expect a ValueError traceback). `... add not-a-date food x nan` then `... total` (expect `Total: nan`).
   Confidence: high

3. Save is not atomic, so the data file can be truncated or corrupted
   Category: correctness (data integrity)
   Cause → event → consequence: `save()` opens the real file with mode "w", which empties it first, then streams JSON into it → a crash, Ctrl-C, full disk, a serialisation error midway, or two CLI runs at once → `expenses.json` ends up empty or half-written (or one run's added expense is lost). The next `load()` then raises JSONDecodeError and all history is unreadable. There is no backup, no temp-file-plus-`os.replace`, and no locking.
   Where: expense_tracker/storage.py:17-19 `save()`; read-modify-write in cli.py:16-19 `cmd_add`.
   Confirm: code inspection of storage.py:18 `with open(path, "w") as f: json.dump(...)`. A human could run two `add` commands in parallel in a loop on a scratch file and count the entries afterwards.
   Confidence: medium (the cause is certain; how often it happens is low for a single-user CLI)

4. CSV and Markdown exports are not escaped, allowing broken columns and spreadsheet formula injection
   Category: security / correctness
   Cause → event → consequence: fields are joined with f-strings, with no `csv` module and no quoting → a description or category containing `,`, `"`, a newline or `|`, or starting with `=`, `+`, `-` or `@` → the CSV has shifted columns or extra rows, the Markdown table breaks, and when the CSV is opened in Excel or LibreOffice, `=HYPERLINK(...)`-style payloads run as formulas.
   Where: expense_tracker/exporters.py:24 `CsvExporter.expenses`, :28 `CsvExporter.summary`, :42 and :47 in `MarkdownExporter`. JSON (:33) is safe. No test uses special characters.
   Confirm: `... --file /tmp/s.json add 2026-11-01 food "lunch, with tip" 10` then `... export --format csv` (the row has 5 fields under a 4-column header). Repeat with the description `=1+1` or `a|b` and `--format md`.
   Confidence: high (malformed output); medium (how much the injection matters for a personal tool)

5. `export --output` overwrites any path without checks, including the data file itself
   Category: security / correctness
   Cause → event → consequence: `open(args.output, "w")` takes any path, with no existence check, no confirmation and no rejection of the data path → a typo, or `--output expenses.json` → an arbitrary file is overwritten, or the JSON store is replaced by CSV or Markdown. Every later command then fails with JSONDecodeError, which compounds risk 3. For an AI agent running the CLI, this is a file-write path outside `--file`.
   Where: expense_tracker/cli.py:32-38 `cmd_export` (line 35).
   Confirm: `... --file /tmp/s.json export --format csv --output /tmp/s.json && ... --file /tmp/s.json list` (expect a JSONDecodeError traceback).
   Confidence: high

6. Unpinned dev and build dependencies
   Category: dependency
   Cause → event → consequence: requirements-dev.txt lists `pytest`, `ruff` and `mypy` with no versions, there is no lock file or hashes, and pyproject.toml:2 has an open-ended `setuptools>=61` → a fresh `pip install` pulls new major versions. Results:
   - New ruff rules or mypy strictness can make the mandatory review gate (AGENTS.md §4/§8) fail, or change, with no code change.
   - Results can't be reproduced between machines or the recorded evidence.
   - A compromised upstream release would be installed silently.
   .ruff_cache/0.17.6 shows one specific version was used locally, but it is not recorded anywhere.
   Where: requirements-dev.txt:1-3; pyproject.toml:2.
   Confirm: `cat requirements-dev.txt`; `.venv/bin/pip freeze`, compared with a fresh venv install a few weeks later; `ls .ruff_cache`.
   Confidence: high (the cause); medium (that it breaks something soon)

7. The type-check gate gives false confidence because most code is untyped
   Category: maintainability
   Cause → event → consequence: all of cli.py, storage.py and `Expense.to_dict`/`from_dict` lack annotations, and mypy is run with default settings (no `check_untyped_defs`, no `disallow_untyped_defs`, and no `[tool.mypy]` in pyproject.toml) → mypy skips the bodies of unannotated functions → `.venv/bin/mypy expense_tracker` reports success while type errors in cli/storage go unchecked.
   Other drift from AGENTS.md:
   - §5 requires "type hints on all public functions"
   - §2 says "one test file per module", but tests/ has only test_basic.py and test_cli_output.py
   - expense_tracker.egg-info/SOURCES.txt is stale: it lacks exporters.py and test_cli_output.py, which shows the editable-install metadata predates the refactor.
   Smaller point: `__main__.py:3` calls `main()` with no `if __name__` guard, so importing `expense_tracker.__main__` runs the CLI.
   Where: cli.py:8, 16, 23, 28, 32, 41, 48, 52; storage.py:9, 17; models.py:11, 15; pyproject.toml (no mypy section).
   Confirm: `.venv/bin/mypy --disallow-untyped-defs expense_tracker` (expect many errors), compared with a plain `mypy expense_tracker` (expect clean). Running `grep -n "def " expense_tracker/*.py` shows the missing annotations.
   Confidence: high

8. Agent operations: protecting real data and following the rules rely only on written instructions
   Category: agent operations
   Cause → event → consequence:
   - (a) The data path defaults to `expenses.json` in the current directory, with nothing technically stopping a CLI run without `--file` → an agent (or a test that calls `main()` without `--file`) reads, prints or overwrites the user's real `expenses.json`. That is real personal data, which AGENTS.md §4/§7 forbid touching. The only protection is the prose "Always pass `--file`".
   - (b) `DEFAULT_PATH` is read from `EXPENSES_FILE` once, at import time, and bound as a default argument → setting the env var after import, or monkeypatching it in a test, is silently ignored. Data then lands in the cwd file.
   - (c) AGENTS.md conflicts with the code: §5 requires Decimal and no tracebacks, which the code doesn't do. An agent asked to "follow AGENTS.md" may therefore make an unrequested data-format change (Decimal serialisation changes the JSON format and the locked test output), which §8.4 says needs human approval. AGENTS.md §6 also requires the acceptance criteria in docs/REPORT.md §1.3 to stay green, but they are not encoded as executable tests (not verified; docs/ was excluded).
   - (d) The review gates (§8) and the forbidden-action list (§7) are not enforced: no pre-commit hook, no CI config and no permission settings are present in the repo. The environment also reports the folder as "not a git repository" even though a .git directory exists, so the git-based gates and tags (`baseline`, `final`) referenced in §7 may not work as described.
   Where: storage.py:6, 9, 17; cli.py:54; AGENTS.md:37-41, 45, 47, 53, 65-69; tests/test_basic.py and tests/test_cli_output.py (correct only because each test passes a path explicitly).
   Confirm: `grep -n DEFAULT_PATH expense_tracker/*.py`; `ls -a .claude .github .pre-commit-config.yaml 2>/dev/null` (expect nothing); `git -C <repo> status` and `git tag` to check the repo and tag state. In a scratch directory, `cd /tmp/x && python -m expense_tracker add ...` creates `/tmp/x/expenses.json`.
   Confidence: medium for (a) and (b) (the mechanism is certain, whether it happens depends on agent behaviour); medium for (c); low-to-medium for the git/tag part of (d).
