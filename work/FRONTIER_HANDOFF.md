# Marker Frontier workstream: coordination / handoff note

Parallel workstream to the Decision Brief / hero / Examiner Matrix work. It runs in the shared working tree; there is
no worktree, because `renderer/` and `qc/brief.py` are untracked, so a worktree from HEAD would not contain them.
Contract and rules: `docs/MARKER_FRONTIER.md`.

## Files this workstream owns (all new)

| File | Role |
|---|---|
| `qc/frontier.py` | `marker-frontier/1`: merges research bundles, resolves blindspot refs against epistemic-field/1, derives gates and states; `check()`, `inject()`, `attach()` |
| `schema/marker_research.v1.schema.json` | qte77 ingestion socket (research bundle schema) |
| `research/seed.controller.json` | real seed bundle: controller blindspots + research log (no literature) |
| `fixtures/frontier/example.qte77.json` | FIXTURE bundle (synthetic placeholder papers) |
| `fixtures/marker_frontier.json`, `fixtures/marker_frontier.example.json` | built frontier documents (`python -m qc.frontier fixtures`) |
| `docs/MARKER_FRONTIER.md` | contract, governance, ingestion |
| `renderer/src/model/frontier.js` | pure view model |
| `renderer/src/ui/MarkerFrontier.jsx`, `renderer/src/ui/frontier.css` | the section; CSS is scoped under `.mf` |
| `renderer/frontier.html`, `renderer/src/frontier-main.jsx` | standalone dev preview (`npm run dev` → /frontier.html) |
| `renderer/test/frontier.test.js`, `tests/test_frontier.py` | tests |
| `work/qa_frontier.py` | screenshots (`work/viz/frontier_*.png`) |

## Shared files touched (minimal hooks, applied after re-reading the latest versions)

* `renderer/src/App.jsx`: one import line, plus `<MarkerFrontier field={M.F} brief={brief} onTrace={onTrace} />`
  after the raw-proof `<details>`. The component reads its own payload (`#frontier-payload`; in dev it fetches
  `/marker_frontier.json`), so `data.js` did not change.
* `app.py`: `from qc import … frontier …`; `render_instrument(…, research=())` returns
  `frontier.attach(html, REPORTS)`; the call site passes `frontier.signature(REPORTS)` as the cache key.
* `renderer/dist/index.html`: rebuilt (`vite build`) with the then-current sources from both workstreams.

## Interface consumed (read-only)

* `qc.brief.resolve` (the `{collection, id, path}` resolver), reused for engine-fact references.
* epistemic-field/1:
  * `rims[]`, `missing_dimensions[]`, `dimensions[kind=missing]`;
  * `actions[].triggered_by` / targets, to show which controller action already addresses a blindspot.
  * Action ids are not referenced from bundles: they are rank-based and would go stale.
* decision-brief/1 (renderer): limit claims `limit.<rim id>`, or a claim whose `focus` is that rim / missing
  dimension. A frontier blindspot chip calls the existing `onTrace(claim)` only for such claims, so nothing is ever
  attributed to the brief that the brief does not state.

## Dependencies on the Decision Brief agent

* If `limit.<rim id>` claim ids or `resolve()` change, `renderer/test/frontier.test.js` ("link into the Examiner
  Matrix") and `tests/test_frontier.py` will flag it.
* Public bundle (`qc/bundle.py`) does not attach the frontier yet. To add it, one line:
  `html = frontier.attach(instrument.render(...), REPORTS)`. The frontier holds no imagery.

## Files deliberately NOT touched

`qc/brief.py`, `qc/instrument.py`, `qc/contract.py`, `qc/field.py`, `qc/__main__.py`, `qc/bundle.py`,
`renderer/src/ui/Hero.jsx`, `renderer/src/ui/Panel.jsx`, `renderer/src/styles.css`, `renderer/src/data.js`,
`renderer/src/model/brief.js`, `renderer/vite.config.js`, `renderer/index.html`, `docs/REPRESENTATION_CONTRACT.md`,
`docs/DECISION_BRIEF.md`.
