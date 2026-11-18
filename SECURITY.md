# Security Policy

## Supported Versions

PCBench Local is currently pre-1.0. Security fixes are applied to the `main` branch.

## Scope

This project is a local diagnostic and benchmark tool. It should not collect secrets, upload reports automatically, or modify security settings without explicit user action.

The security audit module is read-only by design. On Windows it runs one PowerShell script (`pcbench/security/windows_posture.ps1`, invoked by absolute path from System32) that reads configuration: Security Center antivirus and firewall products, Defender status, Windows Update history, UAC, Guest account, automatic sign-in (only whether a stored password exists, never its value), Remote Desktop, SMBv1, Secure Boot, BitLocker and SmartScreen. It also lists listening ports, startup entries and local administrators. It never changes a setting.

When the tool is not running with administrator/root privileges, audit output is marked with `partial: true` and a privileges finding. The tool still runs read-only checks, but process, port, service, or security-provider details may be incomplete.

## Reporting a Vulnerability

Please do not open a public issue for vulnerabilities. Use GitHub's **Report a vulnerability** button on the Security tab of this repository (private vulnerability reporting).

When reporting, include:

- Operating system and Python version.
- Command used.
- Relevant error output.
- Whether the issue exposes sensitive local data or changes system state.

## Sensitive Data

Generated reports may include local hardware details, usernames, IP addresses, listening ports, process names, and security configuration summaries. Reports are ignored by Git via `/reports/` and should be reviewed before sharing publicly.

Use `--sanitize` when generating reports that will be shared, uploaded, or imported into an external database. Sanitized reports replace hostnames, IP addresses, MAC addresses, usernames, user profile folders, command paths, and connection endpoints with tokens. Tokens are HMAC-SHA256 values keyed with a random secret generated for each run: they are consistent within one report, but cannot be reversed by hashing candidate values (a plain hash of a private IPv4 address can be brute-forced in milliseconds). Tokens from different runs do not match.

Runtime logs are written to `reports/pcbench.log` with simple rotation. Logs are local-only and ignored by Git; they are intended for troubleshooting module start, finish, artifacts, and failures.

If execution is interrupted with `Ctrl+C`, PCBench attempts to remove the disk benchmark temporary file before exiting.

## Design Rules

- Do not add network upload behavior by default.
- Do not store credentials or tokens in reports.
- Do not run destructive commands from audits.
- Keep security checks read-only unless a future command clearly asks the user for remediation.

## Outbound Network Scope

Network checks only run when the network module is enabled. Default outbound targets are:

- `1.1.1.1` for ping latency.
- `1.1.1.1:443` for TCP connectivity.
- `google.com:443` for DNS resolution timing.
- Speedtest servers selected by `speedtest-cli` only when `--speedtest` is explicitly enabled.

Users can change ping and DNS targets with `--ping-host` and `--dns-host`.
