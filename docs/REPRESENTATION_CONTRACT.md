# Representation contract `epistemic-field/1`

```
scientific model (qc.stats · qc.spatial · qc.robustness · qc.provenance)
        │  qc.field.build()
        ▼
reports/<batch>/field.json        ← the uncertainty field: renderer-independent epistemic state
        │  (JSON only; no Python engine needed)
        ▼
renderer(s): renderer/ = Evidence Instrument (React Three Fiber, primary; docs/RENDERER_INSTRUMENT.md) ·
             qc/hero.py = V1 exploratory/diagnostic renderer (legacy, parity checks) · tables · …
```

`epistemic-field/1` is the canonical contract for the **local scientific examination and decision loop**. It answers
what the loaded dataset supports, where that support stops, and which immediate acquisition action addresses the
current decision. It continues to drive SIGNAL, SCRUTINY, FIELD, OUTER RIM and NEXT CAPTURE.

The broader research-opportunity loop is a separate renderer-independent contract, `marker-frontier/1` (see
`docs/MARKER_FRONTIER.md`). It derives inquiry vortices from the field's typed limits, then represents candidate marker
protocols, current-data testability, observability gaps, capability pools and an acquisition roadmap. This separation
keeps representation search and tooling opportunity out of the validated QC decision object while preserving
reciprocal evidence references between them.

* Schema: `schema/epistemic_field.v1.schema.json` (JSON Schema 2020-12).
* Coherence rules that a schema cannot express live in `qc/contract.py:check`: referential integrity, status vs thresholds,
  scrutiny logic, shares summing to 1, leverage vs pivotal, action triggers resolvable, and no presentation vocabulary.
* Canonical fixtures: `fixtures/epistemic_field.Batch_3.json` (reject) and `.Batch_2.json` (accept) plus `fixtures/assets/`:
  BSE thumbnails and registered engine segmentation (`*_seg.png`, labels 0 pore / 1 matrix / 2 high-Z) at 8× downsampling.
  Regenerate with `python -m qc fixture reports/Batch_3`.
* Tests: `tests/test_contract.py` (schema, coherence, non-vacuity, reproducibility from the engine, renderer independence,
  no invented geometry) and `tests/test_field.py` (the preserved scientific claims).

## 1. Conceptual hierarchy

```
EpistemicField
├─ context              batch · reference_frame {id, explicit selection, support} · role · parent-micrograph unit · model
├─ quantity_scope       explicit intrinsic target paths vs reference-relative paths
├─ reference_frames[]   eligible/unavailable candidates · reasons · parent/KPI/spatial/acquisition support · selected
├─ reference_sensitivity all eligible frames evaluated together · intrinsic digest · per-frame verdict/support/means/spreads/
│                       spatial regimes · invariant and frame-dependent findings · why ranges · exploration guardrail
├─ decision             verdict · p_batch · tests (severity, count, Bonferroni) · null calibration · n_independent ·
│                       reference_linked[] · pivotal[] · thresholds · reasons (prose)
├─ dimensions[]         what can be (or could have been) measured
│   ├─ kind=kpi         unit (canonical) + display {unit, factor} · modalities · cross_checks ·
│   │                   uncertainty_model {observation_family, support_model, uncertainty_adapter,
│   │                   reference_protocol} ·
│   │                   robustness {cls, worst_perturbation, worst_shift, worst_shift_over_tile_sd} ·
│   │                   reference {mean, sd, sd_between, sd_tile, var_mean, n, mdc95_3tiles, tile_range} ·
│   │                   spatial_support {cls, scale_dependent_heterogeneity[], scale_model_sensitivity,
│   │                   window_variance aggregation audit, tile_excess (+CI), range_um, variogram} | null
│   └─ kind=missing     acquired=false · would_require[]                      (composition)
├─ entities[]           the statistical units (parent micrographs)
│                       fields[] · independence {reference_linked, also_in_batches} · geometry ·
│                       validity {measurable per family, reasons} ·
│                       acquisition {metrics, differs_from_approved[], outside_tested_range[]} ·
│                       leverage {verdict_without, p_without, flips, cause} | null (ref-linked) ·
│                       size_distribution {per-bin density vs reference, floor, excess_piled_at_floor}
├─ observations[]       entity × acquired dimension
│                       value · per_field{} · reference_relation {status, z, q95, q99, envelope95,
│                       approved_mean, exceedance_ratio, direction, beyond_reference_support} ·
│                       variance_shares {approved_material, spatial_sampling, baseline_support} ·
│                       scrutiny {outcome, robust_dimension, tile_consistent, fields_beyond_95, acquisition_share,
│                       failed[codes], conditional_on_untested_acquisition} · acquisition_explains_deviation · rims[]
├─ missing_dimensions[] entity × missing dimension: consequential · basis {dependent_observations, …}
├─ spatial_profiles[]   entity × spatial KPI: runs[] (own 0-based frame each; run_separation = "unknown") ·
│                       25-µm context columns · unsmoothed 100-µm local means · open_at_start/end ·
│                       parent-cluster reference_band · comparison_support · whole_profile_excursion
├─ rims[]               where support fades: {type, scope ∈ batch|entity|observation|dimension, target,
│                       consequential, basis (structured), statement (prose)}
├─ actions[]            ranked NEXT CAPTURE: verb · tier · addresses · status · cost · targets {observations,
│                       entities, dimensions} · triggered_by[rim ids] · trigger_facts[{collection,id,path}] ·
│                       effect {kind, …} | null · evidence / rationale (prose)
├─ provenance           fields[] {id, batch, fid, entity, width_um, height_um, px_nm} · edge_links[]
├─ summary              deviating[] · surviving[] · consequential_rims[]
└─ assets (fixtures)    field id → image asset
```

**Epistemic chain carried by the contract:** observation → reference relation → scrutiny outcome → rims (support
boundaries, typed and scoped) → actions (each pointing back through `triggered_by` and `trigger_facts`).

### Field classification

| Class | Members |
|---|---|
| Scientific / computed quantity | values, per_field, z, q95/q99, envelope95, exceedance_ratio, variance_shares, reference.{mean, sd, sd_between, sd_tile, var_mean, mdc95}, robustness shifts, spatial_support, size_distribution, profiles, prevalence, p-values, effects |
| Epistemic / support state | reference_relation.status, scrutiny.outcome + failed codes, conditional_on_untested_acquisition, acquisition_explains_deviation, beyond_reference_support, rims (type, scope, consequential), missing_dimensions.consequential, spatial_support.cls |
| Provenance / validity | entities.fields, independence, provenance.fields / edge_links, validity, acquisition deviations, run_separation |
| Decision / action | decision.*, leverage, actions.* |
| Annotation (human prose, non-normative) | statement, title, evidence, rationale, reasons, label, short_label, note, display |

## 2. Removed from the model (they were UI decisions)

| Was | Why it was UI | Now |
|---|---|---|
| a fake 60 µm gap between unconnected runs in profile x-coordinates | invented a physical distance for layout | each run has its own 0-based frame; `run_separation: "unknown"`; spacing is renderer-owned (`RUN_GAP_UM` in hero.py) |
| `dominant`, `reducible_share` | existed only for ring hue / width | renderer derives them from `variance_shares` |
| `dev` | named and shaped for "brightness" | `exceedance_ratio` = \|z\|/q95 (a statistic; the brightness mapping is in the renderer) |
| `acq_sensitive` (flicker flag) | merged two different facts | `entity.acquisition.outside_tested_range[]` and `observation.acquisition_explains_deviation`; "flicker" = renderer OR of both |
| composition as a cell in the KPI matrix | presupposed the "extra column" metaphor | `dimensions[kind=missing]` + `missing_dimensions[]` relevance per entity |
| formatted strings as the only form of acquisition deviations, gate reasons, rim bases, triggers | renderer would have to parse prose | structured `basis`, `acquisition.*[]`, `effect`, `trigger_facts`; prose kept beside them as annotation |
| row ordering (reference-linked rows last) | layout choice | entities are sorted by id; order carries no meaning (renderer sorts) |
| base64 thumbnails inside the field | renderer transport | `provenance.fields` + optional `assets` |
| `fines_brightness_u` | the name collided with presentation vocabulary | `fines_bse_intensity_u` (normalised BSE intensity, a physical signal) |

The marker-aware spatial descriptors do not enter the batch verdict. The configured QC verdicts and scrutiny rules are
unchanged. The support-matched local envelope still grounds open-edge acquisition actions, so a more explicit envelope
can legitimately change which captured edge is reported as open.

## 3. Still coupled (honest list)

* **Analysis-resolution parameters**: 25 µm context columns and unsmoothed 100 µm moving local means are analysis
  choices. Only the 100 µm statistic is compared with the 100 µm parent-bootstrap envelope. The envelope is descriptive,
  not coverage-calibrated, and exposes its 5–6-parent support, bootstrap endpoint sensitivity and the former flattened
  mean ± 1.96 window-SD population-spread audit.
* **Action ranking** (tier + verb order) is a policy encoded in `qc/field.py`. It is semantic (decision priority), but a
  renderer that shows "rank 1" inherits our policy.
* **Prose annotations** are English and partially redundant with structured fields. Renderers may ignore them, but they
  are not machine-checked against the numbers they describe (except via tests on a few key values).
* **`display.factor` / `short_label`** are naming and units conventions in the model layer; they are not visual
  instructions, but they are presentation-adjacent.
* **The V1 renderer** still hard-codes its own presentation constants and the 5-step narrative, by design. It reads no
  engine code (enforced by test).

## 4. Can a React Three Fiber renderer consume it unchanged?

**Yes.** Load `fixtures/epistemic_field.Batch_3.json` (or any `reports/<batch>/field.json`) and the `assets` images. Every
rule outcome needed for display is explicit. A renderer only maps meaning to form (e.g. `exceedance_ratio` → emission,
`scrutiny.outcome` → material solidity, `variance_shares` → geometry, `rims[].type/scope` → boundary objects,
`actions[].targets/triggered_by` → links). It never recomputes statistics. Profiles give per-run coordinates in µm, and
`provenance.fields` gives physical tile sizes for texture placement. Nothing requires Python.

## 5. Unresolved representational questions (deliberately not decided here)

Each is a place where choosing a visual metaphor would silently choose an ontology.

1. **Primary space: statistical unit or physical space?** The grid makes the micrograph × KPI matrix primary. A
   spatial / 3-D scene would make the stitched cross-section primary. They imply different things about where evidence
   "lives".
2. **Is a missing dimension the same kind of thing as a measured one?** Rendering composition as one more column (or one
   more axis) implies commensurability with KPIs. The contract keeps it as a separate kind.
3. **Is there one outer rim or several?** Rims have 4 scopes and 6 types with no common metric (spatial extent, pixel floor,
   population size and chemistry are incommensurable). A single hull, surface or "fog boundary" would assert a common space
   that the data does not define.
4. **Continuous vs categorical states.** z and exceedance are continuous; status and scrutiny are rule thresholds. A
   continuous visual (glow) suggests the thresholds are arbitrary; a categorical one (solid / hatched) suggests they are
   physical.
5. **Comparability of uncertainty across dimensions.** `variance_shares` are proportions within one observation. Mapping
   them to a common magnitude (height, size, opacity) across KPIs invents a cross-KPI uncertainty scale.
6. **Status of reference-linked entities.** Are they part of the batch (dimmed), part of the reference, or a third
   category? They are physically approved material inside an incoming folder.
7. **Locality of actions.** Some actions are local (EXTEND at a section edge, ZOOM on one micrograph), some are batch-level
   (SECTIONS, BASELINE), some are a new modality (EDS). Placing actions in space asserts locality; listing them asserts
   they are commensurable choices.
8. **Unknown separation between runs.** Disjoint runs of one micrograph have an unknown physical gap. Any layout chooses a
   distance or an order.
9. **Narrative order vs epistemic order.** SIGNAL → SCRUTINY → FIELD → RIM → CAPTURE is a story. The contract has no
   temporal or reasoning-order field. Should a "reasoning trace" become part of the state?
10. **Batch: container or entity?** Prevalence and the batch decision belong to the batch, which the contract treats as
    context. A renderer that gives the batch its own object makes it an entity with state.

## 6. Reference role (additive extension, `docs/REFERENCE_SELF_AUDIT.md`)

These keys are present only when the field is the reference auditing itself, so incoming fields are unchanged:
* `context.role = "reference"`.
* `decision.verdict = "REFERENCE"` with `decision.p_batch = null` and a `decision.self_audit` block: the method, parents,
  frame size, departures and chance calibration.
* `entities[].reference_influence`: the shift of the reference mean when the parent is left out, also in MDC units.
* `observations[].reference_relation.frame = "leave_one_out"` and `frame_n`.

`contract.check` enforces three rules: a reference field has no leverage, no reference-linked entity, no batch p, and
every measurable observation in its own leave-one-out frame; REFERENCE never appears without the role; incoming fields
are unaffected.
