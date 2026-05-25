# Security Policy

## Supported Versions

PCBench Local is currently pre-1.0. Security fixes are applied to the `main` branch.

## Scope

This project is a local diagnostic and benchmark tool. It should not collect secrets, upload reports automatically, or modify security settings without explicit user action.

The security audit module is read-only by design. It checks local configuration such as firewall state, Defender status, listening ports, startup entries, and local administrators.

When the tool is not running with administrator/root privileges, audit output is marked with `partial: true` and a privileges finding. The tool still runs read-only checks, but process, port, service, or security-provider details may be incomplete.

## Reporting a Vulnerability

For private repositories, report issues directly to the repository owner.

When reporting, include:

- Operating system and Python version.
- Command used.
- Relevant error output.
- Whether the issue exposes sensitive local data or changes system state.

## Sensitive Data

Generated reports may include local hardware details, usernames, IP addresses, listening ports, process names, and security configuration summaries. Reports are ignored by Git via `/reports/` and should be reviewed before sharing publicly.

Use `--sanitize` when generating reports that will be shared, uploaded, or imported into an external database. Sanitized reports replace hostnames, IP addresses, usernames, command paths, and connection endpoints with deterministic truncated hash tokens.

## Design Rules

- Do not add network upload behavior by default.
- Do not store credentials or tokens in reports.
- Do not run destructive commands from audits.
- Keep security checks read-only unless a future command clearly asks the user for remediation.
