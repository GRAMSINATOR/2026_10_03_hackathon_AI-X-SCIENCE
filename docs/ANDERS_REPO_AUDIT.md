# Audit: Anders' repo (`qte77/2026-10-03-london-ai-science-hack`) vs ours

Exploratory audit, 2026-10-03, against Anders' `main` at `11be16b`. Nothing was changed in either repo. Read alongside
`docs/VISION_BRIEF_V2.MD` and `docs/JOB_SPLIT_V2.MD`.

**Bottom line.** Anders' repo is a hosted web shell with no science code. It meets ours most usefully as the online
surface for our results, plus two credibility mechanisms worth borrowing. Its written architecture describes a different
product, and adopting that would split our thesis.

## 1. What Anders' project actually is

**Built and live:** "HackBench", a FastAPI app on Modal at <https://thismay52--hackbench-web.modal.run> (`/v1/health`
and the agent card were verified to respond).

| Component | What |
|---|---|
| Agent-native discovery | `/llms.txt`, `/robots.txt` with a Content-Signal line, A2A agent card (one skill: `evaluate-qc-verdict`), `/openapi.json`, `/v1/health` |
| CI (`ci.yml`) | ruff with security rules, `mypy --strict`, pytest, `pip-audit`, gitleaks, a guard against tracking TIFFs / `.env` / `private/` |
| Deploy (`deploy.yml`) | deploy to Modal after green CI on `main`, then e2e tests against the live URL |
| Pre-registration (`preregister.yml`) | a `prereg-*` tag creates a GitHub release with a server timestamp: proof the pipeline was frozen before the unseen batch was opened |

**Not built:** no image loading, segmentation, KPIs or statistics. The source is 2 files (`src/hackbench/api.py`,
`src/hackbench/deploy.py`).

**Planned (`docs/architecture.md`):** a different product, aimed at the Originator track ("agents that know when they're
wrong"): an eval bench for AI agents doing Polaron QC. It specifies honeypots (decoy labels, channel/filename shortcuts), a
synthetic drift injector with known ground truth, agents under test (Claude, Devin, an open model), a detector chain
(trip-wires, re-scoring, provenance, LLM judge), ECE/Brier calibration, falsification checks and a leaderboard. Our kind
of pipeline appears there only as the "reference pipeline (honest, non-agent)" control.

**Fit with `JOB_SPLIT_V2`:** Anders' lane is scientific expansion plus hosting/connectivity. The hosting half is delivered
and done well. Nothing in the repo covers the scientific half: the four literature requests in `docs/FIELD_MODEL.md` §7
are unanswered there, and there are no candidates in the agreed HYPOTHESIS / FAILURE STATE / … / STATUS format.

## 2. Strongest intersections

### 2.1 Hosted shell + our representation contract (connectivity)

Our `field.json` (`epistemic-field/1`) is renderer-independent JSON with a schema. It needs no Python engine and was
designed for any consumer. Anders' app has endpoints but no data; our engine has data but no web interface. Joining them
makes demo step 7 (agentic connectivity) a live call: a lab agent asks "what should I measure next for Batch_3?" and gets
the ranked `actions[]` back, each with `triggered_by` and `trigger_facts`.

Concretely:
- `/v1/batches/{id}/field` → `reports/<batch>/field.json` (or `fixtures/epistemic_field.<batch>.json`);
- `/batches/{id}` → the built R3F renderer (`qc/instrument.py` already injects the payload into `renderer/dist/index.html`);
- `/batches/{id}.md` → `reports/<batch>/report.md` (matches Anders' planned "*.md twins");
- agent-card skill changed from `evaluate-qc-verdict` to something like `recommend-next-capture`.

This matches the V2 stack position: lab agent → epistemic acquisition controller → instrument.

### 2.2 Pre-registration (time-critical)

`data/` holds only Batch_1–3, so the unseen batch has not been opened yet. A server-timestamped release taken before it
lands is cheap, strong evidence of honest uncertainty for the Polaron judges. It only counts if done before the batch
arrives, and `renderer/` (currently untracked) should be committed first so the frozen state is complete.

### 2.3 Known-answer material injection (the one real science contribution)

`qc/robustness.py` applies 10 *acquisition* perturbations: what the pipeline should ignore. Anders' drift injector
idea, applied to the *material* instead (paste fine high-Z objects at +X% density; dilate pores by a known amount), gives
an empirical detection curve. That curve can be checked against the minimum detectable changes claimed in
`docs/CLAIMS.md` (e.g. ±5.6 per 1000 µm² for additive density, ±0.29 µm for additive D50) and makes demo step 2
(CHALLENGE THE DIAGNOSIS) measured rather than asserted.

### 2.4 Number provenance for prose annotations

Anders' plan requires every reported number to map to a logged source. `docs/REPRESENTATION_CONTRACT.md` §3 admits our
prose annotations "are not machine-checked against the numbers they describe". A test that extracts numbers from
`statement` / `rationale` / `reasons` and matches them to structured values in the same field would close that gap.
Estimated cost: about 30 minutes, in `tests/test_contract.py`.

## 3. Similar-looking, but don't adopt

| Anders' idea | Why not |
|---|---|
| "Never use detector-channel presence or filenames as features" | Already satisfied. `qc/io.py` canonicalises detector names (ETD and SE → SE2), and the acquisition deviations that trigger REPEAT come from measured image statistics (`acquisition_deviations`, `qc/field.py:148`), not detector names. |
| ECE / Brier calibration | Meaningless with 2–3 batches. Our simulation-calibrated thresholds (`null_calibration`) are the defensible version. |
| Falsification ("does the stated counterexample flip the verdict?") | Essentially our `leverage` / pivotal check (verdict with each micrograph removed). |
| Hash-chained run journal | Our pipeline is deterministic, and `trigger_facts` already ties each action to its evidence by JSON path. |
| Honeypots, agents under test, leaderboard, Devin | A second product and a second demo story. Conflicts with V2 "no parallel epistemologies", and none of it exists yet. |

## 4. Incompatibilities

- **Opposite product framings.** In Anders' plan our engine is a control inside their eval bench; in ours their work is
  the outer layer of our controller. Guilhem needs to settle this explicitly, or the repos will keep diverging.
- **Don't move our engine into Anders' repo.** Their `mypy --strict` and ruff `ANN` rules would fail on almost all of
  `qc/`. Keep the field file as the boundary: bundle `fixtures/` (and `fixtures/assets/`) plus `renderer/dist/index.html`
  into the Modal image.
- **Serve precomputed files, not the live engine.** Running the full engine on Modal would need 1.7 GB of TIFFs in a
  volume, the approved reference build and scikit-image. Not worth it for the demo.
- **Tooling differs** (uv / pyproject / hatch vs `requirements.txt`; FastAPI vs Streamlit). Only a problem if the codebases
  are merged; the contract boundary avoids that.

## 5. Recommended next steps, in order

1. **Pre-register now.** Commit `renderer/`, then add `preregister.yml` or run
   `gh release create prereg-v2 --prerelease` on our repo before the unseen batch arrives.
2. **Anders wires their app to our field file** (their lane): field, verdict, report and renderer endpoints, plus a
   next-capture skill in the agent card. They re-point their README / architecture doc to V2, or confirm the eval-bench
   plan is parked.
3. **Material-injection test** (our lane): extend `qc/robustness.py` and report detected-vs-injected curves next to the
   claimed minimum detectable changes.
4. **Prose-number provenance test** in `tests/test_contract.py`.
5. **For Guilhem: Originator-track framing.** Our system already "knows when its measurements are insufficient": fragile
   ACCEPT flagged, validity gates, chemistry left unresolved. That could support an Originator entry without building any
   eval bench. Check the event rules on entering more than one track.

## 6. Housekeeping found during the audit

`renderer/` has no `.gitignore`, so `git add renderer` would also commit `node_modules`. Add `renderer/node_modules` (and
`renderer/dist`, if build output should not be tracked) to `.gitignore` before committing.
