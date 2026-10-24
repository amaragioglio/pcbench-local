# Changelog

## Unreleased

### 0.4.0 — desktop window for everyone

- Add desktop window (`PCBench.exe`, `main.py app`): one button, plain-language results in Spanish and English, security first, three-light inspection sheet, fix steps per finding, "fixed since last check", sanitized report by default.
- Expand Windows security audit: Security Center antivirus/firewall (no false alarm with third-party antivirus), Defender tamper protection and definition age, Windows Update age and pending restart, UAC, Guest account, automatic sign-in, Remote Desktop/NLA, SMBv1, Secure Boot, BitLocker, SmartScreen.
- Harden: PowerShell called by absolute path; new `critical` severity; missing admin rights is info, not a security warning; loopback-only ports are not reported as exposed.
- Improve accuracy: CPU warm-up and median of three trials with process start-up excluded; RAM measured with memcpy/memchr instead of a Python loop; disk reads bypass the OS cache; each result has a confidence level. RAM and disk scores rescaled; scores from 0.3.x are not directly comparable.
- Build two executables: `PCBench.exe` (window) and `pcbench-cli.exe` (terminal). UPX disabled to reduce antivirus false positives.

### Earlier unreleased changes

- Harden `--sanitize`: tokens are now keyed per run (HMAC) instead of plain truncated SHA-256, which allowed recovering private IP addresses by brute force. Also redacts MAC addresses and user profile folders found in free text.
- Improve HTML report: overall score with per-area bars, color-coded OK/WARN/FAIL, security findings listed by severity, readable timestamps, mobile layout without horizontal scroll.
- Show only the JSON file name in the HTML report; full paths could expose the account name.
- Fix CI dependency audit for Windows-only packages on Linux runners.
- Rewrite README introduction, quick start and privacy section for public release.

## 0.3.0

- Added normalized dashboard scores.
- Added Markdown report export.
- Added explicit compare options for base/current reports and profile filtering.
- Added interactive wizard command.
- Added Supabase-optimized JSON export.
- Added Windows launcher script.
- Added wizard presets and execution confirmation.
- Added Linux read-only security audit.
- Added `--sanitize` report mode for shareable reports without raw hostnames, IPs, users, commands, or endpoints.
- Added privilege-scope detection and partial security audit markers.
- Added local rotating runtime log at `reports/pcbench.log`.
- Added `Ctrl+C` cleanup for disk benchmark temporary files.
- Hardened Docker runtime with a non-root user.
- Expanded CI dependency audit to all requirements files.
- Documented outbound network targets.
- Added Phase 3 foundation: version flag, output directory, report retention and English UI/report strings.
- Added Phase 4 UX: numbered wizard, Windows setup launcher, HTML open prompt and optional UAC elevation.
- Replaced GPUtil/py3nvml with NVIDIA NVML bindings through `nvidia-ml-py`.
- Removed `speedtest-cli` from core dependencies; `--speedtest` is now optional.
- Added PyInstaller spec and tag-driven Windows release workflow.
- Added local SQLite run history with `pcbench history`.
- Added inline HTML score trend charts backed by SQLite history.
- Added weekly schedule command with Windows Scheduled Task support and cron guidance.

## 0.1.0

- Added terminal-first CLI.
- Added system inventory.
- Added RAM, CPU, disk, network, and GPU diagnostics.
- Added read-only local security audit.
- Added JSON, HTML, and DOCX reports.
- Added report comparison.
- Added Dockerfile and GitHub Actions CI.
- Added project packaging metadata.
