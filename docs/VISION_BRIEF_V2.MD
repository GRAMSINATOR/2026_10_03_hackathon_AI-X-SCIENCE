# VISION BRIEF V2

## Product category

We are building a **dataset-challenge and observability-planning layer for agentic microscopy**.

The system sits between scientific intent and instrument execution.

A higher-level scientific agent may know the objective.

The microscope may already know how to move, image, switch detector, change magnification or trigger another measurement.

Our layer asks two connected questions:

> **Given what we currently know, what should the instrument measure next — and why?**

> **Is the current way of perceiving this dataset sufficient, and what new observational handles are worth developing?**

Polaron's battery-electrode QC challenge is the proving ground.

It gives us a concrete diagnostic problem, real microscopy, a working QC engine and a reason to prove that the controller does more than generate elegant uncertainty visualisations.

---

# 1. Stack position

The long-term architecture is:

**scientific objective / lab agent**  
→ **epistemic acquisition controller**  
→ **instrument / microscope control layer**  
→ **measurement**  
→ **analysis / inference**  
→ **updated uncertainty field**  
→ **epistemic acquisition controller again**

Parallax does not replace:

- the scientific agent;
- the microscope-control API;
- segmentation / perception;
- the physical instrument;
- the QC classifier.

It is the **measurement-policy and perceptual-expansion layer under uncertainty**.

Its job is to decide how the immediate observation should adapt, while mapping better representations and justified
future measurement capabilities. The local five-lens Examiner and NEXT CAPTURE handle the current decision. The
Agentic Marker Frontier turns structured limits into marker investigations, observability gaps and capability pools.

---

# 2. Why this layer matters

Autonomous labs do not only need agents that decide **which experiment** to run.

They also need systems that know:

- whether the current measurements are sufficient;
- whether apparently strong evidence is actually acquisition-driven;
- where the data stops supporting confident inference;
- whether the current field of view is too small;
- whether the resolution is wrong;
- whether another detector is needed;
- whether more samples of the same kind would be mostly redundant;
- whether a completely different measurement would unlock enough information to justify its cost;
- and whether the uncertainty model itself is missing an important dimension.

The core problem is therefore not:

> "How do we collect more data?"

It is:

> **"How should the measurement policy change so that the next observation is maximally useful?"**

---

# 3. The local scientific object: the uncertainty field

The local decision loop has **one canonical epistemological object**.

That object is the:

> **uncertainty field**

The uncertainty field represents the range and structure of material states that remain plausible given the evidence acquired so far.

It is not one confidence score.

It reflects support across the actual dimensions of observation:

- spatial position;
- coherent capture area;
- field of view;
- scale / magnification;
- detector / modality;
- baseline population coverage;
- physical features and KPIs;
- acquisition conditions;
- sampling density;
- composition information;
- known nuisance factors;
- and scientifically justified additional dimensions.

Every major system component must either:

1. estimate the field;
2. explain why it has its current shape;
3. challenge whether the field is missing a dimension;
4. or choose an acquisition action expected to reshape it usefully.

The research-opportunity loop consumes this field through `marker-frontier/1`; it does not alter or duplicate the
field's scientific verdict. Its opportunity map records inquiry vortices, marker protocols and observability
dependencies for research and planning agents.

---

# 4. The fading outer rim

The key conceptual and visual construct remains the **fading outer rim**.

The outer rim is the boundary where the current dataset stops strongly constraining reality.

It is not merely the edge of an image.

A dataset has a shape in measurement space.

That shape depends on:

- how much material was sampled;
- whether the capture was spatially coherent or fragmented;
- what scales were observed;
- which detectors / modalities were used;
- how many genuinely independent samples exist;
- how representative the baseline is;
- which acquisition conditions were covered;
- which physical properties were measured at all.

Toward the centre of well-supported regions, many alternative states of reality have been ruled out.

Toward the rim, support fades.

Beyond it, increasingly many plausible material states remain compatible with what we have observed.

The controller should therefore ask:

> **Where is the outer rim consequential to the scientific decision we are trying to make?**

---

# 5. Measurement policy, not simply active learning

Ordinary active learning often assumes a predefined action space:

> choose the next sample / point from the available search space.

Our controller must be able to challenge that action space itself.

Candidate actions may include:

- sample another independent field;
- capture a larger coherent region;
- move to a different region;
- increase magnification;
- decrease magnification to gain spatial context;
- repeat acquisition under controlled settings;
- switch detector;
- add EDS;
- acquire an adjacent section;
- expand the approved baseline;
- acquire another physical measurement;
- request a novel parallel dataset.

This creates two decision levels:

### Level A — Where / what should we measure next inside the current acquisition vocabulary?

### Level B — Is the current acquisition vocabulary itself insufficient?

Level B is one of the main differentiators.

---

# 6. Recursive epistemology

The controller is intentionally recursive.

It does not merely estimate uncertainty using a fixed list of variance sources.

It must also ask:

> **What important source of variance or information might our current uncertainty model not contain?**

A scientifically credible newly discovered variance source may make the system **less certain**.

That is correct behaviour.

The recursive cycle is:

**observe → model variance → infer outer rim → discover missing variance → expand the rim honestly → acquire / infer new evidence → constrain again**

The system should never be rewarded simply for reducing uncertainty.

It should be rewarded for making the uncertainty model **more faithful to what can and cannot actually be known**.

---

# 7. Two recursive improvement loops

## A. Acquisition loop

**current data → uncertainty field → consequential outer rim → candidate acquisition actions → choose next measurement → new data → updated field**

This is the production controller.

Its output is an acquisition policy.

Examples:

> Capture a wider coherent BSE mosaic before collecting more random fields.

> Increase magnification in this region; current uncertainty is resolution-limited.

> Repeat this field under controlled acquisition settings before treating the apparent shift as material.

> Morphology is robust but composition remains unresolved; EDS is now the highest-value next measurement.

## B. Scientific-discovery loop

**failure state → missing information → scientific literature / agentic research → candidate new inference or measurement dimension → test → update the controller's model / action space**

This is qte77's lane.

It prevents the controller from assuming that its current measurement vocabulary is complete.

---

# 8. qte77's role in V2

qte77 is the **measurement-space expansion agent**.

He should challenge the current uncertainty model from outside it.

His research has two outputs.

### 1. New inference dimensions recoverable from existing data

Examples:

- spatial correlation structures;
- topology;
- morphology descriptors;
- texture;
- clustering;
- characteristic length scales;
- cross-detector relationships;
- physical proxies;
- scale-dependent statistics.

These should enter the controller only if they materially alter the uncertainty field or acquisition recommendation.

### 2. New measurement actions / parallel datasets

Examples:

- larger coherent SEM mosaics;
- EDS;
- tomography;
- adjacent sections;
- alternative detector modes;
- process telemetry;
- composition measurements;
- electrochemical / mechanical data;
- another scientific modality.

A new measurement should not enter the action space because it is interesting.

It needs **critical mass of unlocked value**.

That means:

- the failure state matters;
- the information is meaningfully orthogonal to what we already have;
- the expected reduction / reshaping of consequential uncertainty is substantial;
- the measurement is feasible enough to justify;
- and the benefit can eventually be tested.

This creates a controller whose **action vocabulary can itself improve over time**.

---

# 9. Capture geometry is a first-class control variable

One of the strongest near-term ideas is that the system should reason about the **shape of acquisition**.

"More data" is not a sufficient recommendation.

Suppose the observed material has spatial correlation extending close to the field-of-view boundary.

Then collecting fifty more small crops may mostly repeat the same local view of the phenomenon.

The highest-value action may instead be:

> **increase coherent capture area**

Conversely, if the relevant structure lies near the resolution limit, widening the field could be counterproductive.

Then:

> **increase magnification**

The controller should therefore attempt to estimate, where defensible:

- within-field vs between-field variance;
- spatial autocorrelation;
- characteristic correlation length;
- characteristic defect / cluster scale;
- how variance changes with window size;
- spatial redundancy;
- sensitivity to resolution;
- detector-specific information;
- how quickly uncertainty decreases with added area or independent sampling.

This is how the outer-rim metaphor becomes an actual acquisition decision.

---

# 10. Decision objective

The controller should eventually rank acquisition actions by something approximating:

> **expected reduction in consequential uncertainty / acquisition cost**

"Cost" can initially be crude:

- time;
- number of additional images;
- instrument complexity;
- need for another modality;
- operator effort.

For the hackathon, the model does not need to solve full Bayesian optimal experimental design.

But every NEXT CAPTURE recommendation should correspond to a defensible statement about:

1. which uncertainty it addresses;
2. why that uncertainty matters;
3. why this acquisition is more informative than obvious alternatives.

Do not fabricate numerical information-gain scores if the current model cannot support them.

---

# 11. The hero interface: Evidence Field as control surface

The main interface should look like a **scientific control surface**, not a conventional dashboard.

The hero is the Evidence Field.

It should allow the user to perceive:

- where the material appears different;
- where measurements are stable;
- where evidence is acquisition-sensitive;
- where support fades;
- which part of the outer rim is currently consequential;
- which acquisition action the controller recommends.

Possible visual channels:

- **hue** → type of evidence / uncertainty;
- **brightness** → material deviation strength;
- **solidity** → survival under nuisance / falsification tests;
- **flicker** → acquisition instability;
- **fade / hollowness** → weak model support;
- **expanding area cue** → need for broader coherent capture;
- **zoom cue** → magnification bottleneck;
- **modality cue** → detector / measurement missing;
- **pulse** → high-leverage next action.

The statistics remain auditable underneath.

The first visual experience should be:

> **the shape of what is known, the shape of what is not known, and where the instrument should look next.**

---

# 12. Core demo story

The strongest demo sequence is:

**1. DIAGNOSE**

Run the actual Polaron QC analysis.

Show that the system can detect a meaningful deviation and produce a usable ACCEPT / INVESTIGATE / REJECT result.

**2. CHALLENGE THE DIAGNOSIS**

Apply acquisition normalization, perturbation robustness, provenance / sampling correction and baseline support.

Watch weak apparent signals disappear.

Keep what survives.

**3. SHOW THE OUTER RIM**

Reveal where the current dataset stops supporting confident inference.

Do not show uncertainty as a generic confidence bar.

Show what kind of measurement limit creates it.

**4. NEXT CAPTURE**

Recommend the next observation:

- more area;
- different scale;
- different detector;
- repeat acquisition;
- another modality;
- broader baseline.

Explain why.

**5. AGENTIC EXPANSION**

Show that the controller can also accept scientifically grounded new measurement dimensions discovered by the research agent.

This is the bridge to next-generation agentic labs.

---

# 13. Polaron as proof environment

The current Polaron pipeline remains crucial.

It demonstrates that we are not drawing an abstract autonomous-lab architecture.

We already have a working diagnostic substrate that:

- reconstructs parent micrographs rather than treating every tile as independent;
- identifies acquisition fingerprints;
- tests KPI robustness under acquisition perturbations;
- rejects unstable measurements;
- rejected pseudotime when its apparent structure was acquisition-driven;
- identifies a robust Batch 3 deviation concentrated in M2060;
- exposes how much the decision depends on M2060;
- keeps chemistry unresolved rather than overclaiming;
- produces an interpretable QC verdict.

Those are early examples of the controller's governing philosophy:

> **find signal → challenge signal → expose unsupported assumptions → choose what must be observed next**

Polaron is the first application.

The longer-term target is the measurement-policy layer of autonomous microscopy and, potentially, broader agentic-lab systems.

---

# 14. Positioning

Avoid:

> AI for autonomous labs.

Too broad.

Avoid:

> uncertainty-aware microscopy.

Too weak and already crowded.

Avoid:

> active learning for microscopy.

Already an established field.

Preferred framing:

> **Epistemic acquisition controller for agentic microscopy**

Alternative:

> **Measurement-policy layer for autonomous microscopes**

Pitch formulation:

> **Autonomous labs do not only need agents that decide what experiment to run. They need systems that know when their measurements are insufficient — and how to improve them. We build that layer for microscopy.**

Short version:

> **Know what to measure next.**

---

# 15. Relationship to the existing landscape

We should reuse mature parts rather than reinvent them.

See `docs/RESSOURCES.MD`.

Relevant adjacent stacks include:

- gpCAM / BoTorch / Xopt for Bayesian experiment design;
- GSTools / scikit-gstat for spatial correlation and dataset geometry;
- MAPIE / UQ libraries for calibrated uncertainty;
- Bluesky Adaptive / HELAO for autonomous experimental orchestration;
- AtomAI / HyperSpy / LiberTEM for scientific-image pipelines;
- Gently / SBEMimage / vendor APIs for agentic or automated microscope execution.

Our possible differentiation is not any one of those components.

It is the **recursive measurement-policy layer connecting them**:

> model the epistemic boundary of the acquired dataset → decide how measurement should expand → allow scientific evidence to challenge the dimensions from which that boundary was inferred.

---

# 16. Non-goals

- Do not build a generic autonomous-lab platform.
- Do not attempt real microscope control during the hackathon unless an unusually easy integration appears.
- Do not create multiple parallel uncertainty frameworks.
- Do not represent uncertainty only as scalar confidence.
- Do not recommend "more data" without saying what shape of data.
- Do not invent numerical acquisition utility without support.
- Do not add scientific modalities just because they are interesting.
- Do not let agentic literature research become a parallel product.
- Do not resurrect pseudotime without new evidence.
- Do not hide newly discovered uncertainty.
- Do not replace the working QC engine with speculative architecture.
- Do not make the UI a wall of plots.
- Do not overclaim chemistry, causality or failure mechanisms.

---

# 17. Hackathon V2 build priority

1. **Preserve the working QC engine.**
2. **Audit independence / leakage and any statistical assumptions on which the proof layer depends.**
3. **Formalise the minimum useful uncertainty field.**
4. **Make dataset geometry explicit.**
5. **Test spatial-scale / coherent-area logic with real statistics where possible.**
6. **Build the Evidence Field control surface.**
7. **Make the outer rim visible in a way tied to real evidence.**
8. **Implement a small set of defensible NEXT CAPTURE actions.**
9. **Keep conventional QC evidence accessible underneath.**
10. **Let qte77 feed scientifically grounded new inference / measurement candidates through a strict gate.**
11. **Use external libraries only when they accelerate a defensible component.**
12. **Demo the transition from diagnosis → uncertainty boundary → acquisition decision.**

---

# 18. Final product thesis

> **We build the measurement-policy layer that helps an autonomous microscope decide what to observe next, by modelling where its current evidence stops constraining reality and recursively improving the vocabulary of measurements available to it.**

The Polaron challenge proves the first loop.

The long-term opportunity is next-generation agentic laboratories.
