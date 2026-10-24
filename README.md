# PCBench Local

**Benchmark, hardware check and read-only security audit for your PC, from the terminal.**
Find out if your machine is healthy, compare it with itself over time, and share a report
without leaking your IP, hostname or username.

No account, no telemetry, no uploads. Everything runs and stays on your computer.

![HTML report](docs/img/html-report.png)

## What it checks

| Area | What you get |
|---|---|
| CPU | Single-core and multi-core score, scaling factor |
| RAM | Safe allocation test, read/write bandwidth |
| Disk | Read/write speed and fsync latency |
| Network | Ping, jitter, packet loss, DNS and TCP reachability (optional speed test) |
| GPU | Detection, VRAM, usage and temperature when the driver exposes them |
| Security (Windows) | Defender, firewall, listening ports, connections, local admins, startup items |
| Security (Linux) | Firewall, sudo users, listening ports, connections, systemd services, containers |

Each run produces an overall score out of 100, a status per area, and reports in JSON, HTML,
Markdown, DOCX and a flat JSON ready for Supabase. A local SQLite history powers comparisons and a
score trend chart.

## Quick start

**Windows** (Python 3.11+):

```powershell
git clone https://github.com/amaragioglio/pcbench-local.git
cd pcbench-local
.\setup.bat        # creates .venv and installs dependencies
.\pcbench.bat      # guided wizard
```

**Linux / macOS**:

```bash
git clone https://github.com/amaragioglio/pcbench-local.git
cd pcbench-local
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python main.py wizard
```

Prefer a single file? Tagged [releases](https://github.com/amaragioglio/pcbench-local/releases) include
`pcbench-<version>-windows.exe`. It is unsigned, so Windows SmartScreen may warn you: choose
**More info → Run anyway**, or build from source.

## Privacy and security

- **Nothing is uploaded.** Reports, logs and history are written only to your reports folder.
- **The audit is read-only.** It never changes firewall, Defender, services or users.
- **Share with `--sanitize`.** Hostnames, IPs, MAC addresses, usernames, user folders, command paths and
  connection endpoints are replaced with tokens. Tokens are keyed with a random secret per run, so the
  same IP looks the same inside one report but cannot be recovered by guessing.
- Without administrator/root rights the audit still runs and is marked `partial: true`.
- Network checks contact only the targets listed in [SECURITY.md](SECURITY.md).

```powershell
.\.venv\Scripts\python.exe main.py run --quick --sanitize --reports json,html,md
```

## More commands

Examples use the Windows virtual environment path; on Linux/macOS use `./.venv/bin/python`.

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
.\.venv\Scripts\python.exe main.py run --quick --output-dir D:\PCBench\reports --keep-last 20
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

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md): every bug fix ships with
a test, and `python -m pytest` must pass. Security issues: see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
