# PCBench Local — Roadmap

This document is the source of truth for the in-flight refactor toward `v0.3.0`.
It defines phases, scope, deliverables, and definition-of-done. Update it as phases close.

## Workflow rules (apply to every phase)

- **One branch per phase, one PR per phase.** No giant branches mixing bug fixes with features.
- **Baseline before touching anything** (Phase 0). Phases 1-3 must not change JSON structure or dashboard scores without explicit justification.
- **Every bug fix ships with a test.** No test, no merge. Pure UX changes (wizard, .bat) need a documented manual test instead.
- `CHANGELOG.md` is updated when a phase closes, not per commit.
- Commit style stays as it is today (`Add...`, `Fix...`, `Harden...`, `Improve...`).
- Version bump: phases 1-3 close at `0.2.0`. Phase 6 closes at `0.3.0`.
- **Project language is English.** UI strings, wizard prompts, report bodies, log messages, and docs are all English. Spanish strings remaining from earlier work get migrated as part of Phase 3.

## Phase 0 — Setup

Goal: leave the repo ready to iterate without surprises.

- Create `ROADMAP.md` (this file).
- Decide and document unified language: **English**.
- Decide and document git strategy: **branch-per-phase + PR**.
- Generate Windows baseline: `main.py run --full --reports json,html,docx,md,supabase`. Saved under `.baseline/` (gitignored).
- Generate Docker baseline (after Phase 1 ping fix, since current Docker run reports network as failed).
- Note invariants: top-level JSON keys, dashboard row shape, report filename pattern.

Branch: `chore/phase-0-setup`.

## Phase 1 — Critical bugs · `fix/phase-1-critical-bugs` · 1-2 days

| File | Change |
|---|---|
| `benchmarks/network.py` | Platform-aware ping flag (`-n` Windows / `-c` Linux); Linux regex (`bytes from`, `time=`) |
| `runner.py` | `try/except` per step; record `status: failed` per module instead of aborting the run |
| `wizard.py` | Cancel returns cleanly with exit code 0, not `SystemExit(1)` |
| `benchmarks/disk.py` | Hoist `path.stat()` out of the latency loop; rename metric to reflect "fsync overhead" |
| `benchmarks/gpu.py` | On WMI failure return `[]` and surface the error in a separate key; `detected_count` reflects actual GPUs |
| `reports/compare.py` | Sort report list by filename, not mtime |

**New tests:**

- `tests/test_network_ping_parser.py` — real Windows ES/EN and Linux ping outputs, `subprocess.run` mocked.
- `tests/test_runner_resilience.py` — force exception in a step, verify JSON still saves.
- `tests/test_compare_sort_order.py` — inverted mtimes do not break ordering.

**Definition of done:** CI green. Docker smoke test passes without `--skip-network`.

## Phase 2 — Security and hardening · `fix/phase-2-security` · 2-3 days

| File | Change |
|---|---|
| `security/audit.py` | `IsUserAnAdmin()`; banner when not admin; mark partial reports |
| `reports/sanitize.py` (new) | Truncated hash for hostname/IP/usernames; global `--sanitize` flag |
| `logging_setup.py` (new) | File logger at `reports/pcbench.log` with simple rotation |
| `runner.py` | SIGINT handler that cleans up the disk benchmark temp file |
| `SECURITY.md` | Explicit list of outbound endpoints (`1.1.1.1`, `8.8.8.8`, `google.com`, optional speedtest) |
| `Dockerfile` | Non-root `USER pcbench` |
| `.github/workflows/ci.yml` | `pip_audit` runs against all three requirements files |

**New tests:** `tests/test_sanitize.py` (no PII via grep), `tests/test_audit_admin.py` (mock no-admin → warning in findings).

**Definition of done:** `pcbench run --sanitize` produces reports with no PII findable via grep. Partial reports are visibly marked when admin is missing.

## Phase 3 — Foundation decisions · `feat/phase-3-foundation` · 1-2 days

| File | Change |
|---|---|
| All UI/report strings | Migrate Spanish strings to English |
| `cli.py` | Add `--version`, `--output-dir`, `--keep-last N` |
| `reports/*.py` | Honor `--output-dir`. Default to `~/Documents/PCBench/reports` (Windows) or `~/PCBench/reports` (Linux/macOS) |
| New helper | `--keep-last 20` prunes oldest reports when saving |

**New tests:** `tests/test_output_dir.py`, `tests/test_keep_last.py`.

**Definition of done:** `pcbench --version` prints `0.2.0`. Reports default outside the project directory.

## Phase 4 — Non-technical UX · `feat/phase-4-ux` · 2-3 days

| File | Change |
|---|---|
| `wizard.py` | Numbered menu (1-4), one-line explanations per option |
| `runner.py` | At the end, prompt to open the HTML report; `webbrowser.open()` / `os.startfile()` |
| `setup.bat` (new) | Detect `py`/`python`; if missing, open download URL; create venv; install requirements; launch wizard |
| `pcbench.bat` | Just launch wizard (assumes setup is done) |
| `security/audit.py` | If not admin, offer `--elevate` (relaunch via UAC) |

**Manual tests documented in `docs/manual-tests.md`:**

- PC without Python → `setup.bat` walks the user all the way to a report.
- Double-click on `pcbench.bat` → wizard launches, HTML opens automatically.
- Ctrl+C mid-run → temp file cleaned up, clean exit.

**Definition of done:** a fresh Windows user with no Python reaches an open HTML report by following `setup.bat` alone.

## Phase 5 — Dependencies · `chore/phase-5-deps` · 1 day

- `GPUtil` → `pynvml` (official NVIDIA). Rewrite `_collect_gputil_gpus`.
- `speedtest-cli`: drop from `requirements.txt`; document as optional manual install for `--speedtest`.
- `docx_report.py`: **do not migrate** to `python-docx` if the current output opens cleanly in OnlyOffice/Word. Rule: don't break what works.
- Bump everything to versions that pass `pip-audit`.

**Definition of done:** `pip-audit` green across all three requirements files.

## Phase 6 — Distribution · `feat/phase-6-distribution` · 2-3 days

- `build/pyinstaller.spec` producing `pcbench` as a single binary.
- `.github/workflows/release.yml`: on `v*` tag, Windows runner builds the `.exe` and uploads it as a release asset.
- README "Download" section linking to the latest release.
- Optional: code signing if a cert is available (without it, SmartScreen will warn — document the workaround).

**Definition of done:** tagging `v0.3.0` produces `pcbench-0.3.0-windows.exe` that runs on a machine without Python installed.

## Phase 7 — New features (post-stabilization)

Only after Phase 6 closes. One PR per feature.

- `feat/sqlite-history` — SQLite instead of a folder of JSON files, with automatic migration of existing reports.
- `feat/trend-graphs` — embed trend charts in the HTML report (requires SQLite first).
- `feat/schedule-mode` — `pcbench schedule weekly` creates a Windows Scheduled Task or cron entry.

## Tracking board

| Phase | Type | Effort | Blocks |
|---|---|---|---|
| 0 | setup | 0.5d | everything |
| 1 | bugs | 1-2d | 2, 3 |
| 2 | security | 2-3d | 6 |
| 3 | foundation | 1-2d | 4 |
| 4 | UX | 2-3d | 6 |
| 5 | deps | 1d | — |
| 6 | release | 2-3d | 7 |
| 7 | features | weeks | — |

**Total phases 0-6: ~10-15 working days.**

## PR checklist (will live in `.github/PULL_REQUEST_TEMPLATE.md`)

- [ ] New tests cover the changed code paths.
- [ ] `python -m pytest` green locally.
- [ ] CI green.
- [ ] If `runner.py`, `cli.py`, or `reports/` changed: baseline diff reviewed.
- [ ] If `SECURITY.md` scope touched: `SECURITY.md` updated.
- [ ] `CHANGELOG.md` updated if this PR closes a phase.
