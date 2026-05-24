# Contributing

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
.\.venv\Scripts\python.exe main.py run --no-save --quick --skip-security --skip-gpu --skip-network
```

## Project Guidelines

- Keep benchmark modules independent under `pcbench/benchmarks/`.
- Keep security checks read-only.
- Do not commit generated reports from `/reports/`.
- Prefer terminal-first output over GUI dependencies.
- Document platform-specific behavior honestly.

## Commit Style

Use short imperative messages:

```text
Add DOCX report generation
Improve terminal summary output
Add Linux security checks
```
