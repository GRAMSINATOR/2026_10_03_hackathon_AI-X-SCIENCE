# VISION BRIEF V1

## Vision in one sentence

We are building a **recursive epistemic diagnostic system** that performs materials QC, models where the current dataset stops constraining reality, and then improves the diagnostic process by identifying the next measurement, capture strategy, inference dimension, or parallel dataset that would reduce the most consequential uncertainty.

Polaron's battery-electrode QC problem is the proving ground.

The product is broader:

> **Diagnose the material, diagnose the limits of the diagnosis, then improve how reality is observed.**

The ACCEPT / INVESTIGATE / REJECT result remains essential proof that the system can do the requested QC task. It is not the organizing metaphor of the product.

---

## The core object: the uncertainty field

The product must not drift into multiple parallel epistemological systems.

There is one canonical object:

> **the uncertainty field**

The uncertainty field represents the range and structure of material states that remain plausible given the evidence currently available.

It is not a single confidence score.

It is shaped by the dataset's actual support across:

- spatial position;
- coherent capture area;
- field of view;
- magnification / scale;
- detector or measurement modality;
- baseline population coverage;
- physical features and derived KPIs;
- acquisition conditions;
- sampling density;
- composition information;
- known nuisance factors;
- and any other scientifically justified source of variance.

Everything else in the product must either:

1. **describe the uncertainty field**;
2. **change its shape**;
3. **explain why it has that shape**; or
4. **identify an observation that would reshape it usefully**.

Provenance, perturbation testing, detector disagreement, active acquisition, baseline coverage, model support, literature research and new measurement technologies are not separate product ideas.

They all operate on the same uncertainty field.

---

## The fading outer rim

The key visual and epistemological metaphor is the **fading outer rim of the dataset**.

This is not simply the physical edge of an SEM image.

The outer rim is the boundary of what the current dataset can legitimately constrain.

The dataset has a **size and shape** in measurement space.

That shape is determined by what has actually been captured:

- how much area;
- how coherently that area was captured;
- at what magnification;
- with which detector;
- across how many independent samples;
- under which acquisition conditions;
- with what physical or compositional measurements;
- and across which kinds of material variation.

Inside the well-supported region, the system has evidence.

Toward the rim, support fades.

Beyond it, increasingly many states of reality remain plausible because the data no longer constrains them strongly enough.

The product should therefore model not only observed variance, but how each variance source changes the significance, thickness and geometry of this outer rim.

Examples:

- strong spatial correlation near the field-of-view limit may mean the dataset's spatial rim is too close and larger coherent captures are needed;
- a feature near the resolution limit may mean the scale rim is the dominant constraint and higher magnification is needed;
- disagreement between BSE and another detector may expose a modality rim;
- a narrow approved baseline may create a population-support rim;
- unknown chemistry can create an unresolved explanatory dimension even when morphology is measured well;
- acquisition instability can widen the range of appearances consistent with the same underlying material state.

The canonical question is:

> **Given the variance we can currently see, where does the dataset stop strongly constraining reality?**

---

## The recursive architecture

The system is intentionally recursive.

It does not only estimate uncertainty inside the current dataset.

It also asks whether the **model of uncertainty itself is incomplete**.

This creates two nested levels operating on the same uncertainty field.

### Level 1 — Model the dataset's current uncertainty

The system looks at the current data and estimates:

- observed variance;
- spatial variance;
- between-sample versus within-sample variance;
- acquisition-driven variance;
- detector disagreement;
- scale dependence;
- baseline support;
- sampling redundancy;
- residual deviations;
- plausible unobserved variance implied by the current capture geometry.

From that, it infers the current fading outer rim.

The operational loop is:

**current dataset → estimate variance → infer the outer rim → locate the dominant constraint → choose the next observation → update the field**

The next observation may be:

- more independent samples;
- a larger coherent area;
- higher magnification;
- lower magnification / more context;
- another detector;
- another section;
- repeated acquisition under controlled conditions;
- EDS or another compositional measurement;
- broader approved baseline material;
- or another justified capture change.

The system should not assume that "more data" means "more samples of the same kind."

It should ask:

> **What shape of new data would reduce the consequential uncertainty most?**

### Level 2 — Audit the sources of variance themselves

The agentic layer then challenges Level 1.

It asks:

> **What important sources of variance or information might our current uncertainty model not even contain?**

This is a second-order blindspot search.

A newly discovered, scientifically credible variance source may initially **expand the outer rim**.

That is desirable.

It means the system has discovered that it was previously overconfident.

Only after the relevant evidence is acquired or extracted can that rim be tightened again.

The recursive epistemic cycle is therefore not monotonically "uncertainty goes down."

It is:

> **discover missing uncertainty → widen the supported model honestly → acquire or infer the missing evidence → constrain it again**

That dynamic is central to the product.

The system improves not only by collecting more evidence, but by becoming better at identifying **what kinds of evidence it did not know it needed**.

---

## qte77 — recursive measurement-space expansion

qte77 owns the agentic scientific-research layer.

His role is not generic paper search and not a parallel feature-development stream.

His job is to **challenge the current variance model from outside it**.

He begins from consequential failure states exposed by the uncertainty field:

- unresolved residual variance;
- unexpected spread;
- spatial truncation;
- scale ambiguity;
- detector disagreement;
- composition blindness;
- weak physical interpretation;
- unsupported morphology regimes;
- acquisition sensitivity;
- or other blindspots that materially affect the diagnostic process.

He then searches papers, technical literature and scientific evidence for two classes of expansion.

### 1. New inference dimensions from data we already have

These are scientifically grounded measurements or relationships that may already be latent in the existing dataset but are not yet part of our model.

Examples may include:

- morphology descriptors;
- spatial correlation measures;
- topology;
- texture;
- clustering statistics;
- scale-dependent features;
- cross-detector relationships;
- physical proxies;
- characteristic length scales;
- new combinations of existing measurements;
- or other inferential structures supported by literature.

The question is not:

> "What else can SEM tell us?"

It is:

> **"What scientifically credible dimension are we currently failing to model that could explain, expose or constrain meaningful variance?"**

A candidate inference is valuable when it can:

- reveal hidden variance;
- explain existing spread;
- distinguish nuisance from material signal;
- expose a new blindspot;
- shrink an existing rim;
- or show that the current rim should actually be wider.

### 2. New measurement approaches and novel parallel datasets

Some uncertainty cannot be resolved from the current SEM dataset.

qte77 should also identify measurement approaches, instruments, modalities, assays, process data, or other parallel datasets that could unlock genuinely new information.

Examples may include:

- EDS;
- larger coherent SEM mosaics;
- different magnification regimes;
- adjacent cross-sections;
- tomography;
- alternative microscopy modes;
- process telemetry;
- compositional measurements;
- mechanical or electrochemical measurements;
- or another scientifically defensible data source.

But novelty alone is not enough.

A new measurement approach should enter the product only when it reaches **critical mass of unlocked value**.

That means it must correspond to failure states that matter and offer enough additional information to justify the acquisition burden.

The rough acceptance test is:

- **consequence** — does the blindspot matter to a QC decision, failure mode, or important scientific interpretation?
- **orthogonality** — does the new data contain information the current dataset genuinely cannot provide?
- **coverage** — does it resolve one high-leverage blindspot or several related blindspots at once?
- **information gain** — is it expected to reshape the uncertainty field substantially?
- **feasibility / cost** — is the gain plausible relative to acquisition effort, time or complexity?
- **testability** — can the proposed value be evaluated rather than merely asserted?

This prevents the agentic layer from becoming a catalogue of interesting technologies.

The governing loop is:

**failure state → identify missing information → search scientific evidence → propose new inference or measurement dimension → estimate/test its effect on the uncertainty field → adopt, reject, or defer**

---

## The outer rim can expand before it contracts

This distinction is important enough to state explicitly.

A good epistemic system is not rewarded for always becoming more confident.

If research reveals a credible missing variance source, the correct response may be:

> **we know less than we thought**

That should visibly expand or reshape the outer rim.

Example:

We may initially believe the relevant variation is captured by local particle statistics.

Then literature and the data together suggest that defect clustering occurs over scales larger than the current field of view.

The system should not hide this because it makes the model look less certain.

It should say:

> **our current capture geometry cannot rule out larger-scale structure**

The spatial rim expands.

The next-best measurement may then become a larger coherent capture rather than more small fields.

After that larger capture arrives, the newly exposed uncertainty can contract again.

This alternating process —

**discover → expand → measure → constrain**

— is the core recursive behavior.

---

## Capture geometry is itself diagnostic

The dataset is not a neutral container.

Its geometry can create or hide uncertainty.

A major product capability is therefore to question the boundaries of capture.

For example:

If the observed morphology has a characteristic correlation length close to the width of the current image, then many additional small independent crops may not solve the important uncertainty.

The better acquisition may be:

> **capture a larger coherent region so larger-scale structure can actually be observed**

Conversely, if the important feature is close to the resolution limit, increasing coherent area may reduce useful resolution.

Then the better acquisition may be:

> **increase magnification in a targeted region**

The product should therefore estimate, where defensible:

- within-field versus between-field variance;
- spatial autocorrelation / correlation length;
- characteristic defect size;
- clustering scale;
- how variance changes with window size;
- sensitivity to pixel size and magnification;
- detector-specific information;
- spatial redundancy;
- and how quickly uncertainty decreases as area or independent sampling increases.

This lets the system distinguish:

> **we need more data**

from:

> **we need data with a different geometry**

That distinction is one of the central product insights.

---

## Product behavior

The product performs three things in one recursive loop.

### 1. Diagnose the material

Do the Track 4 task properly.

Detect meaningful deviation from the approved baseline.

Separate material signal from acquisition artefact where possible.

Produce interpretable evidence.

Return ACCEPT / INVESTIGATE / REJECT.

### 2. Diagnose the diagnostic process

Show:

- where support is strong;
- where support fades;
- which variance source is widening the rim;
- where visually normal material is actually poorly known;
- where apparent anomalies are likely nuisance-driven;
- where a result depends on a small amount of high-leverage evidence;
- and which important forms of variation may remain unseen.

### 3. Improve the measurement process

Recommend the next action most likely to improve the diagnosis:

- change area;
- change scale;
- change modality;
- repeat acquisition;
- extend baseline;
- acquire a new physical measurement;
- or investigate a new scientifically grounded inference dimension.

The product is therefore not simply a QC classifier.

It is a **recursive control system for the quality of the QC process itself**.

---

## Hero interface: the Evidence Field

The main experience should not look like a conventional scientific dashboard.

It should feel closer to a **Launchpad, control surface, or active scientific instrument**.

The hero object is an **Evidence Field**: a grid / field of observations whose visual state represents the current epistemic structure of the dataset.

The visual grammar should privilege the uncertainty field and its rim.

Possible channels:

- **fill / hue** → dominant evidence or uncertainty class;
- **brightness** → strength of observed material deviation;
- **solidity** → how much evidence survives nuisance / falsification tests;
- **flicker** → instability under acquisition or processing changes;
- **hollowness / fade** → weak support and proximity to the outer rim;
- **spatial extent** → scale of the evidence or capture recommendation;
- **direction / expansion cue** → where the dataset should be extended;
- **modality marker** → which detector or measurement is missing;
- **pulse / emphasis** → expected information gain or leverage.

Primitive statistics stay underneath.

The surface should make the **shape of knowledge and ignorance** perceptible before the user reads a table.

---

## Interface modes

### MATERIAL

What appears physically different?

### UNCERTAINTY FIELD

Where is the current dataset strongly constraining reality, and where does support fade?

### OUTER RIM

Which size, shape, scale, modality or population constraints are currently limiting the model?

### NEXT CAPTURE

What data should we acquire next to reduce the most consequential uncertainty?

### DISCOVERED BLINDSPOTS

What new variance source or measurement dimension has the agentic research layer identified?

### EVIDENCE SURVIVAL

Which apparent deviations survive successive attempts to explain them away?

---

## The core interaction

The demo should show the uncertainty field changing under interrogation.

A useful sequence is:

**RAW OBSERVATION → ACQUISITION NORMALIZATION → PERTURBATION / STRESS → SAMPLING / PROVENANCE CORRECTION → BASELINE SUPPORT → OUTER-RIM MODEL → NEXT MEASUREMENT**

Apparent anomalies that can be explained by acquisition fade.

Unstable signals flicker and collapse.

Unsupported regions become visibly hollow.

Surviving material signal becomes more solid.

Then the system exposes what remains unresolved and shows **which direction the dataset itself should expand**.

The emotional result should be:

> **We do not merely find anomalies. We show what survives, what we cannot yet know, and how to observe it next.**

---

## Proof layer: what the current Polaron work already demonstrates

The concept is anchored in real analysis rather than speculative interface design.

The current implementation already provides evidence for the product logic:

- it reconstructed fields into parent micrographs rather than treating all tiles as independent;
- it discovered acquisition fingerprints and used perturbation testing to identify fragile measurements;
- it tested pseudotime / latent progression and rejected it when the dominant structure proved acquisition-driven;
- it rejected KPIs that were too sensitive to blur, gamma, contrast or detector artifacts;
- it identified a baseline micrograph where additive measurements were not trustworthy enough to use normally;
- it found a robust Batch 3 deviation concentrated in M2060;
- removing M2060 materially changes the Batch 3 conclusion, exposing decision leverage;
- chemistry of the bright phase remains unresolved, creating a legitimate measurement blindspot rather than an excuse to overclaim;
- the system already produces an interpretable ACCEPT / INVESTIGATE / REJECT result.

These behaviors are the first working examples of the recursive epistemic philosophy:

**find signal → challenge signal → expose unsupported assumptions → preserve only what survives**

The next step is to make the same logic explicit for dataset shape, unseen variance and future measurement.

---

## Relationship to the Polaron challenge

The challenge asks:

> Can you detect when a supplier's material has changed before it becomes a manufacturing problem?

We should answer that well.

But the product asks a deeper operational question:

> **How sure are we that our quality-control process would detect the kinds of change that matter, and what should we change about the measurement process if it would not?**

Polaron is therefore both:

1. the diagnostic task;
2. the validation environment for the recursive uncertainty model.

The Track 4 outputs remain available as hard proof:

- material KPIs;
- uncertainty;
- hidden-batch result;
- interpretability;
- ACCEPT / INVESTIGATE / REJECT;
- recommended follow-up.

They support the thesis.

They are not the hero.

---

## Product statement

> **A recursive diagnostic system that maps the limits of what the current dataset can tell us, discovers what those limits may themselves be missing, and identifies the next observation that would improve the diagnosis most.**

Shorter:

> **See what survives. See where knowledge fades. Expand the data where it matters.**

Another useful formulation:

> **We do not just ask whether you have enough data. We ask whether your dataset has the right shape — and whether your model of that shape is missing an entire dimension.**

---

## Non-goals

- Do not create multiple parallel epistemological frameworks.
- Do not reduce the uncertainty field to one confidence score.
- Do not treat every interesting literature finding as a product feature.
- Do not recommend new modalities or technologies unless they address consequential failure states.
- Do not assume more samples are always the answer.
- Do not assume the current field of view, magnification, detector set or baseline geometry is appropriate.
- Do not hide newly discovered uncertainty merely because it makes the system look less confident.
- Do not resurrect pseudotime unless new evidence genuinely supports it.
- Do not make latent-space aesthetics the centerpiece.
- Do not turn the interface into a wall of KPIs, p-values or conventional scientific plots.
- Do not overclaim chemistry, chronology, causality or material failure mechanisms unsupported by the evidence.
- Do not let qte77's research stream become a separate feature factory.
- Do not optimize the product architecture around the wording of the sponsor prompt.

---

## Immediate build priorities

1. **Preserve the existing QC engine as the proof substrate.**
2. **Audit baseline/test independence and reconstructed-parent leakage before building higher-level claims on top of it.**
3. **Formalize the uncertainty field and fading outer rim.**
   - observed variance;
   - acquisition / nuisance variance;
   - sampling variance;
   - spatial and scale dependence;
   - baseline support;
   - plausible unobserved variance;
   - residual material deviation.
4. **Model dataset geometry explicitly.**
   - coherent area;
   - field of view;
   - scale;
   - detector coverage;
   - independent sample count;
   - spatial redundancy.
5. **Build the Evidence Field as the hero interaction.**
6. **Make the outer rim visible.**
   The user should be able to see where the dataset's size and shape stop supporting confident inference.
7. **Build NEXT CAPTURE.**
   Compare candidate acquisition changes by expected reduction of consequential uncertainty relative to effort.
8. **qte77: run the recursive scientific-research loop.**
   Search for missing variance sources, new inference dimensions, and novel measurement / parallel-data opportunities tied to actual failure states.
9. **Introduce a critical-mass gate for new parallel datasets.**
   New data sources should be added only when their expected orthogonal information gain is large enough to justify them.
10. **Show recursive expansion explicitly.**
    When a newly discovered variance source means we were overconfident, the interface should be allowed to expand the outer rim before recommending how to constrain it again.
11. **Keep conventional QC outputs behind / beneath the hero surface as technical proof.**
12. **Use the unseen batch to test both the diagnostic result and the usefulness of the uncertainty / acquisition recommendations.**

The target is not a prettier QC dashboard.

The target is a **scientific control surface that recursively improves the quality, geometry and vocabulary of measurement itself**.
