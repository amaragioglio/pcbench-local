# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Desktop window built with pywebview: a local HTML/CSS/JS page rendered in the OS webview (Edge WebView2 on Windows), talking to the existing Python engine through a JS bridge. No web server, no network listener. The terminal CLI stays as-is for technicians. Packaged as a Windows .exe with PyInstaller.

## Users

- People at home who suspect their PC is slow or unsafe and do not know much about computers.
- Owners of small businesses checking the PCs in their office or shop without an IT person.
- Secondary: the technician they may send the report to. The app speaks plainly to the first two, and the exported report must still be useful to the third.

## Product Purpose

Answer, in a few minutes and in plain language, "Is my PC safe?" first and "Is it performing well?" second, and tell the person exactly what to do about each problem. Success: a non-technical person runs it, understands the result without help, and fixes or forwards the urgent items.

## Positioning

A free, local, read-only check that combines security posture and hardware performance in one run, explains every finding with step-by-step fixes in Spanish or English, and can produce a shareable report with personal identifiers removed. It is not an antivirus and must say so.

## Operating Context

- Windows 10/11 PCs at home or in small offices; run on demand, occasionally weekly.
- Some checks need administrator rights; the app must work without them and say what was skipped.
- Benchmarks load the CPU, RAM and disk for a short time; the user should not be using the PC heavily during the run.
- Reports are saved locally (HTML, JSON, DOCX, Markdown) and may be sent to a technician.

## Capabilities and Constraints

- Read-only: never changes settings, never reads passwords, never uploads anything.
- Security checks (Windows): antivirus via Security Center, Defender tamper protection and signature age, firewall, Windows Update age and pending restart, UAC, Guest account, automatic sign-in, Remote Desktop/NLA, SMBv1, Secure Boot, BitLocker, SmartScreen, network-exposed ports.
- Performance: CPU single/multi-core, RAM bandwidth, disk read/write (cache-bypassed) and latency, network ping/jitter/DNS, GPU sensors when available; each with a confidence level.
- Languages: Spanish and English, chosen from the OS language with a manual switch.
- Not a replacement for antivirus or professional benchmarks (Cinebench, CrystalDiskMark).

## Brand Commitments

- Name: PCBench Local.
- Existing technical reports and CLI use a green-on-black terminal look for technicians; that look is not binding for the new consumer window.

## Evidence on Hand

- Real benchmark and audit engine with automated tests (pcbench/).
- No testimonials, user counts, certifications or partnerships exist; none may be claimed.

## Product Principles

1. Safety first: urgent security issues appear before anything else.
2. Plain words, real steps: every problem says why it matters and how to fix it.
3. Honest numbers: show confidence, never overstate precision, never imply antivirus protection.
4. Nothing leaves the PC unless the person chooses to share a report.
5. Works without admin rights and says what it could not check.

## Accessibility & Inclusion

Must be usable by people with low technical confidence: readable type sizes, clear contrast, keyboard operable, no jargon in primary text, Spanish and English parity.
