# Electrode batch QC from SEM: Polaron Track 4

Detect whether an incoming batch of battery-electrode material has changed against an approved baseline. The system works
from multi-detector SEM cross-sections. It explains *what* physically changed and *how sure* it is, and outputs
**ACCEPT / INVESTIGATE / REJECT**.

## Key findings (from reconnaissance; details in `docs/RESEARCH_LOG.md`)

1. **Fields are not independent samples.** The 31 fields are tiles cut from **13 parent micrographs**. Tiles of one parent
   share their height and the exact TIFF XResolution, and their edges abut. Five parents span 2–3 batch folders. For
   example, `cfe5vt7s` (Batch 3), `r17byphk` (Batch 2) and `ffwubibz` (Batch 1) are one continuous cross-section.
   **All statistics are therefore done per micrograph**, with tile-to-tile spread treated as spatial sampling noise.
2. **Every micrograph has its own acquisition fingerprint** (black level, contrast, histogram stretching, detector set).
   Segmentation is anchored per image (affine-invariant 50% step thresholds). Each KPI's sensitivity to synthetic
   acquisition changes was *measured*, and acquisition differences are shown next to every finding.
3. **Pseudotime / latent progression was tested and is not supported.** The leading latent axis of DINOv2 embeddings
   changes with detector and normalisation and tracks black level. 85–90% of the variance sits inside a tile.
4. **The robust material signal is the high-Z (BSE-bright) additive population.** Batch 3 contains a micrograph
   (M2060) with +77% fine high-Z objects at unchanged additive loading. That is robust to tested acquisition changes
   (≤12% of the effect). Batch 2 is in family.

| Batch | Verdict | Why |
|---|---|---|
| Batch_1 | REFERENCE | approved baseline; self-audit flags M2316 (additive contrast-to-noise 3.2 < 4, so additive not measurable) |
| Batch_2 | **ACCEPT** (p = 1.0) | its 3 independent micrographs are inside the approved envelope; 3 more are continuations of approved sections (not independent), so the ACCEPT is fragile |
| Batch_3 | **REJECT** (p = 0.017) | M2060: additive number density 34.4 vs 19.5 per 1000 µm² (t = 6.7, 3/4 tiles); M2068 coarser additive and M2088 porosity +37% are outside 95% but spatially inconsistent |

## Quick start

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/Scripts/python.exe -r requirements.txt
# data: data/Batch_1, data/Batch_2, data/Batch_3 (TIFFs from the hackathon drive)
python -m qc reference data/Batch_1 --noise-from data/Batch_2 data/Batch_3   # approved reference (~2 min)
python -m qc assess data/Batch_2 data/Batch_3                                # verdicts + reports/<batch>/result.json
streamlit run app.py                                                         # interactive dashboard
```

### Unseen batch (released on day one)
1. Put its TIFFs in `data/<NewBatch>/`. Names like `img_<id>_<BSE|ETD|SE|Inlens>.tif` are expected; other names fall back to BSE.
2. Run `python -m qc assess data/<NewBatch>` (about 1 min per ~20 fields), or press **Run / refresh** in the app.
3. New tiles are automatically linked to known parent micrographs when their edges abut, so a tile that continues an
   approved micrograph is reported as such. A different pixel size switches size KPIs off through the validity gate.

## How a verdict is made

```
TIFFs → fields (BSE + SE + InLens, co-registered) → provenance (parent micrograph, tile order)
      → BSE 3-phase segmentation (pore / graphite-like matrix / high-Z additive), per-image anchors
      → KPIs per tile + 4 strips;  acquisition fingerprint;  SE-detector porosity cross-check
      → micrograph means → two-level prediction intervals vs approved micrographs
        (between-micrograph spread from baseline; tile-sampling noise pooled from replicate tiles;
         95%/99% thresholds calibrated by simulation, so coverage is real despite n = 5-6 baseline micrographs)
      → validity gate (additive contrast-to-noise ≥ 4, pixel size)
      → batch p-value = 2 × min(severity test, count test), both simulated under the approved population
      → ACCEPT / INVESTIGATE / REJECT + plain-language evidence
```

* **REJECT**: batch p < 0.05 *and* ≥1 micrograph outside the 99% envelope on a robust KPI, consistently across its tiles.
* **INVESTIGATE**: p < 0.20, any micrograph outside 99%, a moderate-robustness KPI outside 99%, a failed validity gate,
  or fewer than 3 micrographs.
* **ACCEPT**: otherwise.

| KPI | robustness (worst synthetic acquisition shift / tile-sampling SD) |
|---|---|
| High-Z additive area fraction | robust (0.16) |
| Additive median particle size (ECD) | robust (0.45) |
| Additive particle number density | robust (0.51) |
| Porosity (BSE-dark area fraction) | moderate (1.24, contrast) |
| Area-weighted pore size | moderate (0.44) |
| In-plane solid chord length | moderate (1.84, blur) |

Moderate KPIs can trigger INVESTIGATE but never REJECT on their own.

## Layout
* `qc/`: `io` (discovery, 25 nm/px from XResolution), `segment`, `features` (KPIs, acquisition, cache), `provenance`,
  `stats` (reference, two-level intervals, bootstrap decision), `explain`, `robustness`, `viz`, `pipeline`, CLI.
* `app.py`: Streamlit dashboard (verdict, evidence heatmap, material-state map, provenance mosaic, field explorer, method).
* `work/`: reconnaissance scripts (audit, tile stitching, KPI screening, perturbations, embeddings in `work/emb/`).
* `docs/RESEARCH_LOG.md` and `docs/CLAIMS.md`: what was tested, and what can and cannot be claimed.
