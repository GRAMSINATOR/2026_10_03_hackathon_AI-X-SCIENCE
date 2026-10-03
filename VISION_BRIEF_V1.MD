# VISION BRIEF V1

## Working thesis

We are not building a better anomaly detector.

We are building an **epistemic diagnostic layer** that shows where a scientific quality-control process is strong, where it is blind, why it is uncertain, and **what should be measured next to improve the diagnosis most efficiently**.

Polaron's battery-electrode QC task is the proving ground. The product is broader:

> **Map what the diagnostic system knows, what it may be missing, and which next observation would reduce uncertainty most.**

The ordinary QC answer — ACCEPT / INVESTIGATE / REJECT — remains important, but it is **supporting proof**, not the organizing metaphor of the product.

---

## One canonical model

The product must not drift into several parallel epistemological systems.

There is **one primary representational object**:

> **the uncertainty field**

The uncertainty field describes the spread of material states that remain plausible given the evidence currently available.

It is not a single scalar confidence value. It is a structured distribution over the observable space of the diagnostic process, including:

- **spatial position**;
- **capture scale / magnification**;
- **detector or measurement modality**;
- **derived physical features / material KPIs**;
- **acquisition conditions and known nuisance factors**.

Everything else in the product must be expressed as something that **widens, narrows, reshapes, or interrogates this field**.

This is the canonical epistemological rule:

> **Represent the current envelope of plausible reality → find where that envelope is too wide, unsupported or inconsistent → estimate which observation would contract it most → update.**

A **blindspot** is a region of the uncertainty field that remains poorly constrained.

A **robust anomaly** is an observed deviation that remains outside the supported uncertainty spread after plausible acquisition, sampling and nuisance variation are accounted for.

A **measurement recommendation** is an acquisition action predicted to contract the uncertainty field more than the alternatives.

A **capture-geometry problem** is a case where the dominant uncertainty comes from how reality was sampled — for example insufficient coherent spatial extent, the wrong magnification, redundant local sampling, or the wrong modality.

A **model-support problem** is a case where the current observation lies outside the region represented well enough by the baseline to justify a confident interpretation.

Provenance, perturbation testing, detector disagreement, uncertainty calibration, sampling density, baseline coverage, composition ambiguity and active acquisition are **not separate product concepts**. They are factors that modify the same uncertainty field.

The product is therefore fundamentally:

> **a system for dynamically refining the shape of what is known.**

### Two improvement loops, one object

There are only two allowed improvement loops, and both update the same uncertainty field.

**Measurement loop**

**current data → uncertainty field → blindspot → next capture → updated field**

This determines what should be measured next: more area, different scale, another detector, another section, EDS, more baseline material, or another acquisition strategy.

**Discovery loop**

**paper / agentic research → candidate measurable pattern or inference operator → test on current data → update field**

This is where **qte77's workstream** belongs.

qte77 should run the agentic literature-research / inference-discovery loop: search papers and related technical work for new patterns, descriptors, physical proxies, cross-detector relationships, characteristic scales, morphology statistics, or other inference leads that may be extractable from the current dataset.

The purpose is not to create a parallel research product. qte77's output should be **candidate measurable structures** that can be tested against the existing data and then either incorporated into or rejected by the same uncertainty field.

A candidate lead becomes part of the product only if it changes the uncertainty field in a useful, testable way — for example by revealing previously hidden variance, explaining existing spread, reducing a blindspot, improving the estimate of plausible unseen variation, or changing the highest-value next observation.

This creates a continuous-improvement runway and a perpendicular challenge to the current model: the system is not limited to the features we thought of at the start. qte77 continuously searches for additional scientifically grounded ways to interrogate the same dataset, while the canonical product model remains unchanged.

This prevents the research stream from becoming a parallel feature factory.

All new inference leads must answer one question:

> **Does this improve our estimate of what remains plausible, or tell us how to reduce that uncertainty more efficiently?**

---

## The problem

Most QC systems treat the dataset as fixed and ask:

> Is this sample normal or abnormal?

That leaves several deeper questions unanswered:

- Is an apparent deviation actually material, or is it caused by acquisition?
- How much relevant variance may exist outside what was sampled?
- Is the current field of view too small to reveal the structure that matters?
- Is the current magnification too low or too high?
- Are we repeatedly sampling the same local regime?
- Would another detector or modality resolve the ambiguity better than collecting more of the same data?
- Is the baseline itself too narrow?
- Is the model extrapolating beyond the region in which it has support?
- Which single additional observation would improve the decision most?

The dataset is therefore not just an input. **The geometry and method of capture are themselves objects of diagnosis.**

---

## Product

The product is a **self-improving diagnostic interface** for scientific and industrial QC.

It performs the requested diagnosis, but then interrogates the diagnosis itself.

### Core loop

**OBSERVE → DIAGNOSE → LOCATE BLINDSPOTS → CHOOSE NEXT OBSERVATION → UPDATE THE KNOWLEDGE MODEL → DIAGNOSE AGAIN**

The system should identify whether the dominant bottleneck is:

- sample count;
- spatial coverage;
- coherent capture area;
- resolution / magnification;
- detector modality;
- acquisition instability;
- baseline diversity;
- composition information;
- or an unsupported region of the model.

The goal is not simply "more data."

The goal is:

> **the right shape of data, captured in the right place, at the right scale, with the right modality.**

---

## Favored frame

The interface is intentionally biased toward one question:

> **Where is the diagnosis weakest, what kind of weakness is it, and what measurement would improve it most?**

This is an epistemological tool embodied inside a materials diagnostic system.

A visually unusual region is not automatically uncertain.

A visually normal region is not automatically well known.

The system must distinguish between:

- **supported normality**;
- **supported material shift**;
- **measurement-confounded evidence**;
- **spatial undersampling**;
- **scale ambiguity**;
- **modality disagreement**;
- **baseline weakness**;
- **composition blindness**;
- **model extrapolation / unsupported state**.

This is closer to Track 2's epistemological-agent logic applied to Track 4's physical QC problem: the diagnostic system should know when it does not know.

---

## Central technical idea

The core computation is to estimate and update the **uncertainty field**.

The field should represent, as far as the available data allows:

1. the variation already observed in the material;
2. the variation attributable to the observation / acquisition process;
3. the plausible but unobserved variation implied by sparse sampling, spatial structure, limited scale, weak baseline coverage or detector limitations;
4. the residual deviations that survive those explanations;
5. how much the field is expected to contract under each candidate next measurement.

The important object is not a generic confidence score and not a collection of separate uncertainty widgets.

It is the **shape and spread of plausible reality under the current evidence**.

The operational question is always:

> **What uncertainty remains, where does it live, and what observation would shrink it most?**

A region might need:

- a wider coherent field of view;
- higher magnification;
- lower magnification / more context;
- another adjacent section;
- more independent spatial sampling;
- BSE rather than another InLens image;
- ETD / InLens for morphology or topography;
- EDS for composition;
- more approved baseline material;
- or simply a repeated acquisition under controlled settings.

The system should rank those interventions by **expected diagnostic value**, ideally relative to acquisition cost or effort.

---

## Capture geometry is part of the model

A major thesis is that the system should question the **boundaries of capture**.

Example:

If variance appears correlated over spatial scales close to the current field-of-view boundary, collecting hundreds of additional tiny random crops may be less informative than collecting a smaller number of **larger contiguous regions**.

Conversely, if the uncertain feature lies near the resolution limit, widening the field may make the diagnosis worse; the correct intervention may be higher magnification.

Therefore the system should estimate, where possible:

- within-field versus between-field variance;
- spatial autocorrelation / correlation length;
- characteristic defect or structure size;
- clustering scale;
- detector disagreement;
- sensitivity to resolution;
- how uncertainty changes with sampled area;
- how much of the current evidence is spatially redundant.

This allows the model to answer a question that conventional QC rarely asks:

> **Are we collecting enough data, or are we collecting data in the wrong geometry?**

---

## Hero interface: Evidence Field

Do not make the main experience a conventional scientific dashboard.

The hero object should feel closer to a **Launchpad / control surface / active scientific instrument**.

### Evidence Field

A grid of spatial evidence units representing the currently observed material.

Each pad is not just "an anomaly score." It represents the **epistemic state** of that observation.

Possible visual channels:

- **hue** → dominant evidence / blindspot type;
- **brightness** → magnitude of observed or residual signal;
- **solidity** → survival under falsification / perturbation;
- **flicker** → measurement instability;
- **hollowness** → unsupported or undersampled region;
- **border / leverage** → how much the region influences the final diagnosis;
- **directional cue** → recommended next acquisition;
- **pulse / projected area** → expected information gain.

Primitive statistical values should stay underneath. The main representation should compress them into a perceptually legible state.

### Modes

#### MATERIAL
What appears to differ physically?

#### BLINDSPOTS
Where could the current capture regime be missing relevant variation?

#### NEXT VIEW
What observation would improve the diagnosis most?

#### EVIDENCE SURVIVAL
Watch apparent deviations disappear or persist as the system applies successive falsification layers.

---

## The wow-factor interaction

Begin with many apparent differences.

Then progressively challenge them:

**RAW → NORMALIZE ACQUISITION → PERTURB / STRESS → CORRECT SAMPLING / PROVENANCE → BASELINE SUPPORT → SURVIVING SIGNAL**

Signals that can be explained by acquisition fade or collapse.

Signals unstable to processing flicker and disappear.

Unsupported regions become visibly hollow rather than falsely precise.

Signals that survive become more solid.

The emotional result should be:

> **We begin with many apparent anomalies. We try to explain them away. What remains is the evidence we actually trust.**

This gives continuity, motion and visual drama without inventing pseudotime.

---

## Adaptive acquisition

The interface should not stop at "uncertain."

It should propose the **next best observation**.

Examples:

- "Increase coherent capture width before adding more random samples."
- "Acquire a higher-magnification BSE image in this region."
- "Repeat this field under controlled acquisition settings."
- "Acquire adjacent sections to test spatial persistence."
- "Use EDS here: morphology is robust but chemistry is unresolved."
- "More baseline material is more valuable than more incoming-batch sampling."

Where possible, candidate actions should be scored by something like:

**expected uncertainty reduction / acquisition effort**

This turns the system from passive inspection into **adaptive evidence acquisition**.

---

## What we already have as proof

The current Polaron implementation is valuable because it gives this concept a real technical substrate rather than leaving it as speculative UX.

The reconnaissance already demonstrated several behaviors the new product should preserve:

- reconstructed 31 fields into approximately 13 parent micrographs instead of treating all fields as independent;
- found that some apparent latent structure was acquisition-driven and rejected pseudotime rather than forcing it;
- measured which physical KPIs survive realistic acquisition perturbations;
- rejected KPIs that were too sensitive to blur, gamma, contrast or detector artifacts;
- identified a baseline micrograph where additive measurements were not comparable enough to trust;
- found a robust Batch 3 deviation concentrated in M2060;
- showed that removing M2060 flips the Batch 3 decision back toward ACCEPT;
- kept chemistry of the bright phase explicitly unresolved and recommended EDS rather than overclaiming;
- produced a usable ACCEPT / INVESTIGATE / REJECT pipeline with a hidden-batch path.

This is the **proof layer**.

The new interface should make the epistemic structure behind these behaviors visible.

---

## Relationship to the Polaron track

The track asks:

> Can you detect when a supplier's material has changed before it becomes a manufacturing problem?

We should still answer that well.

But we do not want the track brief to define the product.

Our stronger question is:

> **How good is the diagnostic process itself, where are its blindspots, and what should we observe next to make it better?**

Polaron becomes a concrete validation environment for a more general scientific instrument.

The Track 4 outputs — material KPIs, uncertainty, hidden-batch accuracy, interpretability, ACCEPT / INVESTIGATE / REJECT — should remain available beneath the interface as evidence that the system actually works.

They are not the hero.

---

## Non-goals

- Do not resurrect pseudotime unless new evidence genuinely supports it.
- Do not make latent-space aesthetics the centerpiece simply because they look technical.
- Do not collapse all uncertainty into one confidence score.
- Do not assume more samples are always the correct answer.
- Do not assume the current capture geometry is appropriate.
- Do not make the main page a wall of KPIs, p-values or conventional scientific plots.
- Do not hide unsupported regions behind false precision.
- Do not overclaim chemistry, chronology, causality or material failure mechanisms not supported by the data.
- Do not optimize the product around the wording of the sponsor prompt.

---

## Product statement

> **A diagnostic system that maps what it knows, what it may be missing, and the next observation that would improve the diagnosis most.**

Alternative formulation:

> **We don't just ask whether your data is sufficient. We ask whether you're collecting the right shape of data.**

And the shortest demo idea:

> **See what survives. See what is missing. Know what to measure next.**

---

## Immediate build priority

1. Preserve the existing QC engine as the evidence substrate.
2. Audit the current model for baseline/test leakage caused by reconstructed parent micrographs spanning batch folders.
3. Define the minimal representation of the **uncertainty field** for each evidence cell / region:
   - observed spread;
   - nuisance / acquisition-explainable spread;
   - plausible unobserved spread from sampling and support limits;
   - residual material deviation;
   - support / blindspot level;
   - expected contraction under candidate next measurements.
   Derive decision leverage, recommended acquisition action and expected information gain from this same representation rather than creating separate conceptual systems.
4. Build the Evidence Field as the hero interaction.
5. Add the evidence-survival / falsification sequence.
6. Add a NEXT VIEW mode that can recommend spatial extent, scale, modality or additional baseline sampling.
7. Keep conventional QC outputs and technical evidence available below / behind the hero surface.
8. Use the unseen batch as the proof test for both diagnostic accuracy and the usefulness of the blindspot / next-acquisition model.

The target is not a prettier dashboard.

The target is a **new scientific control surface for improving how diagnosis itself is performed**.
