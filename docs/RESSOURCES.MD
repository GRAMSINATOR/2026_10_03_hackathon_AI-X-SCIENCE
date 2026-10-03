# RESSOURCES

## Purpose

This file tracks existing libraries, repositories, products and research directions that overlap with pieces of the project.

The goal is **reuse, not imitation**.

We are not claiming to invent uncertainty quantification, active learning, adaptive microscopy, autonomous laboratories, spatial statistics or microscopy automation.

The product thesis in `VISION_BRIEF_V2.MD` is about how those pieces can be assembled into an **epistemic acquisition controller**: a layer that reasons about the limits of the current dataset and decides how the observational space should expand.

---

# 1. Core adjacent landscape

## Polaron

**What it is:** materials intelligence / microscopy analysis platform connecting processing, microstructure and performance.

**Why it matters:** this is the direct application context. Polaron already cares about quantitative microstructure, uncertainty, failure modes and prioritising valuable experiments. Therefore our differentiation cannot simply be "microscopy + uncertainty."

**Useful for us:**
- understand the product context;
- keep the QC proof layer materially relevant;
- compare our epistemic-acquisition framing against what Polaron already offers.

Links:
- https://www.polaron.ai/
- https://www.polaron.ai/platform
- https://www.polaron.ai/newsroom/launching-academic-partnerships

---

# 2. Bayesian active learning / autonomous experiment design

## gpCAM

Berkeley Lab Gaussian-process / autonomous experimentation stack.

**Relevant capabilities:**
- Gaussian-process uncertainty;
- ask/tell/train loops;
- acquisition functions;
- Bayesian optimisation;
- custom kernels and noise models;
- multi-task / non-trivial search spaces.

**Potential use:** formal machinery for NEXT CAPTURE and expected-information-gain style acquisition decisions.

**Important distinction:** gpCAM usually assumes the search / measurement space is already defined. Our recursive layer also asks whether the **measurement space itself is incomplete or badly shaped**.

- https://gpcam.lbl.gov/
- https://github.com/lbl-camera/gpCAM

## BoTorch

PyTorch Bayesian optimisation library.

**Potential use:** acquisition functions, expected improvement / information-style objectives, constrained optimisation, multi-objective experimental design.

- https://botorch.org/
- https://github.com/pytorch/botorch

## Xopt

Autonomous optimisation / experiment design toolkit.

**Potential use:** optimisation and exploration patterns, heteroskedastic noise, multi-fidelity reasoning, interfaces for experimental controls.

- https://github.com/xopt-org/Xopt
- https://xopt.xopt.org/

## Bluesky Adaptive

Adaptive experiment orchestration built around agent-like ingest / suggest / report loops.

**Potential use:** clean architectural precedent for a future controller boundary between:
- incoming scientific data;
- acquisition-policy agent;
- instrument execution.

- https://blueskyproject.io/bluesky-adaptive/
- https://github.com/bluesky/bluesky-adaptive

## HELAO

High-throughput experimentation / autonomous-lab orchestration.

**Potential use:** reference architecture for connecting multiple instruments and analysis services in autonomous experimental workflows.

- https://github.com/High-Throughput-Experimentation/helao-async

---

# 3. Spatial uncertainty, correlation and dataset geometry

These are especially relevant to the **fading outer rim** and the question:

> Do we need more samples, or do we need a differently shaped capture?

## GSTools

Geostatistical toolbox for:
- covariance models;
- variograms;
- kriging;
- conditioned random fields;
- spatial simulations.

**Potential use:** estimate characteristic spatial scales, correlation lengths and how uncertainty behaves with coherent capture area.

- https://github.com/GeoStat-Framework/GSTools
- https://geostat-framework.readthedocs.io/projects/gstools/

## scikit-gstat

Variogram / spatial statistics library.

**Potential use:** test whether current SEM fields are smaller than important spatial correlation scales; estimate effective range and redundancy.

- https://github.com/mmaelicke/scikit-gstat
- https://scikit-gstat.readthedocs.io/

## PySAL

Spatial-analysis ecosystem.

**Potential use:** broader spatial autocorrelation / neighbourhood statistics if useful beyond simple variograms.

- https://pysal.org/
- https://github.com/pysal/pysal

---

# 4. Uncertainty quantification, calibration and distribution shift

These are parts bins rather than the product centre.

## MAPIE

Conformal prediction and risk-control toolkit.

**Potential use:**
- prediction intervals;
- calibrated uncertainty;
- conformal risk-control ideas;
- checking exchangeability assumptions.

Useful given the small, partially correlated baseline.

- https://github.com/scikit-learn-contrib/MAPIE
- https://mapie.readthedocs.io/

## Uncertainty Toolbox

Calibration, sharpness, scoring and recalibration utilities.

**Potential use:** sanity-check uncertainty outputs rather than inventing calibration metrics.

- https://github.com/uncertainty-toolbox/uncertainty-toolbox

## Alibi Detect

Outlier and distribution-drift detection.

**Potential use:** OOD / drift components when deciding whether a sample is outside supported baseline space.

- https://github.com/SeldonIO/alibi-detect
- https://docs.seldon.io/projects/alibi-detect/

---

# 5. Microscopy / scientific-image analysis stacks

## AtomAI

ORNL microscopy / spectroscopy ML toolkit.

Includes segmentation, representation learning, VAEs, deep-kernel methods and defect-oriented analysis.

**Potential use:** candidate feature extraction and scientific-image ML components. Also useful for qte77 when searching for inference dimensions already recoverable from the images.

- https://github.com/pycroscopy/atomai

## HyperSpy

Multidimensional scientific data analysis, especially microscopy / spectroscopy.

**Potential use:** future multimodal handling if SEM images become paired with spectroscopy / EDS or related multidimensional measurements.

- https://github.com/hyperspy/hyperspy
- https://hyperspy.org/

## LiberTEM

High-throughput electron-microscopy data processing, including live / streaming use cases.

**Potential use:** future real-time analysis substrate if the acquisition controller ever closes the loop directly against live electron-microscopy streams.

- https://github.com/LiberTEM/LiberTEM
- https://libertem.github.io/

## napari

Open-source multidimensional image viewer / plugin ecosystem.

**Potential use:** future integration surface for scientists.

**Not recommended for the hackathon hero UI:** our Evidence Field / Launchpad interaction is intentionally more specialised than a conventional image viewer.

- https://napari.org/
- https://github.com/napari/napari

---

# 6. Adaptive microscopy / acquisition systems

## SBEMimage

Open-source SEM acquisition software with automated acquisition, QC and adaptive tile handling.

**Potential use:** precedent for microscopy acquisition software and adaptive sampling.

- https://sbemimage.github.io/SBEMimage/
- https://github.com/SBEMimage/SBEMimage

## Gently

Open-source agentic microscope / instrument-control project associated with the Janelia ecosystem.

**Relevant idea:** expose microscope functions to agents, generate experiment plans, use perception agents, safety limits and Bluesky-style control.

**Potential use:** this is one of the closest architectural neighbours to a future agentic-lab deployment.

**Difference from us:** Gently is primarily about giving agents microscope capabilities. Our centre is the **measurement-policy / epistemic decision layer** deciding how observation should expand under uncertainty.

- https://github.com/gently-project/gently

## Python-Microscope

Python interfaces for microscope hardware.

**Potential use:** future hardware integration abstraction.

- https://github.com/python-microscope/microscope
- https://python-microscope.org/

## PyMeasure

Python toolkit for scientific instruments and experiment procedures.

**Potential use:** generic instrument-control reference if the product later crosses beyond microscopy.

- https://github.com/pymeasure/pymeasure
- https://pymeasure.readthedocs.io/

---

# 7. Commercial / vendor acquisition references

These are useful for understanding what execution capabilities already exist. We should not reinvent them.

## Oxford Instruments — AZtecFeature

Automated feature / particle analysis and large-area acquisition, including EDS workflows.

**Potential use:** precedent for automated microscope motion + feature detection + compositional follow-up.

- https://nano.oxinst.com/aztecfeature

## Thermo Fisher — AutoScript

Python control / automation interfaces for electron microscopes.

**Potential use:** demonstrates that a higher-level acquisition-policy controller can plausibly sit above commercial microscope APIs.

- https://www.thermofisher.com/in/en/home/electron-microscopy/products/software-em-3d-vis/autoscript-tem-software.html

## ZEISS — ZEN core

Microscopy acquisition, segmentation, analysis, correlation and scripting.

**Potential use:** commercial reference for integrated acquisition / analysis workflows.

- https://www.zeiss.com/microscopy/en/products/software/zen-core.html

## TESCAN — automated / panoramic acquisition

TESCAN systems include automated large-area and high-resolution SEM acquisition workflows.

**Potential use:** concrete example of the execution capability our layer could direct.

- https://www.tescan.com/

## Fovea Lab

Commercially positioned "intelligence layer" for quantitative imaging and adaptive acquisition.

**Potential use:** close product-neighbour for understanding how adaptive acquisition is framed commercially.

**Difference to preserve:** our distinctive frame is the **epistemic boundary of the dataset itself** and recursively deciding whether the observation vocabulary must expand.

- https://www.fovealab.com/
- https://www.fovealab.com/adaptive-acquisition

---

# 8. Relevant research directions / papers

## Bayesian Active Learning for Scanning Probe Microscopy

Review / framework work around Gaussian processes, deep-kernel learning, automated experimental choice and microscopy.

**Why it matters:** establishes that "uncertainty → choose next observation" is an existing scientific lineage that we should build on rather than claim as novel.

Search / reference:
- Bayesian Active Learning for Scanning Probe Microscopy
- ACS Nano, 2022

## Quality-controlled active learning for autonomous microscopy

2026 autonomous-microscopy work explicitly addressing quality control in active-learning loops.

**Why it matters:** close to our concern that an autonomous acquisition system must not confidently steer itself using poor or misleading observations.

- https://www.nature.com/articles/s41524-026-02248-x

## Agentic / autonomous electron microscopy

Recent work on agents that reason, plan and iteratively operate microscopy workflows.

**Why it matters:** validates the broader direction of agentic microscopes / labs while leaving room for a specialised measurement-policy layer.

Search term:
- "agentic electron microscopy"
- "autonomous electron microscopy"
- "thinking microscope"
- "closed-loop microscopy Bayesian active learning"

---

# 9. How the landscape fits our stack

The current landscape already contains strong components for almost every individual layer:

**materials intelligence**
→ Polaron

**microscopy perception / analysis**
→ AtomAI, HyperSpy, LiberTEM

**uncertainty / OOD**
→ MAPIE, Uncertainty Toolbox, Alibi Detect

**spatial support / geometry**
→ GSTools, scikit-gstat, PySAL

**Bayesian experiment design**
→ gpCAM, BoTorch, Xopt

**adaptive orchestration**
→ Bluesky Adaptive, HELAO

**agentic / adaptive microscopy**
→ Gently, SBEMimage, Fovea, vendor APIs

**instrument execution**
→ AutoScript, Python-Microscope, ZEISS / Oxford / TESCAN stacks

The architectural gap we are targeting is the connective decision layer:

> **Given the scientific objective and the data acquired so far, what are the epistemic limits of the current observation regime, and how should the instrument's measurement policy change next?**

---

# 10. What to investigate immediately

For the hackathon, do not integrate everything above.

Highest immediate value:

### 1. GSTools / scikit-gstat

Test whether spatial correlation / characteristic scale can make the "larger coherent capture versus more samples" recommendation mathematically defensible.

### 2. gpCAM / BoTorch

Borrow the language and machinery for acquisition utility / expected uncertainty reduction rather than inventing a fake NEXT CAPTURE score.

### 3. Bluesky Adaptive

Use as an architectural reference for the future controller API:

**ingest → update epistemic state → suggest acquisition → report rationale**

### 4. Gently

Audit how current agentic microscopy systems expose instrument capabilities and planning. Identify the natural interface where our measurement-policy layer would sit.

### 5. 2026 quality-controlled active-microscopy work

Compare its notion of acquisition quality / active learning against our fading-outer-rim formulation so we do not accidentally rediscover an existing method under new language.

---

# 11. Resource-selection rule

A library or paper should enter the implementation only if it helps answer one of these questions:

1. **What uncertainty remains?**
2. **Why does it remain?**
3. **Is that uncertainty caused by the dataset's size, shape, scale, modality or support?**
4. **What measurement action would reduce it most?**
5. **Is our current list of possible measurement actions itself incomplete?**

Everything else is background research.
