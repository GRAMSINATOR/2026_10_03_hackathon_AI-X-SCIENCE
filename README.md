# PARALLAX

**An epistemic acquisition controller for microscopy.**

Parallax uses each incoming microscopy batch for two jobs at once:

1. **material QC:** detect whether the incoming material departs from a configured reference; and
2. **dataset self-audit:** ask whether the current sampling, capture geometry, modalities and reference population are actually strong enough to support the inference being made.

The broader product thesis is to challenge the dataset's current representation: identify structured limits, define
new observational handles, test what can be extracted now, and map which additional measurements would unlock
valuable marker families.

An incoming batch is not only something to classify. It is a **probe of the measurement regime itself**.

> **What survives scrutiny? Where does the current dataset stop constraining the problem? What should the microscope measure next?**

The Polaron Track 4 battery-electrode challenge is the proving ground. It gives Parallax a real SEM dataset, a concrete QC decision, acquisition confounders, small-(n) reference support and an unseen-batch generalisation requirement.

The sponsor-style ACCEPT / INVESTIGATE / REJECT decision is therefore an important proof substrate, but it is **not the product identity**. Parallax is designed to continue after the verdict: it challenges the evidence, exposes the assumptions that the batch has stressed, and turns those limits into the next acquisition policy.

---

## The product in one loop

```text
incoming microscopy
        ↓
reconstruct what is actually independent
        ↓
measure interpretable material markers
        ↓
compare with the configured reference
        ↓
challenge apparent deviations
(acquisition · spatial consistency · validity · provenance)
        ↓
identify the evidence that survives
        ↓
stress-test the dataset assumptions
(scale · spatial extent · population · modality · acquisition)
        ↓
choose what to measure next
        ↓
repeat with a better-shaped dataset
```

Longer term, Parallax sits between a scientific agent and microscope control:

```text
scientific objective / lab agent
        ↓
PARALLAX — measurement policy under uncertainty
        ↓
microscope / instrument control
        ↓
measurement
        ↓
analysis
        ↓
updated evidence state
        ↺
```

The microscope knows **how** to move, image, zoom or switch modality. Parallax decides **whether that is the right next observation and why**.

---

# What Parallax is trying to determine

Parallax is **not** primarily asking:

> “Is this batch good enough?”

It asks:

> **“What does this batch reveal about the adequacy of the dataset and acquisition strategy we are using to judge it?”**

For example, a batch may reveal that:

- a conclusion rests almost entirely on one independent section;
- adjacent fields are spatially redundant;
- the relevant structure approaches the field-of-view boundary;
- the signal piles up at the current resolution floor;
- morphology is visible but chemistry is not measured;
- an apparent anomaly can be reproduced by acquisition changes;
- the reference population is too small to support prevalence claims;
- or a measurement is simply invalid at the present contrast/noise level.

Those are not merely caveats attached after a classifier. They are **inputs to the next acquisition decision**.

---

# The four human questions

The main interface is organised around four questions.

### 1. Dataset self-audit

**Are the assumptions behind the current dataset holding?**

This is about independence, reference support, leverage, coverage and whether the current capture regime can support the inference being attempted.

It is deliberately different from “material passed QC”.

### 2. Surviving signal

**What pattern remains after plausible nuisance explanations are challenged?**

Finding differences in microscopy is easy. Parallax tries to eliminate differences that can be explained by acquisition, spatial inconsistency, invalid measurement or pseudoreplication.

### 3. Open limits

**What is still preventing a stronger inference?**

The current implementation tracks typed limits rather than collapsing everything into one confidence score.

Examples:

| Open limit | Meaning | Typical next action |
|---|---|---|
| **Resolution** | relevant objects approach the current detection floor | zoom / higher-resolution capture |
| **Chemistry** | morphology is visible but chemical identity is not measured | EDS / another compositional modality |
| **Extent** | the signal remains open at the captured boundary | extend the coherent mosaic |
| **Prevalence** | too few independent sections constrain lot-wide prevalence | sample independent sections |
| **Acquisition** | imaging conditions could still explain the signal | repeat under controlled settings |
| **Validity** | the KPI is not reliably measurable in the current image | reacquire / change measurement |

### 4. Next acquisition

**What observation would most directly resolve the consequential limit?**

Parallax can recommend:

- repeat the decisive region under controlled settings;
- increase magnification;
- increase coherent capture area;
- sample a spatially independent section;
- change detector or modality;
- add EDS;
- expand the reference population;
- or stop acquiring more of the same kind when nothing observed justifies it.

The goal is not “more data”.

The goal is **the right shape of data for the decision**.

---

# Scientific process

## 1. Reconstruct provenance before statistics

The raw dataset contains fields, but fields are not automatically independent samples.

Reconnaissance found that the 31 fields are tiles from **13 parent micrographs**. Several parent sections cross batch-folder boundaries. Treating every field as independent would therefore pseudoreplicate the evidence.

Parallax reconstructs parent micrographs and tile order from image metadata and edge continuity, then performs batch statistics at the **parent-micrograph level**.

Tile-to-tile variation is retained as spatial sampling information rather than promoted to fake sample size.

This provenance correction is one of the reasons the controller can challenge sampling assumptions instead of merely consuming folder labels.

---

## 2. Extract interpretable measurements

The current SEM pipeline measures a compact set of morphology/QC markers from BSE imagery:

- high-Z / BSE-bright area fraction;
- median bright-particle equivalent diameter;
- bright-particle number density;
- porosity;
- pore size;
- in-plane solid chord length.

The system also records acquisition fingerprints such as black level, contrast, clipping, noise and sharpness.

A measurement can be **withheld** when the validity conditions are not met. “Not measurable” is a valid scientific outcome.

---

## 3. Build the configured reference model

For each measurable KPI, Parallax estimates the reference population at the parent-micrograph level.

The current model is deliberately simple and auditable:

- between-reference-micrograph variation;
- within-micrograph / tile-sampling noise;
- finite-reference support;
- simulation-calibrated 95% / 99% prediction thresholds.

The batch-level sponsor verdict combines simulated severity and count tests.

This is a frequentist model. It is **not** an LLM confidence score and is not presented as a Bayesian posterior.

---

## 4. Challenge apparent deviations

An observation being outside the reference envelope is not enough.

Parallax asks whether it survives:

- **measurement validity**;
- **tile / field consistency**;
- **acquisition perturbation tests**;
- **provenance / independence correction**;
- **KPI robustness**;
- and **decision leverage**.

A useful way to summarise the philosophy is:

> **Signal first. Falsification second. Attribution last.**

Weak apparent differences are expected to disappear.

That is a feature, not a failure.

---

## 5. Measure decision leverage

The system recomputes the batch decision when decisive evidence is removed.

This answers:

> “Is the batch conclusion broad, or does it rest on one observation?”

That distinction matters directly for the next acquisition.

If one micrograph carries the decision, the response should usually be **verify that micrograph and estimate prevalence**, not make a broad supplier claim.

---

## 6. Challenge dataset composition and capture geometry

Once a signal survives, Parallax asks whether the dataset itself is shaped correctly to constrain it.

The current field model tracks support including:

- independent sample count;
- spatial dependence;
- coherent capture extent;
- resolution / detection floor;
- acquisition coverage;
- modality coverage;
- baseline support;
- missing composition;
- and measurement validity.

Internally these are represented as typed support boundaries. The UI turns them into concrete sampling questions rather than one abstract “uncertainty score”.

---

## 7. Convert limits into acquisition policy

Every recommended acquisition should answer three things:

1. **what limit it addresses;**
2. **why that limit matters to the current inference;**
3. **why this observation is more informative than simply collecting more of the same.**

The current controller is intentionally transparent and rule-based. It does **not** fabricate numerical information-gain scores that the present dataset cannot support.

---

# What the current dataset demonstrates

> **Reference configuration note:** the demo build currently configures **Batch_1** as the reference. The challenge description available in this repository states that teams receive one baseline batch plus incoming batches, but the text we have does not itself prove that the numbered folder called `Batch_1` is the organiser-designated baseline. Treat the mapping as configuration and verify it against the official dataset instructions before making an external “approved Batch_1” claim. If another folder is designated as baseline, rebuild the reference against that folder.

The reference is now an explicit scientific coordinate frame. Batch_1, Batch_2 and Batch_3 each satisfy the current parent/KPI/spatial-support eligibility rules and are cached independently. `Hackathon-Polaron-test` remains a valid target, but is disabled as a reference because it has only three parent micrographs, fewer than three additive-valid parents, inadequate robustness acquisitions and insufficient spatial support. The top-level controls keep **DATASET** and **REFERENCE FRAME** separate, and the field contract records the active frame, every candidate’s support, and the joint comparison across all eligible frames.

Cross-reference comparison is exploratory rather than a membership classifier. It holds target measurements fixed, recomputes reference-relative envelopes and decisions, and reports invariant and frame-dependent findings together so switching cannot be used as significance shopping.

With the current `Batch_1` reference configuration:

| Batch | Current engine result | What the evidence actually says |
|---|---|---|
| **Batch_1** | configured reference | 5–6 usable reference micrographs depending on KPI; M2316 fails additive measurement validity because contrast-to-noise is too low |
| **Batch_2** | ACCEPT, p = 1.0 | its **3 independent** incoming micrographs are within the current reference range; 3 additional images are reference-linked continuations and carry no independent weight; support is therefore thin |
| **Batch_3** | REJECT, p = 0.017 | one robust surviving signal is concentrated in M2060; the verdict changes without it, so the result is decision-significant but highly leveraged |
| **Hackathon-Polaron-test** | INVESTIGATE, p = 1.0 | all measured KPIs are in family, but only **2 independent** incoming micrographs remain after M2316 is recognized as a reference-linked continuation; one more independent cross-section is required to certify the batch |

### Batch 3: the surviving evidence

M2060 contains:

- **34.4** detected fine BSE-bright objects / 1000 µm²;
- reference mean **19.5** / 1000 µm²;
- about **+77%** particle number density;
- unchanged bright-phase area fraction;
- consistency in 3 of its 4 tiles;
- a shift much larger than the tested synthetic acquisition perturbations.

The important claim is:

> **M2060 contains a robust morphology shift under the current model.**

The system does **not** claim that the supplier changed formulation, that the whole lot is affected, or that the bright phase has a known chemistry.

Without M2060, Batch 3 becomes ACCEPT under the current rule.

That leverage is precisely why the next action is not “declare supplier failure”; it is to challenge the measurement and sampling assumptions around M2060.

---

# What Batch 3 challenges about the dataset

The surviving M2060 signal exposes several open questions.

### Resolution

Most of the excess bright-particle population sits near the current particle-detection floor.

**Interpretation:** the current scale may be truncating the population we are trying to describe.

**Action:** acquire higher-magnification BSE.

### Chemistry

The deviating population is visible as BSE-bright / high-Z contrast, but chemistry was not acquired.

**Interpretation:** more BSE morphology cannot establish chemical identity.

**Action:** use EDS or another compositional measurement if attribution matters.

### Extent

The density remains outside the selected reference local band at the edge of the coherent captured section.

**Interpretation:** the current capture does not bound the spatial extent of the signal.

**Action:** extend the coherent mosaic rather than adding an unrelated random crop.

### Prevalence

The batch-level finding is concentrated in one independent micrograph.

**Interpretation:** the current dataset can flag the event, but it does not tightly establish lot-wide prevalence.

**Action:** acquire additional **independent cross-sections**, not merely adjacent tiles.

### Acquisition

The decisive micrograph differs from the reference acquisition fingerprint on several recorded image statistics.

Synthetic perturbation tests explain little of the observed additive-density effect, but not every physical microscope setting was available in metadata.

**Interpretation:** the cleanest falsification step is still to repeat M2060 under controlled reference settings.

**Action:** **VERIFY FIRST**.

---

# Current acquisition policy for Batch 3

The present action sequence is:

```text
1. REPEAT M2060 under controlled / reference acquisition conditions
2. ZOOM to resolve the fine-particle scale
3. EDS if chemical attribution is required
4. EXTEND the coherent M2060 capture where the signal remains open
5. acquire INDEPENDENT SECTIONS to constrain prevalence
```

This sequence is not meant as a universal recipe.

It is generated from the current evidence state and the limits that evidence exposes.

---

# Agentic Marker Frontier: expanding what the lab can perceive

Parallax has a second recursive loop.

The acquisition controller can discover that the **current vocabulary of measurements is itself incomplete**.

A **marker** is a defined quantitative, qualitative or hybrid protocol for perceiving a scientifically meaningful
property. It may be a scalar, distribution, spatial field, categorical phenotype, relation or topology. Structured
limits in the current representation become **inquiry vortices**: reasons to investigate, rather than automatic
defects or anomalies.

Examples might include:

- a morphology descriptor recoverable from existing SEM;
- a clustering statistic;
- a cross-detector relationship;
- chemical identity;
- 3-D pore connectivity.

The **AGENTIC MARKER FRONTIER** separates three questions.

## A. What should be investigated first?

**CURRENT FRONTIER** is a short deterministic attention order. The visible factors state why each opportunity is
near the top. It is a research-priority ranking, not a truth, certainty or confidence score.

## B. Can we test a useful marker with what we already capture?

```text
current blindspot
    ↓
candidate marker
    ↓
scientific evidence
    ↓
test measurability + confounds on current data
    ↓
test its value, robustness and complementarity
```

Candidates are split into **COMPUTABLE / TESTABLE NOW**, **NEEDS TARGETED CAPTURE**, and **REQUIRES NEW
OBSERVABILITY**. This keeps representation search distinct from NEXT CAPTURE, which optimises the immediate decision.

## C. Do inaccessible marker opportunities justify an observability expansion?

```text
multiple useful markers
    ↓
all require a capability the lab lacks
    ↓
literature + blindspot relevance + non-substitutability accumulate
    ↓
scoped capability payload and acquisition-roadmap opportunity
```

For example, multiple chemistry-related marker needs can accumulate into a case for **EDS / elemental mapping**.

The point is not to count papers.

The point is:

> **Do valuable marker opportunities converge on information the current workflow cannot observe, with enough evidence
> and no adequate substitute to justify evaluating a new capability?**

The resulting **OBSERVABILITY EXPANSION** section is a marker-pool argument, not an equipment wishlist. It shows what
the capability would expose, which inquiry vortices it addresses, why current data are insufficient, and its burden
and alternatives. The renderer-independent `marker-frontier/1` contract also exposes a roadmap for downstream agents:
test current-data protocols, make targeted captures, evaluate observability expansion, then re-observe.

The research / literature agent proposes Marker and Capability cases. It does **not** silently modify the validated controller.

qte77's parallel research/evaluation repository is:
[qte77/2026-10-03-london-ai-science-hack](https://github.com/qte77/2026-10-03-london-ai-science-hack).

---

# Proof and governance

Parallax is intentionally designed so the attractive interface is **not the source of scientific truth**.

```text
scientific computation
        ↓
epistemic-field/1
        ↓
deterministic human decision brief
        ↓
renderer
        ↓
click-through proof
```

## Scientific contract

`epistemic-field/1` contains the actual structured state:

- observations;
- measured dimensions;
- reference relations;
- scrutiny outcomes;
- leverage;
- typed support limits;
- missing dimensions;
- acquisition actions;
- provenance.

Each production dimension also declares a marker-specific uncertainty adapter: bounded phase fractions use raw and
p(1−p)-normalised local-window fluctuation, particle density uses equal-area number variance and Fano, and distributional
markers retain parent-cluster protocols. Spatial profiles distinguish 25 µm context columns from the unsmoothed 100 µm
local means compared with the descriptive parent-bootstrap reference envelope.

The renderer does not decide whether a signal survives or which action is scientifically justified.

## Human brief

A deterministic decision-brief layer selects the smallest non-redundant set of consequential claims.

Every visible claim carries proof references back to the field.

An optional LLM compositor seam exists for wording, but it may only compress already-approved facts. It may not alter:

- scientific state;
- numbers;
- proof references;
- action policy;
- verdict;
- support classification.

The demo does not require an LLM to decide the science.

## Examiner Control Matrix

The keyboard-like Examiner surface is the forensic view.

The five lenses expose the same evidence through different questions:

```text
SIGNAL       what appears different?
SCRUTINY     what survives attempts to explain it away?
FIELD        what is producing the current support / uncertainty structure?
OUTER RIM    which measurement assumptions are currently limiting?
NEXT CAPTURE what observation addresses those limits?
```

Clicking a human-facing conclusion traces to the corresponding observation, proof and acquisition rationale.

## Negative evidence is preserved

The system records branches that failed rather than hiding them.

Current examples:

- pseudotime / latent progression was tested and rejected as acquisition-sensitive;
- multiscale scaling exponents did not discriminate usefully;
- learned-embedding novelty was acquisition-sensitive;
- apparent Batch 3 deviations that failed consistency or nuisance scrutiny are not promoted as surviving evidence.

---

# What we can and cannot claim

## Supported by the current dataset / implementation

- raw fields contain substantial provenance dependence and cannot be treated as independent samples;
- the current pipeline can reconstruct parent-micrograph structure and use micrographs as the statistical unit;
- some KPIs are measurably more robust to acquisition perturbation than others;
- M2060 has a strong fine BSE-bright particle-density deviation under the current configured reference model;
- the current Batch 3 decision is highly leveraged by M2060;
- the current capture leaves consequential questions about scale, chemistry, extent and prevalence;
- those questions map to concrete acquisition actions;
- Batch 2's independent observations are within the current configured reference range, but the effective independent sample count is small.

## Not supported

Do **not** claim:

- chemical identity of the BSE-bright phase without EDS;
- supplier formulation change;
- lot-wide prevalence from the present Batch 3 sampling;
- 3-D particle size or tortuosity from these 2-D sections;
- a material trajectory / pseudotime axis;
- universal validity across materials or microscopes;
- optimal Bayesian experimental design;
- that unobserved variance is impossible because no current limit was detected.

The strongest version of “enough data” Parallax should make is:

> **No current observation justifies expanding this same acquisition regime for this stated decision.**

That is a stopping rule, not a claim that nothing unknown exists.

See `docs/CLAIMS.md` and `docs/RESEARCH_LOG.md` for the detailed evidence record.

---

# Interface

The current renderer is intentionally styled as one physical laboratory instrument rather than a SaaS dashboard.

Its major surfaces are:

- **machine status** — compact configured-reference / sponsor-QC state;
- **human readout** — dataset self-audit, surviving signal, open limits, next acquisition;
- **Examiner Control Matrix** — detailed proof/challenge surface;
- **Imaging / Inspection Bay** — registered microscopy, segmentation and spatial profiles;
- **Agentic Marker Frontier** — ranked marker research, observability gaps and capability-pool roadmap;
- **Service Hatch** — raw statistical proof.

The scientific state remains renderer-independent.

See `docs/RENDERER_INSTRUMENT.md`.

---

# Quick start

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt

# Put sponsor TIFFs under data/<Batch>/

# Build independent cached reference candidates and explicitly activate one.
python -m qc references data/Batch_1 data/Batch_2 data/Batch_3 data/Hackathon-Polaron-test --activate Batch_1

# Evaluate each unchanged target against every eligible frame.
python -m qc compare-references data/Batch_1 --active Batch_1
python -m qc compare-references data/Batch_2 --active Batch_1
python -m qc compare-references data/Batch_3 --active Batch_1
python -m qc compare-references data/Hackathon-Polaron-test --active Batch_1

# Build the Evidence Instrument
(cd renderer && npm install && npm run build)

# Run the application
streamlit run app.py
```

### Unseen batch

```bash
python -m qc compare-references data/<NewBatch> --active Batch_1
```

The pipeline automatically:

- discovers detector variants;
- reconstructs parent-micrograph linkage where possible;
- extracts features;
- applies validity gates;
- evaluates the target against each eligible, explicitly cached reference frame;
- proves that intrinsic target quantities have the same digest across frames;
- records reference-sensitive and reference-invariant findings without assigning batch membership;
- builds `epistemic-field/1`;
- derives the human brief;
- emits acquisition actions.

A different pixel size disables incompatible physical-size KPIs rather than silently comparing incomparable values.

---

# Public hosting: derived results only

```bash
python -m qc provenance
python -m qc bundle public_bundle

QC_PUBLIC=1 \
QC_REF=public_bundle/reference.json \
QC_REPORTS=public_bundle/reports \
QC_CACHE=public_bundle/cache/fields \
streamlit run app.py
```

The public bundle is designed to expose derived results without publishing sponsor microscopy imagery. Imagery is withheld unless explicitly enabled, while derived profiles, extents, limits and actions remain available.

See `docs/PUBLIC_MODE.md`.

---

# Repository structure

- `qc/` — image discovery, segmentation, marker extraction, provenance, statistics, robustness, field contract, human brief and acquisition policy.
- `renderer/` — Evidence Instrument / Examiner UI. It reads the scientific contracts; it does not make scientific decisions.
- `app.py` — application shell / Streamlit host.
- `docs/VISION_BRIEF_V2.MD` — long-form product architecture and agentic-lab thesis.
- `docs/DECISION_BRIEF.md` — governed human-summary contract.
- `docs/RENDERER_INSTRUMENT.md` — renderer architecture and visual semantics.
- `docs/RESEARCH_LOG.md` — experiments, negative results and interpretation.
- `docs/CLAIMS.md` — claims that are and are not supported.
- `work/` — reconnaissance, QA and analysis scripts.
- `fixtures/` / reports — deterministic scientific / renderer fixtures where present.

---

# Track 4 proof vs longer-term product

Polaron asks whether incoming material has changed relative to a baseline and whether that decision can be made interpretably and honestly.

Parallax satisfies that substrate, but the larger thesis is:

> **Autonomous microscopes need a layer that can recognise when the present dataset is insufficient, identify which sampling assumption failed, and change the measurement policy accordingly.**

The current hackathon prototype demonstrates the beginning of that loop on real SEM data.

It is **not yet** a universally validated autonomous-microscopy controller.

It is a working measurement-policy prototype with explicit provenance, falsification, support limits, acquisition recommendations and a governed path for expanding what the lab can measure.

---

## Licence and data

Code is licensed under Apache-2.0 (`LICENSE`).

Sponsor-provided datasets and imagery derived from them are excluded from the code licence and remain subject to their original rights and terms (`NOTICE`).
