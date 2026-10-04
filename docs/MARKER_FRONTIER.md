# Agentic Marker Frontier `marker-frontier/1`

> Parallax challenges whether the current way of seeing a dataset is sufficient. It maps new observational handles
> that can be tested now, the valuable handles that cannot yet be observed, and the measurement capabilities that
> would unlock them.

The Polaron QC pipeline is the working scientific instance. It remains responsible for the configured-reference
verdict, provenance, independence, robustness, support boundaries and immediate actions. The Agentic Marker Frontier
sits around that local decision loop and asks a broader question:

> **What additional useful ways of perceiving the current dataset should the agent investigate?**

```text
scientific model ──► epistemic-field/1 ──► five-lens Examiner + NEXT CAPTURE
                              │
                              ├─ structured limits / missing dimensions
research/*.json ──────────────┤
                              ▼
                       qc/frontier.py
              resolve → derive gates → rank opportunity
                              │
                              ▼
                       marker-frontier/1
        vortices → marker protocols → observability gaps
                     → capability pools → roadmap
                              │
                              ▼
               renderer/src/ui/MarkerFrontier.jsx
```

The five Examiner lenses remain the local loop:

1. **SIGNAL** — what changed;
2. **SCRUTINY** — whether the evidence survives acquisition and validity challenges;
3. **FIELD** — the uncertainty and support structure around it;
4. **OUTER RIM** — where justified inference stops;
5. **NEXT CAPTURE** — the next observation that resolves the current decision.

The global opportunity loop is: **observe → challenge → locate inquiry vortices → define candidate marker protocols →
test and rank current-data markers → identify observability gaps → pool them into capability attractors → acquire →
re-observe**.

## Contract objects

### Inquiry vortex

A vortex is a structured reason to inquire. It may be a sampling limit, unresolved spatial structure, resolution-floor
effect, acquisition sensitivity, missing identity or missing modality. It is not automatically a defect or anomaly.

`vortices[]` is derived from the typed `rims` and consequential `missing_dimensions` in every loaded
`epistemic-field/1`, plus explicitly declared general vocabulary gaps. Each vortex carries:

* stable `id`, plain `label`, `kind` and `statement`;
* whether it is instantiated by loaded data;
* `attention` and `consequential` without a probability score;
* source `evidence_refs` and current controller actions;
* reciprocal `marker_refs` and `capability_refs`.

Weak evidence is not promoted into a vortex to populate the interface. Unresolved non-general references fail
coherence checks.

### Marker protocol

A marker is **a defined protocol for perceiving a scientifically meaningful property of a system**. It is broader
than a scalar KPI or binary biomarker. The contract supports quantitative, qualitative and hybrid protocols with
representations such as scalar, distribution, relational graph, spatial field, topological descriptor,
morphological class, categorical state, multiscale signature and cross-marker relation.

Research bundles may provide:

* `name`, `marker_kind`, `representation`, `observable`, `scientific_question`;
* `scientific_definition`, `measurement_definition`, `why_relevant`;
* provisional `observation_family`, `support_model`, `uncertainty_adapter` and `reference_protocol`;
* `current_capture_compatible`, modalities, capability dependencies and capture requirements;
* existing-data test plan, implementation burden, confounds, failure modes and overlap;
* blindspot and decision references.

The builder derives:

* resolved inquiry-vortex and evidence links;
* the categorical gates and governed status;
* `observability` class and investigation wording;
* inspectable `ranking_factors`, deterministic `opportunity_rank` and `priority_band`;
* evidence, contradictions, counts, remaining work and provenance.

No paper automatically creates a marker. Literature may supply a technique or descriptor, but the marker remains a
candidate until its applicability, measurement definition, current-data support, robustness and information value
are investigated.

### Observability attractor

A capability case is rendered as an observability attractor when active inaccessible markers share that requirement.
It is a payload argument, not an equipment recommendation:

```text
candidate marker protocols
        → required information
        → shared observability requirement
        → scoped capability opportunity
```

Derived fields include `marker_pool`, `required_information`, reciprocal vortex links, current controller actions,
categorical `attractor_state`, `ranking_factors` and `attractor_rank`. The evidence drawer preserves substitutes,
integration burden, workflow requirements, literature and project evidence. A capability reaches critical mass only
through convergent credible marker demand, consequential value, non-substitutability and uncontested literature.

## Opportunity map

`opportunity_map` is renderer-independent and contains:

* `current_frontier`: at most three active marker opportunities;
* `candidate_markers.computable_now`;
* `candidate_markers.needs_targeted_capture` — same modality, missing scale or sampling;
* `candidate_markers.requires_new_observability`;
* `candidate_markers.set_aside` — negative results remain visible;
* `tooling_attractors`;
* a four-step roadmap: test current data, targeted capture, expand observability, re-observe;
* the explicit categorical ranking policy.

The ranking orders research attention, not scientific truth. It uses, in order: whether the case is live, whether it
addresses a decision-consequential vortex, observability class, existing-data test state, available evidence,
implementation burden and stable id. Each row explains its factors. There is no universal confidence, probability or
0–100 score; `check()` rejects score-like keys.

## Observability classes

| Class | Meaning | Typical next work |
|---|---|---|
| `computable_now` | Loaded data can support implementation or a defined test | implement, perturb and validate |
| `needs_targeted_capture` | Current modality is suitable, but required scale or sampling is absent | use the local acquisition controller |
| `requires_new_observability` | Required information or capability is absent | evaluate the aggregated capability payload |

This is separate from scientific value and admission state. A marker can be easy to compute and weakly grounded, or
scientifically promising and currently unobservable.

## Evidence and governance

Paper assessments attach to one target and one gate. They retain direction, directness, method strength,
transferability, claim, note, canonical link and independence group. One aligned source is partial support, not
consensus. Contradictory evidence stays visible.

Project records may be a `project_record`, `engine_fact` or `current_data_test`. Reviews select an eligible case but
cannot lift gates that evidence has not met. Fixture bundles may demonstrate rendering and contradiction handling but
never advance a gate or count as demand.

Marker gates remain categorical: scientific basis, measurability, robustness, inquiry value, non-redundancy and
promotion review. Capability gates remain categorical: marker pool, literature basis, inquiry value, no adequate
substitute and lab fit. Governed internal states remain available in provenance; the primary UI uses operational
phrasing such as `INVESTIGATING`, `TESTABLE` and `BUILDING PAYLOAD`.

## Seeded Polaron opportunities

The committed seed contains a small, explicit set of primary method papers. A paper supports candidate plausibility;
it does not assert implementation readiness, robustness or decision value.

* **Open-edge deviation phenotype** — qualitative categorical state already represented by registered profiles;
  distinguishes a bounded feature from a deviation that remains open at a captured edge.
* **Spatial correlation length** — quantitative scalar based on the implemented variogram support; reports supported
  range or a lower bound without extrapolating past capture.
* **Scale-dependent phase-fraction heterogeneity** — implemented raw and p(1−p)-normalised fluctuation curves with
  parent/support audits; still non-decision-driving.
* **Scale-dependent particle count overdispersion** — implemented equal-area mean count, number variance and Fano curves;
  Poisson is only a comparator.
* **Pair correlation, nearest-neighbour spacing, boundary morphology, full chord distributions, lineal-path probability
  and 2-D Minkowski morphology** — candidate protocols with provisional uncertainty adapters and explicit confounds.
* **Sub-floor fines size distribution** — quantitative distribution requiring the existing higher-magnification
  capture action.
* **High-Z phase elemental identity** and **phase-conditioned fines distribution** — require composition-sensitive
  data and pool under the EDS attractor.
* **3-D pore connectivity** — requires volumetric observation and remains exploratory.
* Pseudotime and the earlier, less auditable multiscale exponent keep their negative project results and remain set aside.

Orientation, lacunarity and persistent homology remain deferred. The current data have not established a directional
question for orientation; lacunarity overlaps the new scale curves; persistent homology would add novelty before basic
topology and segmentation sensitivity have been validated.

`fixtures/frontier/example.qte77.json` contains clearly marked synthetic evidence for ingestion and contradiction
tests. It changes display counts, never scientific state.

## Build and validation

Research ingestion validates against `schema/marker_research.v1.schema.json`. A producer sends definitions and
evidence, never states or scores. Conflicting scalar extensions are recorded and not overwritten.

```text
python -m qc.frontier fixtures
python -m qc.frontier build --fields … --bundles research --out …
cd renderer && npm test
```

`qc.frontier.check()` verifies referential integrity, deterministic ranking, observability partitions, reciprocal
vortex links, marker pools, roadmap references, state derivation, fixture isolation and the absence of opaque scores.
The renderer consumes only JSON; the opportunity graph remains usable by future planning and research agents.
