# JOB SPLIT V1

## Purpose

Keep the hackathon work deliberately asymmetric.

We do **not** want two expensive agents independently exploring the same space.

The project has one product direction, defined in `docs/VISION_BRIEF_V2.MD`, with two complementary workstreams:

> **Guilhem + Claude turn the current knowledge into the product.**  
> **qte77 searches for what the current knowledge is missing.**

Both streams feed the same canonical object: the **uncertainty field**.

---

## 1. Guilhem — product direction and convergence

Guilhem owns the product thesis, prioritization and demo framing.

His job is to decide:

- what is conceptually central;
- what deserves to become part of the product;
- what gets cut;
- what the interface should privilege;
- which qte77 findings cross the threshold from interesting research to product-relevant evidence;
- what the final demo must communicate in two minutes.

Guilhem should spend human attention on **selection and coherence**, not on low-level implementation or exhaustive literature search.

---

## 2. Claude — primary product / implementation agent

Claude owns the convergent build.

Its job is to turn the current evidence and `VISION_BRIEF_V2.MD` into the strongest working scientific instrument possible without repeatedly reopening the thesis.

### Claude should focus on

- auditing the existing QC implementation against the vision;
- formalizing the minimum defensible V1 of the uncertainty field;
- modeling the fading outer rim from quantities we can actually support;
- distinguishing what can be computed now from what is only a future acquisition recommendation;
- integrating uncertainty, variance, provenance and acquisition effects into one coherent model;
- designing and implementing the Evidence Field / Launchpad-style interface;
- implementing OUTER RIM / NEXT CAPTURE / EVIDENCE SURVIVAL interactions;
- preserving the ACCEPT / INVESTIGATE / REJECT engine as the proof layer;
- exposing enough technical detail to make the interface scientifically auditable;
- integrating qte77 findings only when they materially improve the canonical uncertainty model;
- preparing and hardening the demo path;
- testing and fixing the implementation.

### Claude should not spend expensive reasoning on

- broad literature exploration;
- speculative lists of possible scientific features;
- instrumentation catalogues;
- repeated re-derivation of the product thesis;
- cosmetic UI changes that do not affect the demo;
- parallel epistemological frameworks.

Claude is now primarily a **convergence engine**.

Its expensive reasoning should end in a design decision, formal model, working implementation, verified correction, or demo improvement.

---

## 3. qte77 — adversarial scientific expansion layer

qte77 owns the recursive research and measurement-space expansion workstream.

He should operate deliberately **perpendicular** to Claude.

His role is to challenge what the current uncertainty model fails to represent.

### qte77 should ask

- What consequential source of variance are we not modeling?
- Where may the current outer rim be falsely narrow?
- What structure may already exist in the SEM data that our current features fail to expose?
- What scientifically grounded descriptor or physical proxy could be extracted from the current dataset?
- What uncertainty cannot be resolved from the current data at all?
- What new measurement, modality, technology or parallel dataset could resolve that failure state?
- Does that new data source have enough orthogonal information value to justify the cost of obtaining it?

### qte77 has two output classes

#### A. Inference extensions from existing data

Find scientifically defensible dimensions that may already be latent in the current dataset:

- spatial statistics;
- morphology descriptors;
- topology;
- texture;
- clustering;
- characteristic length scales;
- scale-dependent measures;
- cross-detector relationships;
- physical proxies;
- new combinations of existing measurements;
- other literature-grounded observables.

These candidates should be tested against the current data where possible.

#### B. Acquisition / parallel-data extensions

Identify new observations that could resolve important failure states that existing data cannot:

- larger coherent SEM captures;
- different magnification regimes;
- repeat acquisitions;
- adjacent sections;
- EDS;
- tomography;
- alternative microscopy modes;
- process telemetry;
- composition data;
- mechanical / electrochemical measurements;
- other scientifically justified parallel datasets.

A new technology is **not** valuable because it is interesting.

It should be promoted only when it addresses a consequential uncertainty and reaches **critical mass of unlocked value**.

---

## qte77 acceptance gate

A research lead should matter to the product only if it does at least one of the following:

- reveals meaningful variance the current model misses;
- explains variance we already observe;
- proves the current outer rim should be wider;
- shrinks an important blindspot;
- distinguishes nuisance from material signal;
- changes the highest-value next acquisition;
- introduces a parallel dataset with enough orthogonal information gain to justify its acquisition burden.

Otherwise it remains a research note or is discarded.

The governing loop is:

**failure state → missing information → literature search → candidate inference / measurement → test or estimate information gain → update uncertainty field**

---

## qte77 output format

Do not send Claude large undifferentiated research dumps.

Each candidate should be compressed into a small structured artifact:

### HYPOTHESIS
What might the current model be missing?

### FAILURE STATE
Which consequential blindspot / uncertainty does this correspond to?

### SCIENTIFIC EVIDENCE
What does the literature actually support?

### CURRENT-DATA TEST
Can we test or derive this from the dataset we already have?

### OUTER-RIM EFFECT
Would it widen, shrink or reshape the uncertainty field?

### NEXT MEASUREMENT
If current data cannot resolve it, what observation would?

### VALUE / CRITICAL MASS
Why is this worth adopting relative to its cost?

### STATUS
**REJECT / TEST NOW / FUTURE CAPTURE / HIGH-VALUE NEW DATASET**

Claude should primarily consume:

- **TEST NOW**;
- **HIGH-VALUE NEW DATASET**;
- and findings that invalidate an assumption already used in the product.

---

## 4. Shared interface between the workstreams

Both streams update the same object.

### Product / measurement loop

**current data → uncertainty field → outer rim → dominant blindspot → next capture → updated field**

### Research / discovery loop

**scientific literature → candidate missing variance / observable / measurement → test → updated field**

qte77 may discover that the uncertainty field is too narrow.

That is not a failure.

The correct recursive behavior is:

**discover missing uncertainty → expand the outer rim → acquire or infer new evidence → constrain it again**

Claude then incorporates the result into the product only when it is technically defensible and useful to the demo or core model.

---

## 5. Token allocation principle

### qte77: exploration-heavy

qte77 has the large exploratory budget.

Spend it on:

- papers;
- cross-sectional audits;
- failed hypotheses;
- new candidate observables;
- adversarial checks;
- alternative measurement technologies;
- identifying where the variance model itself is incomplete.

High failure rate is acceptable here.

### Claude: convergence-heavy

Claude should use high reasoning selectively for:

- the uncertainty-field formalization;
- difficult statistical / architectural decisions;
- integration of proven qte77 findings;
- hero UX logic;
- implementation;
- testing;
- demo hardening.

Do not spend the highest effort on routine refactors, CSS, or broad literature search.

### Guilhem: selection

Guilhem's scarce resource is attention.

Use it to:

- choose;
- cut;
- frame;
- decide what is special;
- protect conceptual coherence;
- decide whether a qte77 discovery has critical mass;
- shape the final demo.

---

## Immediate split

### Guilhem + Claude now

1. Read `docs/VISION_BRIEF_V2.MD`.
2. Audit the current implementation against it.
3. Define the smallest mathematically defensible V1 of:
   - uncertainty field;
   - fading outer rim;
   - blindspot classification;
   - expected next-capture value.
4. Implement the Evidence Field / hero interface.
5. Preserve and expose the existing QC proof layer.
6. Build the demo around one clear recursive story.

### qte77 now

1. Audit the current variance model for missing dimensions.
2. Search literature for candidate inferential dimensions extractable from the current SEM dataset.
3. Test the strongest candidates where possible.
4. Identify consequential failure states the existing dataset cannot resolve.
5. Find acquisition / parallel-data approaches that address those failure states.
6. Apply the critical-mass gate.
7. Return compact candidate briefs rather than product code or broad research summaries.

---

## Final rule

> **Claude builds the best product from what we currently know. qte77 searches for scientifically grounded reasons why what we currently know is incomplete. Guilhem decides what becomes the product.**

No duplicated exploration. No parallel epistemologies. One uncertainty field.
