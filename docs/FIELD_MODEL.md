# Uncertainty field V1: formal specification

One object (`qc/field.py` → `reports/<batch>/field.json`, contract `epistemic-field/1`; see
`docs/REPRESENTATION_CONTRACT.md`). Every NEXT CAPTURE action is a rule over it. The QC verdict (`qc/stats.py`) is the
proof layer it is built on. Renderers consume the contract; `qc/hero.py` is the **V1 exploratory / diagnostic renderer**,
not the canonical representation.

## 1. What is computed now (and what is not)

| Class | Quantities |
|---|---|
| **Measured** (from the current data) | per-micrograph KPI means; tile-sampling SD σ_w (pooled from replicate tiles); approved between-micrograph SD σ_b and its estimation term s²/n; simulation-calibrated 95/99% thresholds; worst tested acquisition shift per KPI; tested acquisition range; variance-vs-window-area slope β; tile-scale excess E with χ² CI; 25-µm transect variograms; additive size histogram; decision leverage (verdict with each micrograph removed); prevalence CI |
| **Inferred with caveat** | spatial class (short-range / FOV-scale / long-range: variogram tails rest on 4 stitched sections); open spatial extent (100-µm window band is a visual aid); "fines at dim end" (n = 5 approved micrographs) |
| **Blindspot exposed, not resolvable** | composition of the high-Z phase; sub-0.36 µm particle population; extent beyond captured sections; untested acquisition factors (kV, working distance, dwell); through-thickness context (40–58 µm crops) |
| **Future actions** | EDS, higher magnification / low kV, extended or spaced mosaics, independent sections, larger approved reference |

Not used: pseudotime or latent axes (tested, acquisition-driven); embedding novelty (acquisition-sensitive); InLens quantities.
The model is **not Bayesian**. It is a frequentist two-level random-effects model with parametric-bootstrap calibration.

## 2. The cell model (micrograph j × KPI k)

```
x_jk ~ μ_k + b_j + e_j/√m_j      b ~ N(0, σ_b²)  approved material spread
                                  e ~ N(0, σ_w²)  tile-sampling noise (one 175×50 µm field)
V_jk = σ_b² + σ_w²/m_j + s_k²/n_k     →  components: material | spatial sampling | baseline support
z_jk = (x_jk − μ_k)/√V_jk ;  q95, q99 = simulated |z| quantiles for m_j tiles (true coverage)
acq_share_jk = (worst tested acquisition shift of k) / |x_jk − μ_k|
```

## 3. V1 exploratory renderer mappings (presentation, not model)

These mappings live in `qc/hero.py`; the contract carries only the quantities and states on the right.

| Channel | Rule |
|---|---|
| brightness | \|z\|/q95 (≥1 = outside the 95% envelope) |
| ▲/▼ | sign(x − μ) |
| solid + glow (*survives*) | deviating ∧ robust KPI ∧ tile-consistent (≥⅔ tiles beyond 95%) ∧ acq_share < 0.5 |
| hatched / dashed | deviating ∧ ¬survives (reason listed in the cell's rules) |
| flicker | acquisition outside the **tested** range ∨ (deviating ∧ acq_share ≥ 0.5) |
| ring hue / width | dominant reducible component (aqua spatial sampling, violet baseline support) / reducible share |
| ∅ | validity gate failed (additive contrast-to-noise < 4, or pixel size ≠ reference) |
| ◇ composition column | dimension not acquired; magenta = consequential (row has a surviving additive deviation) |
| ⤢ spatial rim | deviating ∧ KPI spatial class ≠ short-range ∧ (open edge ∨ tile-inconsistent) |
| ◎ scale rim | additive deviation ∧ ≥50% of excess objects < 0.7 µm ∧ excess ratio peaks at the 0.36 µm floor (≥1.5×) |
| ★ pivotal | verdict changes when the micrograph is removed |
| ∥ ref-linked | micrograph is a physical continuation of an approved section (excluded from the batch test) |
| "beyond ref" | value outside every approved tile |
| pulse | targeted by the selected NEXT CAPTURE action |

Strip: stitched section, 25-µm column profile (100-µm windows, no edge padding) and the approved 100-µm window band.
The band fades outside the captured extent; "◀ open" means the first or last window is still outside the band.

## 4. Dataset geometry measured on this data

| KPI | β (2–32 µm) | tile-scale excess E (95% CI) | variogram | class | consequence |
|---|---|---|---|---|---|
| additive area fraction | −0.78 | 0.6 (0.3–1.4) | flat to 300 µm | short-range | any extra area helps; shape irrelevant |
| additive density | −0.90 | 1.9 (1.1–4.2) | still rising at 400 µm | long-range | adjacent tiles partly redundant; independent sections needed |
| porosity | −0.86 | 3.6 (2.0–7.8) | range ≈ 175 µm | FOV-scale | space fields ≥ 175 µm or capture coherent strips |

Approved reference: additive density, additive D50 and pore size have σ_b = 0 (baseline micrographs differ no more than
tiles do). The approved material is one population, and its envelope is set by sampling.

## 5. NEXT CAPTURE rules

Ranking: tier 1 targets pivotal evidence; tier 2 targets other flags; tier 3 is general support. Within a tier the order is
REPEAT → ZOOM → EDS → EXTEND → SECTIONS → SPACE → REIMAGE → BASELINE (falsify → resolve scale → identity → extent → prevalence).
Cost is ordinal. No information-gain score is invented; "computed effect" appears only where the model gives it.

| Verb | Trigger (computed) | Addresses | Status |
|---|---|---|---|
| REPEAT | pivotal ∧ acquisition differs from approved ∧ surviving deviation | acquisition attribution incl. untested factors | grounded |
| ZOOM | scale rim | resolution floor / sub-surface fines | grounded |
| EDS | consequential composition pad | identity of the high-Z deviation | future modality |
| EXTEND | spatial rim with an open edge | extent of the anomalous region | computed trigger |
| SECTIONS | pivotal evidence ∨ < 5 independent micrographs | lot-level prevalence (Clopper–Pearson CI vs added sections) | computed |
| SPACE | KPI with FOV/long-range class ∧ tile-inconsistent deviation | spatial sampling (spacing ≥ range) | computed |
| REIMAGE | validity gate failed | measurability | grounded |
| BASELINE | always | population support (MDC at n+5, simulated) | computed |

Batch 3 output: REPEAT M2060 → ZOOM M2060 → EDS M2060 → EXTEND M2060 left → SECTIONS (prevalence 1/6: CI width 64 → 44 → 35 → 30 pts
with +7/14/21 sections) → EXTEND M2088 right → SPACE porosity ≥ 175 µm → BASELINE (D50 MDC 0.29 → 0.24 µm,
density 5.6 → 4.5 per 1000 µm², porosity 2.3 → 1.9 pts).
Batch 2 output: SECTIONS (its ACCEPT rests on the minimum of 3 independent micrographs) → BASELINE.

## 6. Independence correction (found in this pass)

Micrographs whose parent section is in the approved reference are **reference-linked**. Batch 2 has 3/6 (M2080, M2148,
M2156) and Batch 3 has 1/7 (M2080). They are shown but excluded from the batch test. The verdicts are unchanged (B2 ACCEPT on 3
independent micrographs; B3 REJECT p = 0.017 on 6), but B2's ACCEPT is now correctly flagged as fragile: every one of its
independent micrographs is pivotal.

## 7. Requests for qte77 (literature; not implementation)

1. Representative-area / correlation-length values reported for graphite(-Si) electrode porosity. Is a ≈175 µm lateral
   range plausible, or is it a cross-section-preparation artefact? (This would change the SPACE spacing.)
2. Can BSE brightness separate Si, SiOx and carbon-coated Si at typical kV? This decides whether the "dim fines" caveat could
   be resolved without EDS.
3. EDS spatial resolution for sub-µm particles in a graphite matrix at 5–10 kV. Is the EDS action feasible on the fines?
4. Typical supplier specs for the fine fraction of Si/SiOx additives. This would turn the density deviation into a spec
   exceedance rather than only an envelope exceedance.
