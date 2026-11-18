# PCBench Local

Terminal-first local PC benchmark, hardware inventory, network check, GPU detection and read-only security audit.

Run a quick check, export a report, and compare it with later runs to track changes in your PC's performance.

## Quick start

**Windows (standalone):** Download `pcbench-0.3.0-windows.exe` from [release v0.3.0](https://github.com/amaragioglio/pcbench-local/releases/tag/v0.3.0), then launch it from PowerShell:

```powershell
.\pcbench-0.3.0-windows.exe wizard
```

You can also [run from source](#install) on Windows, Linux, or macOS with Python 3.11+.

## Features

- CPU single-core and multi-core benchmark.
- RAM allocation and approximate read/write bandwidth.
- Disk read, write and fsync-overhead latency.
- Network ping, jitter, DNS and TCP connectivity.
- GPU detection, VRAM, usage and temperature when exposed by the driver.
- Windows security audit: Defender, firewall, ports, connections, local admins and startup entries.
- Linux security audit: firewall, sudo users, ports, connections, systemd services and container detection.
- JSON, HTML and DOCX reports compatible with OnlyOffice.
- Markdown report for GitHub/issues.
- Supabase-optimized flat JSON export.
- Dashboard with overall score and category status.
- Report comparison.
- Dockerfile for portable usage, with the normal hardware visibility limits of containers.

## Security

- Reports and logs are local-only.
- There is no automatic upload.
- The security audit is read-only.
- Use `--sanitize` before sharing reports outside your machine.
- If PCBench is not running as administrator/root, the security audit marks `partial: true`.
- Runtime logs are written to `pcbench.log` in the selected report directory.
- See [SECURITY.md](SECURITY.md) for scope and outbound network targets.

## Install

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
```

Development on Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
```

Guided Windows setup:

```powershell
.\setup.bat
```

Linux/macOS:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

## Usage

Recommended interactive mode:

```powershell
.\.venv\Scripts\python.exe main.py wizard
```

Windows launcher:

```powershell
.\pcbench.bat
```

Version:

```powershell
.\.venv\Scripts\python.exe main.py --version
```

Quick profile:

```powershell
.\.venv\Scripts\python.exe main.py run --quick
```

Full profile:

```powershell
.\.venv\Scripts\python.exe main.py run --full
```

Shareable sanitized report:

```powershell
.\.venv\Scripts\python.exe main.py run --quick --sanitize --reports json,html,supabase
```

Custom output directory and retention:

```powershell
.\.venv\Scripts\python.exe main.py run --quick --output-dir .\reports --keep-last 20
```

Compare the two latest JSON reports:

```powershell
.\.venv\Scripts\python.exe main.py compare
```

Compare only reports from the same profile:

```powershell
.\.venv\Scripts\python.exe main.py compare --profile quick
```

Compare specific files:

```powershell
.\.venv\Scripts\python.exe main.py compare --base reports\old.json --current reports\new.json
```

Show local SQLite history:

```powershell
.\.venv\Scripts\python.exe main.py history --limit 10
```

Preview weekly scheduling:

```powershell
.\.venv\Scripts\python.exe main.py schedule --dry-run
```

Install a weekly Windows Scheduled Task:

```powershell
.\.venv\Scripts\python.exe main.py schedule
```

## Options

```powershell
.\.venv\Scripts\python.exe main.py run --no-save
.\.venv\Scripts\python.exe main.py run --skip-ram
.\.venv\Scripts\python.exe main.py run --skip-cpu
.\.venv\Scripts\python.exe main.py run --skip-disk
.\.venv\Scripts\python.exe main.py run --skip-network
.\.venv\Scripts\python.exe main.py run --skip-gpu
.\.venv\Scripts\python.exe main.py run --skip-security
.\.venv\Scripts\python.exe main.py run --ram-mib 2048
.\.venv\Scripts\python.exe main.py run --cpu-seconds 10
.\.venv\Scripts\python.exe main.py run --disk-mib 1024
.\.venv\Scripts\python.exe main.py run --speedtest
.\.venv\Scripts\python.exe main.py run --reports json,html,supabase
.\.venv\Scripts\python.exe main.py run --sanitize
.\.venv\Scripts\python.exe main.py run --output-dir .\reports --keep-last 20
.\.venv\Scripts\python.exe main.py run --elevate
```

## Reports

Default report directory:

- Windows: `~/Documents/PCBench/reports`
- Linux/macOS: `~/PCBench/reports`

Generated artifacts:

- `pcbench_report_*.json`: complete data for comparison.
- `pcbench_report_*.html`: browser-friendly visual summary.
- `pcbench_report_*.docx`: document you can open with OnlyOffice or Word.
- `pcbench_report_*.md`: Markdown summary for GitHub.
- `pcbench_supabase_*.json`: flat payload for Supabase.
- `pcbench.log`: local rotating runtime log.
- `pcbench_history.sqlite`: local SQLite history for runs, metrics and findings.

When history has at least two rows, HTML reports include an inline score trend chart.

### Supabase JSON

The Supabase export contains these flat table keys:

- `pcbench_runs`
- `pcbench_metrics`
- `pcbench_findings`

Each key contains rows designed for import or insert into Supabase tables.

## Optional Speedtest

`--speedtest` requires the optional `speedtest-cli` package:

```powershell
.\.venv\Scripts\python.exe -m pip install speedtest-cli
```

## Docker

Build image:

```powershell
docker build -t pcbench-local .
```

Run quick profile:

```powershell
docker run --rm -it pcbench-local
```

Save reports to a local folder:

PowerShell:

```powershell
docker run --rm -it -v ${PWD}\reports:/app/reports pcbench-local run --quick --output-dir /app/reports --skip-security
```

Bash:

```bash
docker run --rm -it -v "$PWD/reports:/app/reports" pcbench-local run --quick --output-dir /app/reports --skip-security
```

If your terminal does not support TTY, run without `-it`:

```powershell
docker run --rm pcbench-local
```

Docker notes:

- Containers do not always see host hardware exactly as the host sees it.
- Disk benchmarks measure the container filesystem or mounted volume.
- GPU requires extra setup, such as NVIDIA Container Toolkit on Linux.
- Windows Defender/firewall security checks do not apply inside a Linux container.
- For real Windows diagnostics, run PCBench locally on Windows.

## Structure

```text
pcbench/
  benchmarks/
  reports/
  security/
  cli.py
  logging_setup.py
  runner.py
  terminal_ui.py
main.py
pcbench.bat
requirements.txt
requirements-dev.txt
requirements-windows.txt
Dockerfile
pyproject.toml
```

## Scope

PCBench does not replace professional tools such as Cinebench, CrystalDiskMark, 3DMark or MemTest86. It is built for local diagnostics, repeated comparisons and basic read-only security posture checks.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and tests.

## License

[MIT](LICENSE).
