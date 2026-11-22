# Software Engineering. Assignment #05 Report

Topic: AI-assisted repository customization, agent readiness and software risk governance

- Repository: https://github.com/Mark6374/expense-tracker
- Baseline version: tag `baseline` (commit 6d994d2)
- Final version: tag `final` (commit e8c3766). Commits after it only add documentation and screenshots.
- All changes between the two versions: https://github.com/Mark6374/expense-tracker/compare/baseline...final
- Date: 22.11.2026, individual work

All command outputs in this report come from real runs. The full logs are saved in `docs/evidence/` (the list is in Appendix B). If something was not tested, I say so in section 7.4.

Note: I did not have a small project of my own that fit the assignment, so the starting project was created for this assignment. How it was made is described in Appendix A.

---

## 1. Task 1. Baseline and context

### 1.1 Repository map (baseline version)

The project is a small command-line expense tracker written in Python. It saves expenses to a JSON file and can show totals, a summary by category and export to CSV, JSON or Markdown.

| What | Details |
|---|---|
| Entry points | `python -m expense_tracker` (file `__main__.py`) and the console script `expense-tracker` from `pyproject.toml` |
| Modules | `cli.py`: argument parsing, commands add/list/total/export/summary and also all output formatting. `models.py`: the `Expense` dataclass. `storage.py`: reading and writing the JSON file (`--file`, `$EXPENSES_FILE` or `./expenses.json` by default) |
| Dependencies | Runtime: only the standard library. Dev: `pytest`, `ruff`, `mypy` in `requirements-dev.txt`, without versions. Build: `setuptools>=61` |
| Tests | `tests/test_basic.py` with 2 simple tests (save/load and total by category) |
| Build | `pyproject.toml` with setuptools, `python -m build` |
| Docs | Only `README.md`. No agent instructions and no CI |

After my changes the project also has `exporters.py`, three more test files (`test_cli_output.py`, `test_validation.py`, `test_exporters.py`), `AGENTS.md`, `CLAUDE.md` and the `docs/` folder.

### 1.2 Commands and results at baseline

Tool versions: Python 3.13.7, pytest 9.2.0, ruff 0.17.6, mypy 2.4.1, pip-audit 2.10.1, build 1.6.1. Logs: `baseline_checks.txt`, `baseline_smoke.txt`.

| Command | Result |
|---|---|
| `.venv/bin/pytest -q` | Failed with exit code 2: `ModuleNotFoundError: No module named 'expense_tracker'`. So the test command from the README does not work |
| `.venv/bin/python -m pytest -q` | 2 passed. It only works because `python -m` adds the current folder to the import path |
| `.venv/bin/ruff check .` | 1 error (I001, imports not sorted in `models.py`) |
| `.venv/bin/mypy --strict expense_tracker` | 22 errors in 4 files, because there are no type hints |
| `python -m build` | Built sdist and wheel, OK |
| `pip-audit -r requirements-dev.txt` | No known vulnerabilities |
| `python -m expense_tracker report` (from README) | `invalid choice: 'report'`. The README shows a command that does not exist |

### 1.3 Acceptance criteria

| ID | Criterion | Test | Baseline | Final |
|---|---|---|---|---|
| AC1 | An expense added with `add` shows up the same in `list` and stays after saving and loading | `test_add_and_load`, `test_amount_round_trips_exactly` | Pass | Pass |
| AC2 | Totals are exact to the cent (0.10 + 0.20 = 0.30) | `test_total_is_exact_to_the_cent`, `test_total_by_category` | Fail (`0.30000000000000004`) | Pass (`0.30`) |
| AC3 | `export` gives correct CSV / JSON / Markdown, one row per expense | `test_cli_output.py`, `test_exporters.py` | Partly (a comma in the description breaks the CSV) | Pass |
| AC4 | Wrong input or a broken data file gives an `error: ...` message, exit code 1, no traceback, nothing is saved | `test_validation.py` | Fail | Pass |
| AC5 | pytest, ruff, mypy (strict) and build all pass | `final_checks.txt` | Fail | Pass |

AC1 and AC3 (for normal data) already worked at baseline and had to keep working. AC2, AC4 and AC5 were the goals for my changes.

### 1.4 Weaknesses found at baseline

| # | Weakness | Evidence |
|---|---|---|
| W1 | Money is stored as `float`, so totals are wrong | `models.py:9 amount: float`; `total` printed `Total: 0.30000000000000004` |
| W2 | No input checks. A wrong date and a negative amount are saved, a wrong number crashes the program | `add 2026-13-45 food 'bad date' -50` printed `Added.`; `add ... abc` gave a `ValueError` traceback |
| W3 | A broken data file crashes every command | after `echo '{not json' > $D`, `list` gave a `JSONDecodeError` traceback |
| W4 | CSV export does not quote fields and does not protect against formulas | `coffee, large` became 5 columns; `=HYPERLINK(...)` was exported as is |
| W5 | Setup is not reproducible: `pytest` fails without installing the package, the README is wrong, dev tools have no versions | see 1.2 and `requirements-dev.txt` |
| W6 | No agent instructions, no CI, nothing checks the rules automatically | no `AGENTS.md`, `.github/` or pre-commit config |

### 1.5 Facts, assumptions and unverified suggestions

- Facts (I reproduced them with a command, see the logs): W1 to W6. One more thing I noticed: the second ruff run showed rules I001 and UP007 even though the project had no ruff config, but `ruff check --isolated` passed. So the lint result depended on a config outside the repository. I could not find where that config is, but the effect itself is reproducible.
- Assumptions (not tested): users open the CSV in Excel or a similar program, otherwise formula injection does not matter. A crash during `save()` would leave a broken file (clear from the code, but I did not reproduce it).
- AI suggestions that were not checked yet are kept separately in section 4. They only go to the risk register after a command confirms them.

---

## 2. Task 2. Agent instructions

I added `AGENTS.md` to the root of the repository. It has these parts:

1. Purpose of the project.
2. Architecture table and data flow.
3. Setup commands.
4. Safe commands that the agent can run without asking: pytest, ruff, mypy, running the CLI only with a temporary `--file`, and read-only git commands.
5. Coding rules: money as `Decimal`, no printing inside business logic, errors without tracebacks.
6. Test rules: every fix needs a test that fails without the fix; tests only use `tmp_path`.
7. Forbidden actions: secrets or real personal data, deploying, publishing or pushing, destructive commands (`rm -rf`, `git reset --hard`, `push --force`, rewriting history, deleting tags or evidence), changing dependencies without review, network access, skipping tests, editing files outside the repository.
8. Review gates: show real check output, then the diff with a short summary and risks, then wait for human approval before a commit. Dependency or data format changes need separate approval.

About loading the file: the agent I used reads `CLAUDE.md` automatically, not `AGENTS.md`. So `CLAUDE.md` has only one line, `@AGENTS.md`, which imports the main file. This way there is one source of rules. After this the agent loaded the rules by itself and I did not have to paste them. It also followed them: before committing M1/M2 (which change the data format) and before pinning dependencies, it stopped and asked for my approval, as section 8 says.

---

## 3. Task 3. Pattern decision

Problem: at baseline `cli.py` had the same `if args.format == "csv" / "json" / "md" / else` block twice, in `cmd_export` and in `cmd_summary` (6 comparisons in total). The formatting code was also mixed into the command handlers. To add a new format you had to change two places.

Options I looked at:

- No pattern, just a dict of functions. This would work, but every format has two operations (list of expenses and summary), and it is nicer to keep them together.
- Strategy (chosen): one small class per format with the methods `expenses()` and `summary()`, and a registry `EXPORTERS = {"csv": ..., "json": ..., "md": ...}`.
- Adapter: not needed, because there is no external interface to adapt.

Why I think the pattern is justified here: it removes real duplication, the list of valid formats now comes from one place (`choices=sorted(EXPORTERS)` in argparse), and a new format is just one new class. Later it was also the only place I had to change for M2. I did not add any other patterns.

| | Before (baseline) | After (commit 465ed5e) |
|---|---|---|
| Format checks in `cli.py` | 6 `args.format ==` in 2 functions | 0, uses `EXPORTERS[args.format]` |
| Size of `cli.py` | 110 lines | 84 lines (+55 lines in `exporters.py`) |
| Unknown format | prints `unknown format`, exit code 1 | argparse error with the list of formats, exit code 2 |

To prove the behaviour did not change, I first wrote 8 characterisation tests for the old code (`tests/test_cli_output.py`, commit b31fc42). After the refactoring all 10 tests still passed without changes (`task3_refactor_tests.txt`). The only difference is the exit code for an unknown format (1 became 2). It is still non-zero, and that is what the test checks.

---

## 4. Task 4. Read-only AI risk review

I asked a separate AI sub-agent to look for risks without changing any files (it only had read tools). The exact prompt is in `task4_ai_risk_review_prompt.txt` and its full answer is in `task4_ai_risk_review_output.md`. After the review, `git status` showed no changes. Then every claim was checked with commands on a temporary data file (`task4_verification.txt`).

| # | Claim | Category | Result | Evidence |
|---|---|---|---|---|
| 1 | Money is `float`, totals are wrong | correctness | Confirmed | `total` printed `0.30000000000000004` |
| 1b | Moving to Decimal will break the characterisation tests | maintainability | Confirmed | after M1, 5 tests in `test_cli_output.py` failed until I updated them |
| 2 | No validation: `abc` gives a traceback, `nan` gives `Total: nan`, negatives are accepted, a missing field gives `KeyError` | correctness | Confirmed | all 4 reproduced (exit codes 1 / 0 / 0 / 1) |
| 3 | `save()` is not atomic, a crash can break the file | correctness | Plausible, not verified | the cause is visible in `storage.py:18 open(path, "w")`, but I did not reproduce a crash |
| 4 | CSV/MD are not escaped: broken columns and formula injection | security | Confirmed | CSV row lengths `[4, 5, 4, 4]`; `=1+1` and `a\|b` exported as is |
| 5 | `export --output` can overwrite the data file | correctness / security | Confirmed | after `--output $D`, `list` gave `JSONDecodeError` |
| 6 | Dev and build dependencies have no fixed versions | dependency | Confirmed | `requirements-dev.txt` had no versions; `setuptools>=61` |
| 7 | Plain `mypy` passes, so it gives false confidence | maintainability | Confirmed | `mypy` said Success; with `--disallow-untyped-defs` there were 12 errors |
| 7b | `egg-info/SOURCES.txt` is out of date | maintainability | True, but not a real risk | it is build output, ignored by git and recreated on install |
| 7c | `__main__.py` has no `if __name__` check | maintainability | Not a risk | the file is only used with `python -m`, nothing imports it |
| 8a | Running without `--file` writes to `./expenses.json` (real data) | agent operations | Confirmed | running in an empty folder created `expenses.json` there |
| 8b | `EXPENSES_FILE` is read once at import | agent operations | Plausible, low | true in the code, but does not matter for separate CLI runs |
| 8d-1 | The rules are not enforced (no CI, hooks or permission settings) | agent operations | Confirmed | `.claude`, `.github` and `.pre-commit-config.yaml` do not exist |
| 8d-2 | "The folder is not a git repository", so tags may not work | agent operations | Unsupported | `git rev-parse --is-inside-work-tree` returned `true`, `git tag` showed `baseline`. The AI used old information about the environment |

In total: 14 claims in 4 categories. 10 confirmed (one of them is true but not a risk), 2 plausible and 2 unsupported.

---

## 5. Task 5. Risk register

Likelihood (L) and impact (I) are from 1 to 3, score = L × I. "Before" means the reviewed version (commit 465ed5e).

| ID | Category | Cause → event → consequence | Component | Evidence | L | I | Score | Mitigation | Owner | Verification | Residual risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R2 | correctness | No input checks → user types a wrong amount/date or the file is broken → traceback, or bad data (`nan`, negative, `2026-13-45`) is saved and spoils all totals | `models.py`, `cli.py`, `storage.py` | task4 F2, baseline smoke | 3 | 3 | 9 | M1 | Mark (maintainer) | `test_validation.py` (16 cases) | Low (1×2=2) |
| R1 | correctness | Money as float → decimal amounts are added → small rounding errors in totals | `models.py`, `cli.total` | `0.30000000000000004` | 3 | 2 | 6 | M1 (same code) | Mark | `test_total_is_exact_to_the_cent` | Very low (1×1=1) |
| R3 | security | CSV fields not quoted or protected → description starts with `=`, `+`, `-`, `@` or has a comma → Excel runs a formula (for example a link to a bad site) or columns move | `exporters.py` | row lengths `[4,5,4,4]`, raw `=HYPERLINK` | 2 | 3 | 6 | M2 | Mark | `test_exporters.py` (11 cases) | Low (1×2=2) |
| R4 | correctness / security | `--output` accepts any path → user or agent gives the data file path → the JSON file is replaced by CSV and the history is lost | `cli.cmd_export` | task4 F5 | 2 | 3 | 6 | Planned: do not allow `--output` equal to `--file`, ask before overwrite | Mark | new test (not done yet) | Open (2×3=6) |
| R8 | agent operations | Default data path is `./expenses.json` and the rules are only text → agent runs the CLI without `--file` or commits without review → real data is touched or an unreviewed change gets in | `storage.DEFAULT_PATH`, process | task4 F8a, F8d-1 | 2 | 2 | 4 | AGENTS.md sections 4, 7, 8 (done); planned: CI and agent permission settings | Mark | CI run, settings file | Open (2×2=4) |
| R6 | dependency | Dev tools without versions and lint rules from outside the repo → a new install gets new versions or rules → checks pass or fail for reasons not related to the code | `requirements-dev.txt`, `pyproject.toml` | 1.5, task4 F6 | 2 | 2 | 4 | Fixed versions, `[tool.ruff]` and `[tool.mypy]` in pyproject (commit 7e5b203) | Mark | install + checks in `final_checks.txt` | Low (1×2=2); `setuptools>=61` is still a range |
| R5 | correctness | `save()` not atomic → crash or two runs at the same time → broken file or lost expense | `storage.save` | only code (plausible) | 1 | 3 | 3 | Planned: write to a temp file and `os.replace`, keep a backup | Mark | test with a simulated crash (not done) | Open (1×3=3) |
| R7 | maintainability | Code without types and default mypy → type errors pass the check | all modules | task4 F7 | 3 | 1 | 3 | Type hints everywhere and `mypy --strict` in config | Mark | `mypy` → Success | Very low (1×1=1) |

Top two confirmed risks for fixing: R2 (score 9) and R3 (score 6). R1, R3 and R4 all have score 6. I chose R3 because it is the only security risk and it can harm other people too (exported files are often shared). R1 gets fixed anyway together with R2, because it is the same code. R4 stays open, has an owner and is one of the conditions in the release decision (section 9).

---

## 6. Task 6. Agent-readiness audit (final version)

| Area | Status | Evidence |
|---|---|---|
| Readable structure | OK. 4 small modules, each with one job; Strategy for formats | 1.1, 3 |
| README is correct | OK. Fixed the non-existing `report` command and the missing `requirements.txt` | commit dadd7d7, `final_smoke.txt` |
| Reproducible setup | OK. venv + pinned `requirements-dev.txt` + `pip install -e .`; `pytest` works directly (`pythonpath` in pyproject) | `final_checks.txt` |
| Pinned dependencies | Partly. Dev tools have exact versions, but the build backend is `setuptools>=61` and there are no hashes | `requirements-dev.txt`, `pyproject.toml` |
| Tests | OK. 37 tests: basic, characterisation, validation, export security | `final_tests_verbose.txt` |
| Lint / types | OK. ruff (E, F, I, UP) and `mypy --strict` pass; rules are in the repository | `final_checks.txt` |
| Build | OK. sdist and wheel | `final_checks.txt` |
| Logging | No logging. Errors go to stderr with clear messages, which I think is enough for a small CLI | `cli.main` |
| Security | OK: input validation, CSV injection protection, pip-audit clean. Not OK: R4 is still open | 5 |
| AGENTS.md (permissions, safe commands, forbidden actions, review gates) | OK, all parts are there, and it worked in practice (the agent stopped for approval) | 2 |
| Rules enforced automatically | No. No CI, no pre-commit hook, no agent permission settings | `ls .github .pre-commit-config.yaml .claude` |

Readiness level: 2 (Documented). The documentation, setup, safe and forbidden commands are all there and all checks pass in the final version. I do not give level 3 (Agent-ready) because of these missing things:

1. No CI that runs pytest, ruff, mypy and build on every change. The review gates exist only as text.
2. Nothing technically stops forbidden actions (no permission settings, no pre-commit hook).
3. Two open data risks that an agent working alone could trigger: R4 (overwrite with `--output`) and R8 (default data path in the current folder).
4. No dependency lock file with hashes.

---

## 7. Task 7. Mitigation and verification

### 7.1 Mitigation M1: R2 and R1 (commit a213efd)

What was changed:

- `models.py`: `parse_amount()` turns the amount into a positive `Decimal` with 2 decimal places. It rejects `nan`, `inf`, `0`, negatives, more than 2 decimals and `12,50`.
- `parse_date()` only accepts the `YYYY-MM-DD` format.
- Validation runs in `Expense.__post_init__`. In `from_dict` a missing field becomes a `ValidationError`.
- `storage.load()` turns broken JSON (or JSON that is not a list) into a `StorageError`.
- `cli.main()` catches both errors, prints `error: ...` and exits with code 1.
- `cmd_add` checks the input before loading or saving the file.
- Totals use `Decimal`.

Data format change (I approved it, as AGENTS.md section 8 requires): the amount is now saved as a string in JSON, for example `"12.50"`. Old files with numbers still load (`test_legacy_float_amounts_still_load`). The output always has 2 decimals now (`5.0` became `5.00`), so I updated the expected values in the characterisation tests in the same commit, on purpose.

How I reviewed the diff (`mitigations_M1_M2.diff`) before approving it: I checked that nothing is saved when the input is wrong (`assert not f.exists()`), that the old format still loads, and that the only changes in old tests were about number formatting.

Tests: the 16 new test cases were written first. 15 of them failed on the old code (`mitigation_tests_before.txt`). The one that passed, `test_legacy_float_amounts_still_load`, checks backward compatibility, so it should pass on both versions. After the change all of them pass.

### 7.2 Mitigation M2: R3 (commit f24d7e2)

What was changed: CSV is now written with `csv.writer`, which quotes commas, quotes and new lines. Text cells that start with `=`, `+`, `-`, `@`, tab or carriage return get a `'` in front (this is the usual protection against CSV injection, recommended by OWASP). In Markdown, `|` is escaped and new lines become spaces. Dates and amounts do not get the prefix, because they are validated and amounts are always positive.

How I reviewed the diff: the protection works for both description and category, and also for the summary export. Normal text is exported exactly like before (`test_csv_plain_text_unchanged` and the characterisation tests).

Tests: 11 new cases, 10 failed before the change and all pass after. `test_csv_plain_text_unchanged` passed before too, which is expected.

### 7.3 Extra fix (not counted as one of the two): R6 and R7 (commit 7e5b203)

I fixed the dev tool versions (`pytest==9.2.0`, `ruff==0.17.6`, `mypy==2.4.1`, `pip-audit==2.10.1`, `build==1.6.1`) and added `[tool.ruff]` (rules E, F, I, UP, line length 110) and `[tool.mypy] strict = true` to `pyproject.toml`. When the ruff rules were set in the project, ruff found 15 lines longer than 88 characters that the outside config had hidden. I fixed this by setting the line length to 110 and splitting one line.

### 7.4 Before and after

| Check | Baseline (6d994d2) | Final (7e5b203) |
|---|---|---|
| `pytest -q` | exit code 2, collection error, 0 tests ran | 37 passed, 0 failed |
| `ruff check .` | 1 error | All checks passed |
| `mypy` strict | 22 errors | Success, 6 files |
| `build` | OK | OK |
| `pip-audit` | no known vulnerabilities | no known vulnerabilities |
| 0.1 + 0.2 | `0.30000000000000004` | `0.30` |
| Wrong date or amount | saved, or traceback | `error: invalid date ...`, exit code 1 |
| CSV row lengths | `[4, 5, 4, 4]` | `[4, 4, 4, 4, 4]` |
| Broken data file | traceback | `error: data file ... is not valid JSON`, exit code 1 |

Logs: `baseline_checks.txt`, `baseline_smoke.txt`, `final_checks.txt`, `final_smoke.txt`, `final_tests_verbose.txt`.

Screenshots of the same runs are below. They were taken in the macOS Terminal on 22.11.2026 and are also saved in `docs/evidence/screenshots/`. The baseline was run from a copy of the `baseline` tag with its own clean virtual environment (same tool versions), so that the installed final code could not hide the baseline import error. `$D` is a temporary data file. The exit codes are real (`set -o pipefail`).

*Figure 1. Baseline checks: pytest fails to collect tests, ruff finds 1 error, mypy --strict finds 22 errors.*

![Baseline checks](evidence/screenshots/01_baseline_checks.png)

*Figure 2. Baseline problems: total 0.30000000000000004, wrong date and negative amount are saved, traceback on "abc", raw =HYPERLINK(...) and an unquoted comma in the CSV.*

![Baseline defects](evidence/screenshots/02_baseline_defects.png)

*Figure 3. Final checks: 37 tests passed, ruff and strict mypy pass.*

![Final checks](evidence/screenshots/03_final_checks.png)

*Figure 4. Final version, same steps: total 0.30, clear error messages with exit code 1, the formula gets a ' prefix, the field with a comma is quoted.*

![Final defects fixed](evidence/screenshots/04_final_defects_fixed.png)

What was not tested: there is no CI, so no CI run. No crash or concurrency test for R5. The CSV protection was checked on the CSV text, I did not open the file in Excel or LibreOffice. Tests were only run on macOS with Python 3.13 (not on 3.10 to 3.12 and not on Windows).

### 7.5 Risk scores after the changes

| ID | Before | After | Comment |
|---|---|---|---|
| R2 | 9 | 2 | Validation checks format and range, but not if the number makes sense (for example 1000 instead of 100) |
| R1 | 6 | 1 | |
| R3 | 6 | 2 | The `'` prefix is visible to the user, and other programs that read the CSV need to remove it |
| R6 | 4 | 2 | The build backend is still a range, no hashes |
| R7 | 3 | 1 | |
| R4 | 6 | 6 | Open, see section 9 |
| R8 | 4 | 4 | Open, partly covered by AGENTS.md |
| R5 | 3 | 3 | Open |

Trade-offs: M1 changes how amounts are saved in JSON. The new version reads old files, but an old version of the program cannot add up the new string amounts. M1 also rejects amounts like `12,50` that some people might type.

---

## 8. Task 8. Background agent safeguards (planned, not run)

Example task for a background agent: "Add a `--category CAT` option to `list` and `export`, with tests." I did not use a paid background agent, this is only the plan.

| Safeguard | Plan |
|---|---|
| Isolation | Separate git worktree `../expense-tracker-agent` on a new branch `agent/category-filter`, made from `final`. The agent does not touch `main`, the tags or my working copy. No network during the run (dependencies are installed in a fresh `.venv` before). |
| Allowed files | `expense_tracker/cli.py`, `expense_tracker/exporters.py`, `tests/test_*.py`, `README.md` (only the usage part). Changing any other file means the result is rejected. |
| Allowed commands | `.venv/bin/pytest -q`, `.venv/bin/ruff check .`, `.venv/bin/mypy`, `python -m build --outdir /tmp/...`, running the CLI with `--file /tmp/...`, and `git status/diff/add/commit` only on the agent branch |
| Forbidden | Everything from AGENTS.md section 7, and also: `git push`, merge, rebase, tag commands, changing `requirements*.txt` or `pyproject.toml`, deleting or skipping tests, touching `docs/evidence/`, reading the home folder or any `expenses.json` outside `/tmp` |
| Limits | 30 minutes, at most 3 fix-and-retest rounds, at most 300 changed lines. If a limit is reached, the agent stops and reports what it has. |
| What the agent must give back | 1) short summary of the change, 2) `git diff final...agent/category-filter`, 3) full pytest log with passed/failed numbers, 4) ruff and mypy output, 5) build result, 6) risk notes: new risks, effect on the data format (should be none), tests that were not written and why |
| Human review | I check everything, run the checks again myself, and only then merge. No automatic merge and no deployment. Changes to dependencies or the data format need separate approval (AGENTS.md section 8). |
| Failure and rollback | If checks fail or a rule is broken, the result is rejected and the worktree and branch are deleted (`git worktree remove`, `git branch -D agent/category-filter`). `main` stays the same. If a problem is found after merging, I use `git revert` (no history rewriting), add a test that shows the bug and add it to the risk register. My real data is safe because the agent only uses files in `/tmp`. |

---

## 9. Task 9. Release decision

Decision: CONDITIONAL (GO with conditions) for version 0.1.0, tag `final`.

Why not NO-GO:

- All main checks pass: 37/37 tests, ruff, strict mypy, build and pip-audit.
- All 5 acceptance criteria pass.
- The two biggest confirmed risks (R2 = 9, R3 = 6) are fixed, and there are tests that failed before the fix and pass after it (section 7).
- The main functions of the tool (adding expenses, totals, export) have no big gaps in testing.

Why not a full GO: some confirmed risks that can lose data are still open, and the readiness level is 2, not 3. For each open item there is a control and an owner:

| Open item | Score | What we do until it is fixed | Owner | When |
|---|---|---|---|---|
| R4: `--output` can overwrite the data file | 6 | Warning in the release notes; AGENTS.md does not allow agents to write outside `/tmp`; the fix (do not allow `--output` equal to `--file`) with a test is the first task for the next version | Mark | next version |
| R8: default data path, rules only in text | 4 | AGENTS.md sections 4, 7, 8; human approval before every commit (this worked during the assignment); add CI and agent permission settings | Mark | before using any background agent |
| R5: save is not atomic | 3 | It is a local tool for one user; users should keep a copy of `expenses.json`; atomic saving planned | Mark | next version |
| Not tested on Python 3.10 to 3.12 and on Windows | – | For this version only macOS with Python 3.13 is supported | Mark | when CI exists |

If R4 is not fixed before the next version, or if someone wants to use a background agent before CI and permission settings exist, then the decision for that version is NO-GO.

---

## 10. Task 10. AI reflection

For this assignment I used Claude Code (the VS Code extension) with the Claude Opus 5.5 model. It got the assignment PDF, the whole repository, and later the rules from `AGENTS.md`, which it loaded by itself through a one-line `CLAUDE.md`. For the risk review I used a separate read-only sub-agent with a prompt that did not allow file changes.

The most useful suggestion came from the risk review. It warned that changing money from `float` to `Decimal` would break the characterisation tests, because they expect numbers like `5.0`. Five tests did fail after M1, but because I expected it, I treated it as a planned format change and did not hide the failures.

The weakest suggestion was that the project "is not a git repository", so the baseline and final tags might not work. One command (`git rev-parse --is-inside-work-tree` returned `true`) showed that this was wrong. The model used old information about the environment instead of looking at the repository.

My own part was making the decisions and checking the results. I chose the project setup, read every diff before approving the commit, and only accepted a finding if there was a saved command output that confirmed it. The tests changed my decisions twice. Writing the M1 and M2 tests first showed that the bugs were real (25 failing tests). Setting the ruff rules in the project showed lint problems that an outside config had hidden, so I moved the config into the repository.

The repository instructions helped. The agent stopped and asked me before committing the data format change and the dependency change, as AGENTS.md says. Next time I would make these rules enforced and not only written: add CI, agent permission settings and a pre-commit hook.

---

## Appendix A. AI-use record

- Tool and model: Claude Code (VS Code extension), model Claude Opus 5.5 (`claude-opus-5-5`), plus one read-only sub-agent with the same model.
- Date: 22.11.2026
- What it received: the assignment PDF and the repository files. After commit dadd7d7 it also received `AGENTS.md` through `CLAUDE.md` (loaded automatically, I did not paste anything).

| # | What I asked (short) | AI output I used | Problems found | My decision / change | How it was checked |
|---|---|---|---|---|---|
| 1 | Help me do the assignment in this folder, make a plan | A plan based on the workflow from the PDF | The folder had no project | I chose to create a small Python + pytest project and write the report in Markdown, in English | I approved the plan before any files were written |
| 2 | Create the starting project | `expense_tracker` v0.1.0 with 2 tests. Some weaknesses were added on purpose so that the audit has something to find | It also had problems that nobody planned (CSV comma, `pytest` import error, lint config outside the repo) | Kept them and listed them as findings | `baseline_checks.txt`, `baseline_smoke.txt` |
| 3 | Write AGENTS.md and CLAUDE.md, fix the README | AGENTS.md sections 1 to 8 | The first version mentioned `exporters.py` before it existed | Removed that line before the commit and added it back with the refactoring | `git show dadd7d7:AGENTS.md` |
| 4 | Find a maintainability problem and use at most one pattern | Characterisation tests, then the Strategy refactoring | None | Accepted after the tests passed without changes | `task3_refactor_tests.txt` |
| 5 | Read-only risk review (exact prompt saved) | 8 risks, 14 claims in total | 2 unsupported, 2 only plausible (section 4) | Every claim was checked with commands | `task4_verification.txt` |
| 6 | Fix R2 and R3, tests first | Code and tests for M1 and M2 | Changes the data format and the expected test values | I read the diff and approved it before the commit (AGENTS.md section 8) | `mitigation_tests_before.txt`, `final_*.txt` |
| 7 | Pin dependencies, set lint and type config | `requirements-dev.txt`, `[tool.ruff]`, `[tool.mypy]` | The ruff rules found 15 long lines | Line length 110, split one line; I approved the dependency change | `final_checks.txt` |
| 8 | Write the report | Report draft | The first logs had empty exit codes (shell problem), one duplicate test run had a wrong label | Logs were made again with bash and real exit codes; the duplicate run was removed | log files, each with date and commit in the header |
| 9 | Take terminal screenshots for section 7.4 | Scripts that run the baseline and final steps in Terminal and save screenshots with `screencapture` | First screenshot was empty (no screen recording permission); one image cut off the title line | I gave the permission; the window was made bigger and the image taken again; I looked at every image | `docs/evidence/screenshots/` |

## Appendix B. Evidence files (`docs/evidence/`)

| File | What is inside |
|---|---|
| `baseline_checks.txt` | pytest, ruff, mypy --strict, build, pip-audit at baseline |
| `baseline_smoke.txt` | CLI steps that show W1 to W5 at baseline |
| `task3_refactor_tests.txt` | Test run after the Strategy refactoring and the count of duplicated checks |
| `task4_ai_risk_review_prompt.txt` | Exact prompt for the read-only review |
| `task4_ai_risk_review_output.md` | Full AI answer, not edited |
| `task4_verification.txt` | Commands and outputs used to check every claim |
| `mitigation_tests_before.txt` | New M1/M2 tests run on the old code (25 failed) |
| `mitigations_M1_M2.diff` | The diff I reviewed and approved before the commit |
| `final_checks.txt`, `final_smoke.txt`, `final_tests_verbose.txt` | Final version: checks, the same CLI steps, the 37 tests by name, git log and diff stats |
| `screenshots/01-04_*.png` | Terminal screenshots, baseline and final (section 7.4) |

How to repeat the checks:

```
git clone https://github.com/Mark6374/expense-tracker
cd expense-tracker
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pip install -e .
.venv/bin/pytest -q && .venv/bin/ruff check . && .venv/bin/mypy
git diff baseline final
```
