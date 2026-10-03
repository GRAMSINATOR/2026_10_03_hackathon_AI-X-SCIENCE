# JOB SPLIT V2

## Purpose

Keep the hackathon work deliberately asymmetric and prevent duplicated high-cost exploration.

The canonical product direction is defined in:

- `docs/VISION_BRIEF_V2.MD`
- `docs/RESSOURCES.MD`

There are three roles:

> **Guilhem decides what the product is.**  
> **Claude turns current knowledge into the product.**  
> **qte77 expands the scientific and external measurement space.**

Everything feeds the same canonical object: the **uncertainty field** and the acquisition decisions derived from it.

---

# 1. Guilhem — product direction, selection and demo coherence

Guilhem owns:

- product thesis;
- priority;
- what gets cut;
- what the interface privileges;
- what counts as genuinely special;
- whether a qte77 finding reaches critical mass;
- final UX framing;
- final demo story.

Guilhem should spend attention on **selection, coherence and consequence**, not on exhaustive paper search, infrastructure or low-level implementation.

Primary question:

> **Does this make the epistemic acquisition controller clearer, more defensible, or more useful?**

If not, it is probably scope.

---

# 2. Claude — convergent product / implementation agent

Claude owns the **coherent centre of the product**.

Its job is to turn the current evidence and V2 vision into the strongest working instrument possible without repeatedly reopening the thesis.

Claude is now a **convergence engine**, not the broad exploration engine.

## Claude owns

### A. Uncertainty-controller core

- formalise the minimum defensible uncertainty field;
- model the fading outer rim from quantities we can actually support;
- distinguish observed variance from acquisition / nuisance variance;
- represent sampling and baseline-support limits;
- reason about spatial scale and coherent capture where defensible;
- derive blindspot classes;
- derive NEXT CAPTURE recommendations from the same model;
- keep recommendations auditable rather than decorative.

### B. Product / UX

- Evidence Field / Launchpad-style hero interaction;
- MATERIAL / UNCERTAINTY / OUTER RIM / NEXT CAPTURE / EVIDENCE SURVIVAL views;
- visual causality;
- compact explanation of why a recommended acquisition follows from the evidence;
- integration of QC proof beneath the hero surface.

### C. Existing QC proof layer

Preserve and harden:

- provenance reconstruction;
- robust KPI selection;
- perturbation testing;
- baseline comparison;
- ACCEPT / INVESTIGATE / REJECT;
- evidence trace;
- hidden-batch path.

### D. Integration

Claude consumes qte77 outputs only when they:

- invalidate an assumption already used;
- materially improve the uncertainty field;
- materially change NEXT CAPTURE;
- provide a testable new inference dimension;
- or add a high-value external measurement / dataset.

## Claude should not spend expensive reasoning on

- broad paper search;
- technology catalogues;
- speculative instrumentation;
- generic API discovery;
- hosting;
- deployment plumbing;
- broad external-data sourcing;
- repeated re-derivation of the product thesis;
- low-value cosmetic refactors.

Expensive Claude reasoning should end in:

- a formal decision;
- a model;
- working code;
- a verified correction;
- or a material demo improvement.

---

# 3. qte77 — scientific expansion + external connectivity

qte77 owns the **expanding edge of the system**.

He should work deliberately perpendicular to Claude.

His role has two connected halves:

1. **scientific adversarial expansion**;
2. **hosting, APIs, connectivity and external data / measurement sourcing**.

The common principle is:

> **Find what the current system cannot see or reach, and identify the scientifically or technically justified way to extend it.**

---

## 3A. Scientific adversarial expansion

qte77 should challenge the current uncertainty model from outside it.

Questions:

- What consequential variance source are we not modelling?
- Where is the outer rim falsely narrow?
- What structure may already exist in the SEM data but be invisible to our current features?
- What scientifically grounded descriptor or proxy could expose it?
- What important uncertainty cannot be resolved from the current dataset?
- What new measurement could resolve it?
- Does that measurement unlock enough orthogonal information to justify itself?

### Output class A — inference extensions from existing data

Examples:

- spatial statistics;
- morphology descriptors;
- topology;
- texture;
- clustering;
- correlation length;
- scale-dependent measures;
- cross-detector relationships;
- physical proxies;
- new combinations of existing measurements.

These should be tested on the current data where possible.

### Output class B — acquisition / parallel-data extensions

Examples:

- larger coherent SEM mosaics;
- different magnification;
- controlled repeat acquisition;
- adjacent sections;
- EDS;
- tomography;
- alternative microscopy modes;
- process telemetry;
- composition data;
- electrochemical or mechanical measurements;
- other scientifically justified parallel datasets.

A new measurement is not valuable because it is interesting.

It must correspond to a **failure state that matters** and reach **critical mass of unlocked value**.

---

## 3B. Hosting, APIs, connectivity and external sourcing

qte77 owns anything where the product needs to reach beyond the local core.

This includes:

### Hosting / deployment

- choose the lightest reliable hosting path;
- deploy the demo;
- handle environment / secrets / service configuration;
- ensure the app is reachable and stable;
- own deployment debugging so Claude does not burn product tokens on it.

### API integration

- external scientific APIs;
- literature / paper retrieval APIs;
- model APIs needed by the agentic research layer;
- remote data services;
- future instrument-control APIs where useful as an architectural demonstration;
- any service boundary required for larger connectivity.

### External data sourcing

- identify credible parallel datasets;
- locate accessible sources;
- assess licensing / accessibility quickly;
- determine whether data can actually be pulled into the demo;
- avoid adding data merely because it exists.

### Connectivity architecture

- define how the acquisition controller would connect to:
  - scientific agents;
  - microscopy-control systems;
  - external analysis services;
  - literature / research agents;
  - external datasets;
  - future instrument APIs.

For the hackathon, this should stay **thin and demonstrable**, not become a platform rewrite.

qte77 owns the external edge; Claude owns the product centre.

---

# 4. qte77 acceptance gate

A research lead, API, dataset or new technology should enter the product only if it does at least one of the following:

- reveals meaningful variance the current model misses;
- explains variance we already observe;
- proves the current outer rim should be wider;
- shrinks a consequential blindspot;
- distinguishes nuisance from material signal;
- changes the highest-value next acquisition;
- enables a measurement the controller genuinely needs;
- introduces a parallel dataset with enough orthogonal information gain to justify its acquisition burden;
- materially improves the demo's credibility or future agentic-lab connectivity.

Otherwise:

**park it.**

---

# 5. qte77 output format

Do not send Claude large undifferentiated research dumps.

Each scientific candidate should be compressed into:

## HYPOTHESIS
What might the current model be missing?

## FAILURE STATE
Which consequential uncertainty does this correspond to?

## SCIENTIFIC EVIDENCE
What does the literature support?

## CURRENT-DATA TEST
Can this be tested from the current dataset?

## OUTER-RIM EFFECT
Would it widen, shrink or reshape the uncertainty field?

## NEXT MEASUREMENT
If the current dataset cannot resolve it, what observation would?

## VALUE / CRITICAL MASS
Why is it worth adopting relative to cost?

## STATUS
**REJECT / TEST NOW / FUTURE CAPTURE / HIGH-VALUE NEW DATASET**

For APIs / external sources, add:

## ACCESS
Can we actually use it now?

## INTEGRATION COST
What does it take to connect?

## DEMO VALUE
Does it materially help the hackathon demo or only the future architecture?

Claude should primarily consume:

- **TEST NOW**;
- **HIGH-VALUE NEW DATASET**;
- assumption-invalidating findings;
- ready-to-use external integrations that materially support the product.

---

# 6. Shared architecture

## Production loop

**scientific objective → uncertainty field → outer rim → dominant blindspot → NEXT CAPTURE → instrument / acquisition → new data → updated field**

## Scientific expansion loop

**failure state → missing information → paper / agentic research → candidate new observable or measurement → test → update uncertainty field / action vocabulary**

## Connectivity loop

**required measurement or external capability → API / dataset / service discovery → integration → controller can now reach it**

These are not three separate products.

They are three ways of improving the same measurement-policy controller.

---

# 7. Token allocation

## Claude — convergence-heavy

Spend high reasoning on:

- uncertainty-field formalisation;
- outer-rim logic;
- difficult statistical decisions;
- hero UX architecture;
- integration of proven qte77 findings;
- implementation;
- testing;
- demo hardening.

Use cheaper / lower effort for:

- routine refactors;
- styling passes;
- boilerplate;
- mechanical tests;
- documentation cleanup.

## qte77 — exploration-heavy

Use the large budget aggressively for:

- literature;
- cross-sectional audits;
- competing hypotheses;
- spatial / variance methods;
- new candidate observables;
- alternate measurement technologies;
- API / external-data discovery;
- external connectivity;
- failed branches.

High failure rate is acceptable here.

## Guilhem — routing and selection

Guilhem decides when exploration becomes product.

The useful mental model is:

> **Claude compresses. qte77 expands. Guilhem decides where expansion becomes compression.**

---

# 8. Execution phases

## Phase 1 — architecture freeze

### Claude
- audit current code against V2;
- define the smallest defensible uncertainty-field / outer-rim implementation;
- specify exactly what drives each visual state;
- identify what is real computation versus future recommendation.

### qte77
- begin cross-sectional scientific audits;
- test spatial / scale methods;
- investigate missing variance dimensions;
- inspect relevant active-acquisition frameworks;
- choose hosting / deployment path;
- identify any immediately useful APIs or external data.

### Guilhem
- approve the central model;
- cut anything that creates parallel epistemologies;
- freeze the demo's hero story.

---

## Phase 2 — parallel build

### Claude
- implement Evidence Field;
- implement outer-rim representation;
- implement a small set of defensible NEXT CAPTURE decisions;
- preserve the QC proof layer;
- wire the demo flow.

### qte77
- continue scientific exploration;
- return only gated candidates;
- deploy / host;
- wire external services where useful;
- source parallel data only if it passes the critical-mass gate.

---

## Phase 3 — integration freeze

Stop broad conceptual invention.

Integrate only:

- assumption-breaking findings;
- clearly useful new observables;
- clearly defensible acquisition recommendations;
- connectivity required for the demo;
- deployment fixes.

Claude switches to:

**test → simplify → make causal → make legible → harden**

qte77 shifts toward:

**deployment → APIs → external connectivity → final research validation**

Guilhem becomes increasingly ruthless about scope.

---

## Phase 4 — demo hardening

No new frameworks.

No broad new papers.

No speculative modalities.

The demo should tell one story:

1. **Here is the material.**
2. **Here is the QC diagnosis.**
3. **Here is which evidence survives scrutiny.**
4. **Here is where the dataset stops supporting us.**
5. **Here is why that blindspot exists.**
6. **Here is what the microscope should measure next.**
7. **Here is how the scientific-agent layer can expand the controller's measurement vocabulary when the current sensing regime is insufficient.**

---

# 9. Final operating rule

> **Claude builds the strongest coherent controller from what we currently know. qte77 searches for scientifically grounded reasons why that knowledge or connectivity is incomplete and owns the external edge. Guilhem decides what crosses into the product.**

No duplicated exploration.

No parallel epistemologies.

No infrastructure work stealing Claude's product tokens.

One uncertainty field. One controller. One demo story.
