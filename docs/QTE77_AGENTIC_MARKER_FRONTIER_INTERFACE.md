# qte77 / HackBench Integration Guide — Parallax Agentic Marker Frontier

**Status:** integration brief for the hackathon build  
**Audience:** qte77 / HackBench implementation agent  
**Parallax role:** scientific / epistemic authority  
**HackBench role:** agent-native access, evaluation, falsification, discovery, and interoperability layer

---

## 1. Purpose

Parallax is no longer only a QC verdict engine.

The broader system treats a scientific dataset as something to **challenge**:

1. inspect what the current dataset can support;
2. locate structured inconsistencies, uncertainty, heterogeneity, blind spots, or unresolved relationships;
3. generate candidate new **markers** — new ways of perceiving or measuring the dataset;
4. rank which markers can be tested from the data already captured;
5. identify promising markers that require information the lab does not currently observe;
6. pool those inaccessible markers into **observability / tooling attractors**;
7. use those attractors to justify future acquisition or experimental capability;
8. feed new data back into the loop.

The agent-facing surface should make this opportunity map consumable by other scientific agents.

HackBench should expose, evaluate, and stress-test that map.

It should **not silently become a second scientific authority** that invents a conflicting marker ontology.

---

## 2. Core distinction: three different Parallax outputs

Do not conflate these.

### A. Current QC / decision output

Question:

> What does the current evidence justify for the present batch / decision?

Examples:

- ACCEPT / INVESTIGATE / REJECT
- current KPI deviations
- current uncertainty decomposition
- scrutiny
- evidence provenance

### B. `NEXT CAPTURE`

Question:

> What should be measured or done next to resolve the **current decision**?

Examples:

- repeat M2060 under approved acquisition settings;
- extend the mosaic;
- collect independent sections;
- use EDS to resolve current compositional ambiguity.

This is **local decision optimization**.

### C. `AGENTIC MARKER FRONTIER`

Question:

> What new observational handles are worth investigating, either from the current dataset or through new observability?

This is **representation / research opportunity search**.

It may suggest:

- edge roughness;
- relational spacing;
- pair correlation;
- lineal-path structure;
- chord lengths;
- topology/connectivity;
- anisotropy;
- other quantitative or qualitative descriptors.

These are not automatically decision-driving QC variables.

---

## 3. Definition of a marker

For this integration, a marker is approximately:

> **A defined protocol for perceiving a scientifically meaningful property of a system.**

A marker can be quantitative or qualitative.

Examples include:

- scalar measurements;
- distributions;
- spatial fields;
- relational geometry;
- graph / topology descriptors;
- morphological classes;
- categorical structural states;
- multiscale signatures;
- cross-marker relationships.

A marker is **not merely a number** and is **not automatically validated**.

A useful marker record may therefore contain:

- what is observed;
- how it is computed / recognized;
- physical support or scale;
- required modality/data;
- uncertainty adapter;
- evidence / literature basis;
- current validation status;
- relation to one or more unresolved dataset structures;
- ranking / priority rationale.

---

## 4. Marker-specific uncertainty is part of the object

Do not assume every marker should be evaluated with generic mean ± SD.

Parallax is moving toward:

> **marker → observation family → support model → uncertainty adapter → comparison protocol**

Examples:

| Marker family | Example uncertainty / support treatment |
|---|---|
| Bounded phase fraction | local-volume-fraction fluctuations, parent-aware resampling |
| Spatial counts | number variance, Fano/overdispersion, point-process methods |
| Particle spacing | nearest-neighbour / pair-correlation envelopes |
| Orientation | circular statistics |
| Boundary roughness | block/boundary bootstrap, multiscale support |
| Spatial profile | correlated functional profile, pointwise or simultaneous predictive envelope |
| Distribution / quantiles | parent-cluster bootstrap |
| Topological descriptor | parent + segmentation perturbation / topology-specific uncertainty |

HackBench should preserve and expose the adapter chosen by Parallax.

It should not flatten all marker uncertainty into a generic confidence score.

---

## 5. The broader opportunity model

The model may contain concepts equivalent to the following.

Names in the implementation may differ; **discover the actual current schema before coding against it**.

### 5.1 Inquiry vortex / challenge node

A structured reason to ask whether the current representation is incomplete.

Examples:

- volatile variance;
- unexplained spatial heterogeneity;
- disagreement between markers;
- acquisition sensitivity;
- scale truncation;
- unresolved phase identity;
- relational structure unexplained by present KPIs;
- insufficient spatial support;
- a whole-profile excursion outside an approved reference envelope.

A vortex does **not** mean “defect.”

It means:

> there may be useful information here that the present representation does not yet capture.

### 5.2 Current-data marker candidate

A marker that can plausibly be tested using data already present.

Question:

> Can we obtain a useful new observational handle without acquiring a new modality?

### 5.3 Observability-gap marker

A scientifically interesting marker that cannot be instantiated with current data.

Question:

> What information would we need in order to compute or validate this marker?

### 5.4 Tooling / observability attractor

A cluster of inaccessible but valuable markers that share a required acquisition capability.

Conceptually:

```text
candidate markers
    ↓
shared missing information
    ↓
required observability
    ↓
tool / modality attractor
```

This is a **payload justification** for acquisition expansion.

It is not a procurement recommendation.

---

## 6. Authority boundary

### Parallax core owns

- scientific derivation;
- marker definitions;
- QC states;
- uncertainty semantics;
- marker ranking inputs;
- evidence provenance;
- marker ↔ vortex relationships;
- current-data vs requires-new-observability classification;
- tooling-attractor membership;
- scientific scope / caveats.

### HackBench / qte77 owns

- agent discoverability;
- machine-readable access;
- schema validation;
- evaluation;
- falsification;
- stress testing;
- known-answer tests where possible;
- contradiction detection;
- reward-hacking tests;
- calibration checks;
- API / A2A / skill exposure;
- public-safe serialization;
- provenance visibility.

### HackBench must not

- silently redefine a marker;
- invent scientific evidence;
- invent literature support;
- promote a candidate marker to validated;
- convert a ranking into “probability this marker is true”;
- infer that a tooling attractor means “buy this instrument”;
- change a Parallax verdict;
- collapse scoped uncertainty into generic model confidence.

If HackBench computes an **evaluation-layer judgement**, label it explicitly as HackBench evaluation, not Parallax scientific state.

---

## 7. Integration strategy

The preferred integration direction is:

```text
PARALLAX SCIENTIFIC MODEL
        │
        ├── decision / evidence field
        │
        ├── next-capture actions
        │
        └── opportunity / marker map
                 │
                 ▼
        renderer-independent artifact
                 │
                 ▼
          HACKBENCH ADAPTER
                 │
        ┌────────┼──────────┐
        │        │          │
       REST    A2A       agent skill
        │        │          │
        └────────┼──────────┘
                 ▼
        agents / evaluators
```

HackBench should consume **renderer-independent scientific artifacts**, not scrape the Parallax UI.

Do not make Three.js / React / dashboard DOM a data dependency.

---

## 8. Discover the actual Parallax contract first

The Parallax opportunity-map implementation is being developed during the hackathon.

Before implementing the adapter:

1. inspect the current Parallax repository;
2. find the authoritative renderer-independent marker/opportunity representation;
3. read any associated schema / contract documentation;
4. identify actual emitted artifact paths;
5. inspect representative ACCEPT and REJECT outputs;
6. inspect the Agentic Marker Frontier UI only to understand presentation, not as the source of truth.

Possible artifact names may resemble:

- `opportunity_map.json`
- `marker_frontier.json`
- an extension of `field.json`
- another renderer-independent object

**Do not guess a path or schema because this document uses conceptual names.**

If no stable artifact exists yet, coordinate around the model object that feeds the renderer and avoid duplicating its logic in HackBench.

---

## 9. Minimum machine-readable semantics

Whatever the exact Parallax schema, the HackBench adapter should be able to recover the following concepts when present.

### Opportunity-map level

- schema/version;
- batch / subject identity;
- source decision/evidence artifact;
- generation/provenance information;
- list of inquiry vortices / challenge nodes;
- current marker frontier;
- broader candidate-marker set;
- observability-gap markers;
- tooling / observability attractors.

### Marker candidate

Prefer access to concepts equivalent to:

```json
{
  "id": "stable-marker-id",
  "label": "Human-readable marker name",
  "definition": "What this marker observes",
  "observation_family": "spatial_count_process",
  "status": "candidate",
  "computability": "current_data",
  "priority": null,
  "priority_factors": {},
  "support_model": {},
  "uncertainty_adapter": {},
  "source_vortices": [],
  "required_data": [],
  "required_modalities": [],
  "evidence_refs": [],
  "literature_refs": [],
  "related_markers": [],
  "caveats": []
}
```

This is an **illustrative semantic shape, not a schema to impose on Parallax**.

Use the actual fields emitted by Parallax.

### Tooling / observability attractor

Prefer access to concepts equivalent to:

```json
{
  "id": "stable-attractor-id",
  "capability": "composition-sensitive imaging",
  "unlocks_markers": [],
  "addresses_vortices": [],
  "why_current_data_is_insufficient": [],
  "evidence_refs": [],
  "literature_refs": [],
  "burden": null,
  "scope": null,
  "caveats": []
}
```

Again: adapt to Parallax; do not force Parallax to match this example.

---

## 10. Suggested HackBench API surface

If the current HackBench architecture permits it, add an agent-native read surface around the opportunity map.

Suggested semantics:

### `GET /v1/opportunity-map`

Returns the current renderer-independent opportunity map.

Useful query filters may include:

- batch;
- marker state;
- computable-now vs requires-new-observability;
- observation family;
- tooling attractor;
- source vortex.

Do not add filters unless there is real data behind them.

### `GET /v1/markers`

Compact marker index.

Each result should expose enough information for an agent to decide whether to inspect it further.

### `GET /v1/markers/{marker_id}`

Full marker record, including proof/evidence references.

### `GET /v1/tooling-attractors`

Aggregated observability-expansion opportunities.

### `GET /v1/tooling-attractors/{id}`

Full payload justification:

- marker cluster;
- unresolved structures;
- required observability;
- basis and caveats.

Exact routes are optional.

The key requirement is a clean agent-readable surface.

---

## 11. Suggested agent skills

HackBench currently exposes an `evaluate-qc-verdict` skill.

Do **not** overload that skill with marker research semantics.

Prefer one or more new skills such as:

### `inspect-marker-frontier`

Purpose:

> Retrieve and explain the ranked marker opportunities Parallax currently sees, while preserving their evidence state and scientific scope.

Input ideas:

- batch / dataset;
- maximum number of candidates;
- current-data only;
- include observability gaps;
- observation family filter.

Output:

- ranked candidates;
- what each would let the lab perceive;
- computability;
- uncertainty adapter;
- evidence basis;
- caveats;
- proof links.

### `inspect-observability-attractors`

Purpose:

> Show which clusters of inaccessible markers could justify a new measurement capability.

Output:

- capability;
- markers unlocked;
- challenge nodes addressed;
- current-data limitation;
- evidence basis;
- scope / burden / caveats.

### Optional later: `challenge-marker`

Purpose:

> Falsify or stress-test one Parallax marker opportunity without modifying the scientific source of truth.

This can test:

- weak literature basis;
- redundancy;
- missing required input;
- inappropriate uncertainty adapter;
- insufficient independent support;
- susceptibility to segmentation/acquisition perturbation.

If added, the result must remain an **evaluation-layer judgement**.

---

## 12. Evaluation opportunities for HackBench

This new surface creates excellent evaluation targets.

### 12.1 Provenance integrity

Every marker opportunity should be traceable to:

- current dataset structure;
- an explicit challenge/vortex;
- research/literature evidence;
- or a combination.

Test for orphan recommendations.

### 12.2 Unsupported opportunity test

Attempt to induce an agent to recommend a plausible-sounding marker that has no support.

Expected behavior:

> refuse to promote it as a Parallax candidate; identify it as a speculative suggestion if discussion is allowed.

### 12.3 Modality hallucination test

Attempt to make the agent claim that a marker is computable from BSE when it actually requires composition, depth, spectroscopy, etc.

Expected behavior:

> preserve required-modality constraints.

### 12.4 Ranking integrity

Changing presentation order must not silently alter scientific priority.

If Parallax emits ranking factors rather than an absolute score, preserve that distinction.

### 12.5 Candidate ≠ validated test

A highly ranked candidate must not be described as an established QC marker.

### 12.6 Tooling attractor ≠ purchase recommendation

The agent should say:

> “This capability would unlock these marker opportunities.”

not:

> “The lab should buy instrument X.”

unless another planning layer explicitly makes that decision.

### 12.7 Uncertainty-adapter integrity

Where a marker has a marker-specific statistical adapter, test that the agent does not substitute generic mean/SD language.

Examples:

- count marker → do not describe Fano / count-process evidence as a generic confidence interval;
- angular marker → do not use ordinary linear mean without justification;
- profile → distinguish pointwise from whole-profile envelope;
- bounded fraction → preserve scale/support semantics.

### 12.8 Sparse-evidence behavior

When support is small:

- preserve low-support state;
- do not synthesize certainty;
- do not hide missing independent parents.

---

## 13. Public deployment and data safety

The marker/opportunity API should be able to work in the same **derived-results-only / no-raw-images** public mode planned for the QC surface.

Prefer payloads containing:

- derived numeric descriptors;
- marker definitions;
- scientific states;
- provenance IDs;
- literature metadata;
- uncertainty metadata;
- tool/modality requirements.

Do not require public raw TIFF access.

Do not expose derived SEM imagery unless publication permission is explicitly settled.

If proof references point to unavailable private imagery, return a safe provenance stub rather than breaking the marker record.

---

## 14. Literature handling

Literature can suggest:

- a marker definition;
- an extraction method;
- an uncertainty/statistical adapter;
- a modality;
- a known scientific relationship.

But literature mention alone does not make a marker validated for this dataset.

Preserve stages such as:

```text
mentioned / discovered
        ↓
plausible for this dataset
        ↓
computable
        ↓
tested
        ↓
useful / non-redundant
        ↓
promoted
```

Exact labels should follow Parallax.

HackBench should expose the distinction and test that agents preserve it.

---

## 15. Interaction with `NEXT CAPTURE`

A marker opportunity may eventually influence acquisition.

But keep two pathways distinct.

### Immediate current-decision pathway

```text
current evidence
    ↓
current epistemic limit
    ↓
NEXT CAPTURE
    ↓
resolve current decision
```

### Broader opportunity pathway

```text
dataset challenge
    ↓
candidate markers
    ↓
observability gaps
    ↓
marker pools
    ↓
tooling / acquisition attractors
    ↓
future research roadmap
```

HackBench should not transform every Marker Frontier item into an immediate `NEXT CAPTURE` action.

---

## 16. Interaction with external science agents

The opportunity-map surface should be designed so that another agent — Claude, an automated lab planner, or a human-facing science agent — can ask:

- What are the most promising untested markers in this dataset?
- Which can be computed now?
- Which are qualitative versus quantitative?
- What uncertainty model applies to each?
- What unexplained structure motivated this candidate?
- Which candidate markers are redundant?
- What new modality would unlock the most currently inaccessible opportunities?
- Why is that modality being considered?
- What evidence or literature supports the recommendation?
- What would falsify the marker?
- What additional data would validate it?

The answers must be grounded in the Parallax artifact.

---

## 17. Recommended response discipline for agents

When an agent talks about the Marker Frontier, prefer this order:

1. **Marker / capability**
2. **What it would let us perceive**
3. **Why it is being considered**
4. **Can we test it now?**
5. **What uncertainty/support model applies?**
6. **Evidence / literature basis**
7. **What remains unresolved?**

Avoid leading with internal IDs or ontology terms.

---

## 18. Failure modes to avoid

Do not turn this into:

- a generic idea generator;
- a chatty research assistant;
- an equipment recommender;
- a second independent marker-ranking engine;
- a literature-summary endpoint;
- a UI scraper;
- a confidence-score generator;
- a way to smuggle speculative markers into the QC verdict.

The distinctive loop is:

> **structured dataset challenge → candidate perceptual handles → observability gaps → aggregated acquisition opportunities**

---

## 19. Recommended implementation sequence

1. Pull / inspect the latest Parallax core.
2. Locate the actual marker/opportunity contract.
3. Write a thin typed HackBench adapter.
4. Add schema validation.
5. Add public-safe serialization.
6. Add one read endpoint for the full opportunity map.
7. Add compact marker/tooling endpoints only if useful.
8. Add one agent skill: `inspect-marker-frontier`.
9. Add falsification/evaluation tests.
10. Update:
   - `openapi.json`;
   - A2A agent card;
   - agent-skills index;
   - `SKILL.md`;
   - `llms.txt`;
   - architecture docs.
11. Add end-to-end tests against the live agent-native surface.
12. Do not duplicate Parallax scientific calculations.

---

## 20. Minimum hackathon version

If time is extremely limited, do only this:

### Required

- consume the Parallax opportunity artifact;
- expose it safely via one API endpoint;
- expose one `inspect-marker-frontier` agent skill;
- preserve scientific/provenance semantics;
- add tests that candidate ≠ validated and observability attractor ≠ procurement recommendation.

### Nice to have

- tooling-attractor endpoint;
- challenge/falsification skill;
- marker-specific uncertainty-adapter validation;
- filtering/search;
- richer agent responses.

A correct thin adapter is better than a large parallel system.

---

## 21. Acceptance criterion

The integration is successful when an external agent can ask:

> **“What new ways of perceiving this dataset does Parallax think are worth investigating, and what would we need to observe them?”**

and HackBench can return a grounded, machine-readable answer that preserves:

- candidate status;
- scientific scope;
- evidence provenance;
- marker-specific uncertainty;
- current-data availability;
- observability gaps;
- tooling-attractor relationships;

without inventing new science or confusing the Marker Frontier with the current QC verdict.

---

## 22. One-sentence architecture rule

> **Parallax owns the scientific opportunity map; HackBench makes that map agent-native, testable, falsifiable, and interoperable.**
