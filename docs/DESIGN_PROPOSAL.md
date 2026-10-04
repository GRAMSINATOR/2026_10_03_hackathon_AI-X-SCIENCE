# Design proposal: Parallax console looks (qte77, 2026-10-04)

A proposal only: adopt or keep is your call. Live reference, rendering your decision briefs:
<https://thismay52--hackbench-web.modal.run/results/?batch=Batch_3> (`?look=polymer|console|lab80`).
No code is copied in this PR; the values below are design data.

**Shared lineage:** your page background `#e4e3df` (`app.py`, `.streamlit/config.toml`) is already the polymer and lab80 background, and the source design template carried the PARALLAX name, so this extends a palette you already use.

## Polymer look (proposed default)

Light soft-UI; Inter throughout; no split-flap animation. Text tokens were darkened so that every text-on-surface pair is at least 4.5:1 (WCAG AA), checked by a test in HackBench.

| Token | Value | Role |
|---|---|---|
| bg | `#e4e3df` | page |
| surface-0 / 1 / 2 | `#e8e8e3` / `#ebe9e4` / `#e0ddd7` | cards, panels |
| text / text-2 / text-3 | `#1f1e1b` / `#3c3a35` / `#55524c` | body, secondary, tertiary |
| crit (reject) | `#b23327` | ≥ 4.5:1 on all surfaces |
| warn (investigate) | `#825900` | ≥ 4.5:1 |
| ok (accept) | `#17703e` | ≥ 4.5:1 |
| ref (reference) | `#2d5ebc` | ≥ 4.5:1 |
| link | `#13669e` | ≥ 4.5:1 (the template's `#1677b8` was 3.75:1) |

Also available: **console** (dark, `#0f1011`, Big Shoulders Display / Archivo / JetBrains Mono) and **lab80** (retro lab instrument). The look is chosen by `?look=`, then the saved choice, then polymer.

## Section map (ours → yours)

| Console section | Your equivalent | Suggestion |
|---|---|---|
| Rail: batch and look selectors | DATASET / REFERENCE FRAME row | keep yours |
| Decision slab and readouts | instrument and metrics | keep yours |
| KPI matrix | "Why: evidence" heatmap | keep yours (micrograph-level) |
| Support, limits, next capture | instrument readout | keep yours |
| **Second method: HackBench** (explicit "methods disagree" line) | none | **adopt**, as a link or expander |
| **Validation and infrastructure** (pre-registration, planted-drift suite, cycle stages, journal) | none | **adopt**, as a link |
| Attribution footer | none | adopt |

## Mobile rules

- Below 720 px the evidence matrix becomes a horizontal scroller with a sticky first column and a "swipe" hint.
- `@media (pointer: coarse)` gives 44 px touch targets.
- `env(safe-area-inset-*)` padding.
- Grids stack to one column.
- In HackBench's browser check, no viewport scrolled horizontally at 390 px (portrait) or 844 px (landscape).

No imagery is included (#4 is still open). Please link the live console rather than commit screenshots.
