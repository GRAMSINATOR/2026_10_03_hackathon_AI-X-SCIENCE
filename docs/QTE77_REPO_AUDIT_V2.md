# Audit V2: qte77's repo (`qte77/2026-10-03-london-ai-science-hack`) vs ours

Consolidated audit, 2026-10-03, against qte77's `main` at `24a77c2` (PRs #1–#10, all merged; no open PRs or issues).
Supersedes `docs/QTE77_REPO_AUDIT.md` (V1, at `11be16b`). Nothing was changed in qte77's repo. Read alongside
`docs/VISION_BRIEF_V2.MD` and `docs/JOB_SPLIT_V2.MD`.

**Bottom line.** qte77's repo is a well-engineered, live, agent-discoverable web shell with no science code. It is the
right online surface for our results. But its public identity (an eval bench for AI agents) contradicts our V2 thesis
(an epistemic acquisition controller), and that gap widens with every PR. Settle the identity first, then connect our
field file to their surface.

## 1. What qte77's project is

**Live:** "HackBench", FastAPI on Modal at <https://thismay52--hackbench-web.modal.run>. `/v1/health` reports the
deployed commit, verified as `24a77c2`.

| Area | What exists |
|---|---|
| People | Landing page at `/` (HTML, Open Graph, `SoftwareApplication` JSON-LD, canonical link) |
| Agents | `/llms.txt`, `/index.md` and `Accept: text/markdown` on `/`, A2A agent card (skill `evaluate-qc-verdict`), `/.well-known/agent-skills/index.json` + `SKILL.md` pinned by SHA-256, `/.well-known/ard.json`, `/.well-known/api-catalog` (RFC 9727), `/openapi.json`, RFC 8288 `Link` headers, markdown 404s |
| Crawlers | `/robots.txt` with per-agent rules, Content-Signal (`ai-train=no`) and a sitemap line; `/sitemap.xml` |
| CI (`ci.yml`) | ruff with security rules, `mypy --strict`, pytest, `pip-audit`, gitleaks, a guard against tracking TIFFs / `.env` / `private/` |
| Deploy (`deploy.yml`) | deploy after green CI on `main`; wait until the new commit is serving; then live e2e tests |
| Pre-registration (`preregister.yml`) | a `prereg-*` tag creates a server-timestamped GitHub release: proof the pipeline was frozen before the unseen batch was opened |

**Not built:** no image loading, segmentation, KPIs, statistics or data endpoints. Source is 4 modules (`api.py`,
`deploy.py`, `landing.py`, `discovery.py`), all serving the web surface.

**Planned (`docs/architecture.md`, unchanged since V1):** an eval bench for AI agents doing Polaron QC, aimed at the
Originator track. It specifies honeypots, a synthetic drift injector, agents under test, a detector chain, ECE/Brier
calibration, falsification checks and a leaderboard. A pipeline like ours appears only as the "reference pipeline
(honest, non-agent)" control.

**Public identity:** the landing page, `SKILL.md`, ARD entry and JSON-LD all say "check whether a science agent's QC
verdict is correct, honest (no reward hacking) and calibrated", and the sitemap invites indexing. None of it mentions
the acquisition controller.

**Fit with `JOB_SPLIT_V2`:** the hosting / connectivity half of qte77's lane is delivered, and done well. The scientific
half is not visible in the repo: the four literature requests in `docs/FIELD_MODEL.md` §7 are unanswered there, and there
are no candidates in the agreed HYPOTHESIS / FAILURE STATE / … / STATUS format.

## 2. Strongest intersections

### 2.1 Their surface + our representation contract (connectivity)

Our `field.json` (`epistemic-field/1`) is renderer-independent JSON with a schema and needs no Python engine. Their app
has a full discovery stack but no data. Joining them makes demo step 7 (agentic connectivity) a live call: a lab agent
discovers the skill, asks "what should I measure next for Batch_3?" and gets the ranked `actions[]`, each with
`triggered_by` and `trigger_facts`.

| Endpoint | Serves |
|---|---|
| `/v1/batches/{id}/field` | `reports/<batch>/field.json` or `fixtures/epistemic_field.<batch>.json` |
| `/batches/{id}` (HTML) | built R3F renderer; `qc/instrument.py` already injects the payload into `renderer/dist/index.html` |
| `/batches/{id}` (`Accept: text/markdown`) | `reports/<batch>/report.md`; their markdown negotiation already does this pattern |
| `SKILL.md` + agent card | a `recommend-next-capture` skill replacing `evaluate-qc-verdict` |

This matches the V2 stack position: lab agent → epistemic acquisition controller → instrument.

### 2.2 Pre-registration (time-critical)

`data/` holds only Batch_1–3, so the unseen batch has not been opened. A server-timestamped release before it lands is
cheap, strong evidence of honest uncertainty for the Polaron judges. It only counts if done first, and the current
uncommitted work (`renderer/`, `qc/instrument.py`, `qc/contract.py`, fixtures) should be committed so the frozen state is
complete.

### 2.3 Commit-stamped health

If our demo is served, `/v1/health` returning the commit ties the live system to the pre-registered commit. It is free
once 2.1 exists.

### 2.4 Known-answer material injection (the one real science contribution)

`qc/robustness.py` applies 10 *acquisition* perturbations: what the pipeline should ignore. qte77's drift-injector idea,
applied to the *material* (paste fine high-Z objects at +X% density; dilate pores by a known amount), gives an empirical
detection curve. That curve can be checked against the minimum detectable changes in `docs/CLAIMS.md` (e.g. ±5.6 per
1000 µm² for additive density, ±0.29 µm for additive D50). It makes demo step 2 (CHALLENGE THE DIAGNOSIS) measured rather
than asserted.

### 2.5 Number provenance for prose annotations

`docs/REPRESENTATION_CONTRACT.md` §3 admits our prose annotations "are not machine-checked against the numbers they
describe". Borrowing qte77's "every number maps to a source" rule: a test that extracts numbers from `statement` /
`rationale` / `reasons` and matches them to structured values in the same field. Estimated cost: about 30 minutes, in
`tests/test_contract.py`.

## 3. Similar-looking, but don't adopt

| qte77's idea | Why not |
|---|---|
| "Never use detector-channel presence or filenames as features" | Already satisfied. `qc/io.py` canonicalises detector names (ETD and SE → SE2), and the acquisition deviations that trigger REPEAT come from measured image statistics (`qc/field.py:148`), not detector names. |
| ECE / Brier calibration | Meaningless with 2–3 batches. Our simulation-calibrated thresholds (`null_calibration`) are the defensible version. |
| Falsification checks | Essentially our `leverage` / pivotal check (verdict with each micrograph removed). |
| Hash-chained run journal | Our pipeline is deterministic, and `trigger_facts` already ties each action to its evidence by JSON path. |
| Honeypots, agents under test, leaderboard, Devin | A second product and a second demo story. Conflicts with V2 "no parallel epistemologies", and none of it exists yet. |

## 4. Incompatibilities

- **Opposite product framings, now public.** In qte77's plan and live site, our engine is a control inside their eval
  bench. In ours, their work is the outer layer of our controller. Because the eval-bench framing is now indexed and
  machine-discoverable, this is no longer just an internal doc mismatch.
- **Don't move our engine into qte77's repo.** Their `mypy --strict` and ruff `ANN` rules would fail on almost all of
  `qc/`. Keep the field file as the boundary: bundle `fixtures/` (with `fixtures/assets/`) and
  `renderer/dist/index.html` into the Modal image.
- **Serve precomputed files, not the live engine.** Running the engine on Modal would need 1.7 GB of TIFFs in a volume,
  the approved reference build and scikit-image. Not worth it for the demo.
- **Tooling differs** (uv / pyproject / hatch vs `requirements.txt`; FastAPI vs Streamlit). Only a problem if the
  codebases are merged; the contract boundary avoids that.

## 5. Recommended next steps, in order

1. **Pre-register now.** Commit the current work (after adding `renderer/node_modules` to `.gitignore`), then add
   `preregister.yml` or run `gh release create prereg-v2 --prerelease` on our repo before the unseen batch arrives.
2. **Agree on one public identity** (GRAMSINATOR + qte77) before more discovery work. Then qte77 swaps `TAGLINE`,
   `WHEN_TO_USE` and the skill text in `landing.py` / `discovery.py` to the V2 controller, and re-points `README.md` /
   `docs/architecture.md`, or explicitly parks the eval bench.
3. **qte77 adds the data endpoints** in §2.1 and the `recommend-next-capture` skill (their lane).
4. **Material-injection test** (our lane): extend `qc/robustness.py` and report detected-vs-injected curves next to the
   claimed minimum detectable changes.
5. **Prose-number provenance test** in `tests/test_contract.py`.
6. **For GRAMSINATOR: Originator-track framing.** Our system already "knows when its measurements are insufficient":
   fragile ACCEPT flagged, validity gates, chemistry left unresolved. That could support an Originator entry without
   building any eval bench. Check the event rules on entering more than one track.

## 6. Housekeeping

`renderer/` has no `.gitignore`, so `git add renderer` would also commit `node_modules`. Add `renderer/node_modules` (and
`renderer/dist`, if build output should not be tracked) to `.gitignore` before committing.
