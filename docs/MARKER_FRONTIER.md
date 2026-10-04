# Marker Frontier `marker-frontier/1`

> A scientific controller should not only decide what to measure next. It should accumulate evidence about what else
> becomes worth measuring, and when that evidence justifies expanding what the laboratory can observe.

```
epistemic-field/1 (rims, missing dimensions, actions)      research/*.json  (marker-research/1: the qte77 socket)
                     \                                       /
                      qc/frontier.py  merge -> resolve blindspots -> derive gates -> derive states -> check()
                                              |
                                  marker-frontier/1 (lab-level; fixtures/marker_frontier*.json)
                                              |
         renderer/src/ui/MarkerFrontier.jsx (two lanes · evidence rail · evidence tray), below the Examiner Matrix
```

Loop: **blindspot → candidate marker → evidence → measurability / confounds → (current capture: Marker Admission) or
(new capability: Capability Expansion) → expanded measurement vocabulary.**

## 1. Objects

**Marker Case.** A tracked, interpretable observable: a scalar, distribution, spatial pattern, morphology family,
cross-modality relation, acquisition signature or composition. It carries:

* inputs: `name`, `family`, `proposition`, `scientific_definition`, `measurement_definition`,
  `current_capture_compatible`, `required_modalities`, `required_capabilities`, `capture_requirements`,
  `existing_data_test` (a plan only), `blindspot_refs`, `decision_refs`, `why_relevant`, `known_confounds`
  (`controlled` + basis), `known_failure_modes`, `redundant_with` (+ increment);
* derived: `status`, `status_basis`, `lane`, `gates`, `rail`, `closes`, `closes_consequential`, `general_gaps`,
  `evidence`, `contradictory_evidence`, `counts`, `next` (what remains to advance), `qualifiers`, `review`.

**Capability Case.** A capability the lab should gain (EDS, Raman, tomography, a detector mode, …). Demand
accumulates across Marker Cases.

* inputs: `name`, `capability_type`, `why_current_workflow_cannot_resolve`, `blindspot_refs`, `decision_refs`,
  `existing_capability_substitutes` (`ruled_out` + basis), and `integration` (`requirements`, `burden`,
  `acquisition_cost_class`, `workflow_effect`, `data_interface_requirements`, `acceptable`);
* derived: `markers_unlocked`, `marker_demands`, `credible_demands`, `closes`, `closes_consequential`,
  `decisions_affected` (controller actions on those blindspots), plus the same derived block as a Marker Case.

**Paper Evidence.** Fields: `id`, `title`, `authors`, `year`, `venue`, `doi`, `url` (canonical; the default is
`https://doi.org/<doi>`), `independence_group`, `blindspot_refs`, `provenance` (retrieved_by / at, query, source_api)
and `assessments[]`. Each assessment bears on **one** target and **one** gate, because directness depends on the
question:

* `target`, `gate`, `direction` (SUPPORTIVE | CONTRADICTORY | NEUTRAL), `claim` (the exact proposition), `note` (why it
  matters);
* `directness`: direct / adjacent / indirect;
* `method_strength`: strong / moderate / weak;
* `transferability`: {material, modality, scale, task, process} ∈ same / similar / different / unknown.

The frontier derives `marker_refs` / `capability_refs` from the targets. It also derives a direction-free `strength`
and a display `label`, and keeps the underlying dimensions beside them.

**Record.** Internal evidence: a `project_record` (a file + locator, e.g. a research-log row), an `engine_fact` (a
reference into epistemic-field/1) or a `current_data_test`. Each record assessment has `target`, `gate`
(scientific_relevance | measurability | robustness | decision_value | non_redundancy) and `outcome`
(passed | failed | inconclusive).

**Review.** `{target, decision: admit | reject | recommend | integrated | defer, by, date}`. Selection is a person's
decision (JOB_SPLIT_V2 §1). It can never lift a case whose gates are not met; an ignored review is listed in
`governance.ignored`.

There is no overall score anywhere. `check()` rejects score-like keys (score, confidence, probability, likelihood,
credence), and the ingestion schema rejects them as property names.

## 2. Evidence label (paper assessment)

transferability: `low` if material or modality is different; `high` if both are same/similar and no axis is
different; otherwise `partial`.

relevance: direct + high/partial transferability = R1; adjacent + high = R2; direct + low or adjacent + partial = R3;
otherwise R4.

| method \ relevance | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| strong | STRONG DIRECT | STRONG TRANSFERABLE | SUPPORTING | INDIRECT |
| moderate | SUPPORTING | SUPPORTING | SUPPORTING | INDIRECT |
| weak | WEAK | WEAK | WEAK | WEAK |

The label shows CONTRADICTORY / NEUTRAL when the direction is not supportive. The strength is kept regardless.

## 3. Gates (categorical: met · partial · contested · failed · open)

**Literature gate** (marker `scientific_relevance`, capability `literature_convergence`). Counted papers only:

* **met**: one strong source (STRONG DIRECT or STRONG TRANSFERABLE) plus a second independent supporting source
  (distinct `independence_group`), uncontested;
* **contested**: a contradictory source at least as strong as the best support, or a counted project record that
  failed the proposition;
* **partial**: some support;
* **open**: no counted literature.

Marker gates:

| gate | rule |
|---|---|
| measurability | failed if `current_capture_compatible` is false or a record failed; met if a record passed; partial if compatible or inconclusive; else open |
| robustness | failed if a robustness record failed; contested by counted contradictory papers without a passing test; met if a test passed and every listed confound is controlled with evidence; partial on any test or control |
| blindspot_closure | failed if decision value was tested and failed; met if a ref resolves to a consequential rim / missing dimension (or decision value passed); partial for non-consequential or general refs |
| non_redundancy | failed / met by record; met by construction if it measures a dimension the field records as not acquired; partial if overlap is stated |
| admission | met = all five evidence gates met **and** a non-fixture `admit` review; partial = eligible, awaiting review |

Capability gates:

| gate | rule |
|---|---|
| marker_demand | met = ≥ 2 credible demands (active, non-fixture markers with scientific relevance met); partial = any active demand |
| consequential_closure | met if its own refs or its demanding markers' refs include a consequential blindspot |
| non_substitutability | failed if a substitute is shown adequate with evidence; met if every listed substitute is ruled out with evidence; partial if some are |
| integration_case | met = `acceptable: true` and a non-fixture `recommend` / `integrated` review; partial = drafted (burden stated) |

## 4. States (functions of the gates; research cannot assert them)

| Marker | rule (first match) |
|---|---|
| CONFOUNDED | robustness failed |
| REJECTED | review reject, decision value failed, or redundant |
| UNAVAILABLE | measurability failed → demand on the named capability (shown in the right lane) |
| ADMITTED | admission met (every evidence gate + review) |
| TRACKABLE | scientific relevance and measurability met |
| SUPPORTED | scientific relevance met |
| BUILDING | some evidence gate partly supported |
| CANDIDATE | links only (a blindspot link is a relationship, not evidence) |

ADMITTED means "credible relevance, a measurable definition observed under current acquisition, confound control,
non-redundant blindspot / decision value, selected by a person". It does not mean universally validated science.

| Capability | rule (first match) |
|---|---|
| REJECTED | review reject, or an adequate substitute |
| INTEGRATED | integrated review with an accepted integration case |
| RECOMMENDED | critical mass and integration case met |
| CRITICAL_MASS | demand met, literature met, consequential closure met, non-substitutability met |
| BUILDING_CASE | demand met, or one need that closes a consequential blindspot |
| WATCHING | otherwise |

Critical mass is stricter than "convergent demand + consequential blindspot + non-substitutability": it also needs
uncontested literature convergence. It is never "number of papers > N".

## 5. Blindspot closure

Bundles reference blindspots as `{batch, collection: rims | missing_dimensions, id}` (the same addressing as
decision-brief proof refs, plus the batch), or as `{general, label}` for a vocabulary gap that no loaded field
instantiates. Every rim of every loaded field (plus consequential missing dimensions) is indexed in
`blindspots[]`. Each entry carries the controller actions that already address it and `addressed_by` (the cases).
An unresolved, non-general ref is a violation.

`open_blindspots` lists consequential blindspots that no live, non-fixture case addresses. This is the pull on the
research agent, shown with what the controller does meanwhile (EXTEND, SECTIONS, …).

The frontier is lab-level: states do not change with the batch on screen. The renderer marks blindspots of the
current batch. A blindspot chip is clickable only when the decision brief already makes a claim about that limit
(`limit.<rim id>`, or a matching focus ref); the click opens that claim in the Examiner Matrix.

## 6. Ingestion contract (qte77)

* One file per research run in `research/` (env `QC_RESEARCH`). It must validate against
  `schema/marker_research.v1.schema.json`. Never edit another producer's bundle.
* `bundle.kind`: `research_agent` (qte77), `controller_seed`, or `fixture`.
* Cases may be new, or extend an existing id. A later bundle may only extend lists (`blindspot_refs`, substitutes,
  confounds, …) and fill unset scalars. A conflicting scalar is recorded in `governance.conflicts` and never
  overwritten. A fixture bundle cannot extend a real case.
* Papers attach to any case by `assessments[].target`; they appear in that case's tray automatically.
* A paper that is not fixture needs `doi` or an https `url`.
* A marker that current capture cannot observe must name `required_capabilities`. A missing capability case becomes a
  visible `derived_stub`.
* Do not send `status`, scores or confidences. Send evidence.

Rebuild: `python -m qc.frontier fixtures` (fixtures), or `python -m qc.frontier build --fields … --bundles research
--out …`. The app attaches the frontier over every `reports/<batch>/field.json` (`qc.frontier.attach`, which fails
open: a broken bundle never takes the decision surface down).

## 7. What is real and what is fixture

* `research/seed.controller.json` (real, no literature):
  * engine facts from epistemic-field/1 (rims `scale:M2060`, `composition:M2060`);
  * research-log rows #4–#7 and #11;
  * a `docs/CLAIMS.md` record.
* Its cases:
  * EDS = BUILDING CASE (one consequential need: composition of the M2060 fines; literature open);
  * sub-floor fines size distribution = BUILDING (closes `scale:M2060`; needs the controller's ZOOM acquisition);
  * pseudotime = CONFOUNDED (log #5);
  * multiscale heterogeneity = REJECTED (log #7);
  * 3-D pore connectivity → tomography = WATCHING (exploratory).
* `fixtures/frontier/example.qte77.json` is **FIXTURE**: synthetic placeholder papers (titles prefixed `FIXTURE ·`,
  no DOI, no link) and one candidate. It is used to show and test ingestion and contradiction rendering. By rule it
  changes counts, never gates or states (tested).

Tests: `tests/test_frontier.py` (socket, resolution, governance, fixture isolation, reproducibility, no research) and
`renderer/test/frontier.test.js` (view model). Visual QA: `python work/qa_frontier.py [integrated]` with
`npm run dev -- --port 5199`.
