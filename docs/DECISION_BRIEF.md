# Governed decision brief (`decision-brief/1`)

```
scientific engine → epistemic-field/1 → decision-brief/1 (qc/brief.py) → hero → Examiner Control Matrix → raw evidence
```

The brief is the human decision layer. It contains **no science of its own**: it selects, groups and words facts that
already exist in the field.

* **Where it is produced.** `qc.brief.build(field)` creates it, and `qc.brief.check(brief, field)` validates it. The
  pipeline writes `reports/<batch>/brief.json` and refuses to render an incoherent brief.
* **Fixtures.** `python -m qc fixture` writes `fixtures/decision_brief.<batch>.json`.
* **The renderer.** It only displays the brief (`renderer/src/ui/Hero.jsx`). It navigates with `renderer/src/model/brief.js`.

## Schema

```
brief
  schema_version   "decision-brief/1"
  source           {schema_version, batch, reference}
  hero             {decision, data_support, surviving_evidence, limits, acquisition_policy}
                   each: {state, [qualifier | mode, sequence, later | footer], claims: [claim id, ...]}
  claims[]         see below
  governance       {rules[], suppressed[]: {candidate, reason, into?, cap?}}

claim
  id               e.g. evidence.M2060:additive_density, limit.scale:M2060, support.qc, action.repeat:1
  kind             decision | scope | support | surviving_evidence | evidence_summary | context | limit | action
  block            hero block it belongs to
  scope            what it is about (batch, entity, observation, rim target)
  status           the state (verdict, support status, survives/fails/none, consequential, action status)
  label            short heading (from field labels, ids, verbs or rim types)
  template         sentence template with {0}, {1}, ... placeholders: no literal data numbers
  values[]         {ref, value, fmt}: every number is a copied field value with its reference
  text             template rendered with values
  fact_template / fact_values / fact      optional secondary line, same rules
  details[]        merged supporting facts (shown in the proof trail), same rules
  role             content | pointer  (pointer: refers to another block, carries no numbers)
  group            redundancy group
  priority         selection order
  proof_refs[]     {collection, id, path}: the same addressing the field uses for trigger_facts
  action_refs[]    field action ids
  focus            the reference the examiner navigates to
  points_to[]      (pointer claims) the claims they refer to
  state_label      (support claims) default wording of the status
```

## States (each from an explicit engine flag; the wording template is chosen by the state)

| Block | Rule |
|---|---|
| Decision | `decision.verdict`. The fact line shows `p_batch` against `thresholds.alpha_reject`. The scope line names the approved reference, its micrograph count and the model. |
| Data support · QC | REFERENCE → not applicable · `validity_failed` → reacquire / invalid · INVESTIGATE → partial · all pivotal entities with `leverage.cause = min_independent_count` → **sufficient at minimum** · otherwise **sufficient** |
| Data support · attribution | no surviving deviation → not applicable · a consequential composition or scale rim on the surviving evidence → **change modality** · otherwise partial |
| Data support · lot prevalence | population rim consequential → **expansion needed** · otherwise sufficient |
| Data support · tested regime | Worst of three sub-states. Extent: a consequential observation-level spatial rim on the surviving evidence → expansion needed. Scale: a consequential scale rim → change modality. Acquisition: outside the tested range → reacquire; a tier-1 REPEAT exists → partial. Anything not triggered: **no expansion justified at tested scales**. |
| Surviving evidence | `summary.surviving`, ordered by exceedance (at most 2). The scrutiny, leverage and robustness facts are merged into one claim. Non-surviving deviations get one context line naming the most fundamental failure. |
| Limits | consequential rims only, ordered scale, composition, spatial, acquisition, validity, population (at most 5) |
| Acquisition policy | Tier-1 actions in rank order (at most 5). The mode comes from the first action's `addresses`: acquisition → VERIFY FIRST, scale / composition → CHANGE MODALITY, spatial extent → EXTEND, population or sampling → EXPAND SAMPLING. With no actions: **STOP**, "No current observation justifies more acquisition of this kind for this decision." |

"No expansion justified at tested scales" and STOP mean that nothing currently observed justifies more acquisition of
that kind *for the stated decision*. They never mean that nothing unknown exists.

## Governance (deterministic)

1. One content claim per redundancy group. Pointer claims refer to another block and carry no numbers.
   * Example: data support says "Attributing the surviving deviation needs a different measurement; see Limits" and
     does not repeat the scale and composition facts.
2. Decision-consequential evidence comes first. For M2060, four candidate facts become **one** evidence claim:
   * outside q99 (`reference_relation`);
   * tile-consistent and acquisition share (`scrutiny`);
   * verdict flips without it (`leverage`);
   * KPI robustness.

   They are recorded in `governance.suppressed` as merged.
3. Limits contain consequential rims only. Non-consequential rims are suppressed: they are visible in the examiner.
4. Policy covers tier-1 actions; lower tiers are listed in one line, not narrated.
5. `check()` enforces:
   * proof refs that resolve;
   * values equal to the field;
   * text equal to the template's rendering;
   * no digits in templates except the definitional envelope names 95% / 99% / q95 / q99;
   * no orphan hero claims;
   * no duplicated content groups;
   * the hero verdict equal to the field verdict;
   * survival and consequentiality matching the field;
   * a list of overstating words (proven, certain, impossible, validated, causes, chemical identity, universal,
     hidden variance, …).

   Tests: `tests/test_brief.py` (coherence, determinism, mutation tests, exact states, STOP case) and
   `renderer/test/model.test.js` (every click target resolves).

## Current states

| | Batch 3 | Batch 2 |
|---|---|---|
| Decision | **REJECT**: "Batch_3 crosses the QC rejection rule." batch p = 0.017 against α = 0.05 | **ACCEPT**: "Batch_2 stays inside the approved envelope." batch p = 1.000 against α = 0.05 |
| Data support | **SUFFICIENT FOR QC** · NOT FOR ATTRIBUTION OR PREVALENCE. 6 independent incoming micrographs; outside the 99% envelope and consistent across fields: M2060. Attribution: change modality · prevalence: expansion needed · regime: change modality. | **SUFFICIENT FOR QC** · AT THE MINIMUM · NOT FOR PREVALENCE. 3 independent incoming micrographs, the rule's minimum: without any one of them the decision becomes INVESTIGATE. Attribution: not applicable · prevalence: expansion needed · regime: no expansion justified at tested scales. |
| Surviving evidence | **M2060 · ADDITIVE DENSITY**: above the approved envelope and survives scrutiny. 34.4 vs approved 19.5 /1000 µm² · without M2060: ACCEPT (p = 0.448). 1 of 4 deviations survive; the M2068 D50, M2088 porosity and pore-size deviations did not. | **NO DEVIATION**: 0 of 3 independent micrographs leave the 95% envelope. |
| Limits | **SCALE · COMPOSITION · EXTENT · PREVALENCE**: fines peak at the 0.36 µm floor (2.3×); chemistry not measured; still outside the band at the start edge of the 698 µm section (extent not bounded); prevalence 1 of 6 (95% CI 0–64%). | **PREVALENCE**: 0 of 3 (95% CI 0–71%). |
| Acquisition policy | **VERIFY FIRST**: Repeat M2060 → resolve scale → chemistry (future) → extent → independent sections | **EXPAND SAMPLING**: independent sections |

Batch 2's three reference-linked micrographs (M2080, M2148, M2156) are excluded from independence, as the independence
correction requires.

## Optional compositor (LLM) seam

`qc.brief.compose(brief, compositor)` lets a compositor rewrite the approved wording. Its output is accepted only if
`check()` still passes: same states, same values, same proof refs. It may compress or choose phrasings. It may not decide,
infer or change the policy.

Assessment: little value now. The deterministic brief already reads cleanly, and an LLM adds a dependency, latency and
a verification burden for marginal phrasing gains. The seam exists if longer free-text summaries (reports, emails) are
ever wanted.
