---
name: PCBench Local
description: A mechanic's inspection sheet for your PC — three lights per line, one lit.
colors:
  ink: "#17324f"
  ink-hover: "#0f2540"
  ink-text: "#e9eff5"
  ink-muted: "#b4c4d4"
  paper: "#eef2f5"
  sheet: "#ffffff"
  rule: "#d5dde5"
  rule-strong: "#b3c0cc"
  text: "#15202b"
  muted: "#526070"
  light-off: "#e6ebf0"
  red: "#c0262d"
  red-soft: "#fbeaea"
  amber: "#e5a019"
  amber-text: "#8a5300"
  amber-soft: "#fdf4e3"
  green: "#2f8a57"
  green-text: "#1d6a40"
typography:
  form:
    fontFamily: "Bahnschrift, DIN Alternate, Roboto Condensed, Arial Narrow, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.12em"
  body:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.5
  verdict:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 600
    lineHeight: 1.25
rounded:
  sm: "4px"
  md: "8px"
  pill: "12px"
spacing:
  xs: "6px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.sheet}"
    rounded: "{rounded.md}"
    padding: "15px 18px"
  button-primary-hover:
    backgroundColor: "{colors.ink-hover}"
  button-secondary:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
    padding: "8px 14px"
  shell-bar:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ink-text}"
    height: "56px"
  checklist:
    backgroundColor: "{colors.sheet}"
    rounded: "{rounded.md}"
  lights:
    backgroundColor: "{colors.light-off}"
    rounded: "{rounded.pill}"
---

# Design System: PCBench Local

## Overview

The desktop window is a vehicle multi-point inspection sheet. Every check is a printed line with three lights (red, amber, green) and exactly one is lit. The visitor presses one button, watches the sheet fill in line by line, reads one plain-language verdict, and opens the red lines first to follow numbered fix steps. It is an Operate surface: standard tabs, buttons and lists; the world contributes type, palette, density and the light signature only.

## Colors

### Primary
**Inspection ink** (`#17324f`) carries the shell bar and the single primary action ("Revisar mi PC"). Nothing else uses it as a fill.

### Neutral
**Form paper** (`#eef2f5`) is the window ground; **sheet** white holds the summary column and checklists; **printed rules** (`#d5dde5`, strong `#b3c0cc`) divide lines, never shadows. Body text `#15202b`, secondary `#526070` (6.4:1 on white).

### Named Rules
**Lights carry meaning, never decoration.** Red, amber and green appear only as the lit light of a line, the line title tinted to match (amber uses `#8a5300` for text contrast), the tally dots and the tab counts. A green fill anywhere else is a bug.
**Notes are unlit.** Informational findings show all three lights off, a dashed light frame and a "Nota" tag; they never count as problems.

## Typography

One workhorse UI face plus one form face.

### Hierarchy
- **Form labels** (Bahnschrift, 13px, 600, uppercase, 0.12em): sheet title, group headers with a rule running to the edge, "Cómo arreglarlo", scores and counts.
- **Verdict** (Segoe UI Variable, 22px, 600): one sentence, red when urgent.
- **Line title** (15px, 600) over **detail** (13px, muted) — detail appears only when it adds a fact (days, product names, ports).
- **Body** (15px/1.5), fix steps as an ordered list, measure capped at 78ch.

## Layout

Shell bar (56px) across the top; below, a 320px summary sheet (date, verdict, tally, primary action, report controls, read-only disclaimer pinned to the bottom) and the checklist area with tabs Seguridad / Rendimiento. Groups are ordered by their worst light; lines inside a group red → amber → green → note → resolved. Under 860px the summary stacks above the checklist and the page scrolls as one column.

## Elevation & Depth

Flat sheets separated by 1px printed rules. The only shadow is on the primary button (`0 1px 2px` + `0 4px 10px`, ink-tinted), to mark it as the one thing to press.

## Shapes

Lines live in 8px-radius lists; the three lights sit in a 12px pill with a 1px rule border; tags are 4px. No cards inside cards.

## Components

### Buttons
Primary: full-width ink, 18px semibold label, disabled to `#7d8fa3` while scanning with the label "Revisando…". Secondary: white with strong rule border. Text links underline at 3px offset.

### Checklist line
A full-width button: lights · title/detail · value · chevron. Red lines open by default; others expand on click or Enter, `aria-expanded` kept in sync. Lines without explanation are static (no chevron, not focusable).

### Tabs
Standard underline tabs (3px ink indicator), arrow keys switch, a count chip tinted by the worst light.

## Motion

One authored moment: when a scan finishes, lines stamp onto the sheet in sequence (45ms stagger, 420ms ease-out, lights scale in 120ms later). While scanning, only the line being checked pulses its lights. Everything is disabled under `prefers-reduced-motion`.

## Do's and Don'ts

- Do keep every check a line with three lights; do put fixes in numbered steps a non-technical person can follow.
- Do keep lines fixed since the last scan on the sheet, tagged "Resuelto".
- Don't add a score gauge, a hero number or icon tiles; the verdict sentence leads.
- Don't use emoji or glyphs as icons; draw SVG.
- Don't show technical English messages in the Spanish interface.
