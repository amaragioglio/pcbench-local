# Contributing

## Language Policy

All user-facing text — CLI output, wizard prompts, report bodies, log messages,
README, and repo docs — is written in **English**.

Legacy Spanish strings still present in the code are being migrated as part of
Phase 3 of the active roadmap (see `ROADMAP.md`). Do not introduce new Spanish
strings; if you touch a Spanish string while working in another phase, leave it
alone unless that PR is explicitly part of the migration.

## Branch Strategy

The active refactor follows a strict **branch-per-phase + PR** workflow:

- One branch per phase (e.g. `fix/phase-1-critical-bugs`, `feat/phase-4-ux`).
- One PR per phase, merged to `main` only when CI is green.
- Do not mix bug fixes with new features in the same branch.
- Phase scope and definition-of-done are tracked in `ROADMAP.md`.

For ad-hoc fixes outside the roadmap, branch off `main` with a descriptive
name (`fix/<short-description>` or `chore/<short-description>`) and open a PR.

## Local Setup

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
```

Linux/macOS:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

## Development Checks

```powershell
.\.venv\Scripts\python.exe -m compileall pcbench
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe main.py run --no-save --quick --skip-security --skip-gpu --skip-network
```

## Baselines

Before starting work on phases 1-3, generate a local baseline:

```powershell
.\.venv\Scripts\python.exe main.py run --full --reports json,html,docx,md,supabase
```

Copy the generated files from `reports/` into `.baseline/` (gitignored) and use
them to diff against new runs. The dashboard scores and JSON structure must not
regress without explicit justification in the PR description.

## Project Guidelines

- Keep benchmark modules independent under `pcbench/benchmarks/`.
- Keep security checks read-only.
- Do not commit generated reports from `/reports/` or `/.baseline/`.
- Prefer terminal-first output over GUI dependencies.
- Document platform-specific behavior honestly.

## Commit Style

Use short imperative messages:

```text
Add DOCX report generation
Improve terminal summary output
Fix Linux ping flag in network benchmark
```
