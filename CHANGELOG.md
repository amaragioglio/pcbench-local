# Changelog

## 0.1.0

- Added terminal-first CLI.
- Added system inventory.
- Added RAM, CPU, disk, network, and GPU diagnostics.
- Added read-only local security audit.
- Added JSON, HTML, and DOCX reports.
- Added report comparison.
- Added Dockerfile and GitHub Actions CI.
- Added project packaging metadata.

## Unreleased

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
