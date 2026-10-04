# Reference self-audit (role REFERENCE)

Batch_1 is the configured reference population. When it is opened, it is never presented as ACCEPT, INVESTIGATE or
REJECT. Its top-level state is the role **REFERENCE**, and it goes through the same machine as any batch: hero,
Examiner Control Matrix and its five lenses, imaging bay, Marker Frontier input and service hatch. Only the semantics
differ: **the reference is also data, and it can challenge its own sampling assumptions.**

```
python -m qc assess data/Batch_1     # writes reports/Batch_1/{result,field,brief}.json + instrument.html, like any batch
```

## Two operations, kept apart

| | Incoming batch (Batch_2, Batch_3) | Reference self-audit (Batch_1) |
|---|---|---|
| Comparison frame | The complete configured reference, unchanged | **Leave-one-parent-micrograph-out**: micrograph *i* is compared with a frame built from the *other* eligible parents, with tile-sampling SD pooled without *i*'s tiles (`qc.stats.loo_frames`) |
| Top-level state | QC verdict | Role REFERENCE, `p_batch = null`, no verdict |
| Unit | Parent micrograph | Parent micrograph (tiles are never promoted to independent observations) |
| "Leverage" | Verdict without each micrograph | **Reference influence**: shift of the reference mean when each parent is left out, in MDC units |
| Consequential rim | Weakens the QC decision | Weakens the reference as a comparison anchor (rules below) |

The incoming fields and their scientific results are byte-identical to before; a test compares them with the committed
fixtures.

## Reference-mode consequentiality (each rule explicit, with its basis in the rim)

| Rim | Consequential when |
|---|---|
| `validity:<parent>` | Always: the parent belongs to the reference, but those KPIs are not trustworthy there and are excluded from the reference statistics. |
| `population:<batch>` (reference support) | Estimating the reference is ≥ ⅓ of a 3-field envelope's variance on some robust KPI (`REF_SUPPORT_SHARE`). |
| `scale:<batch>` (floor truncation) | The reference size distribution is highest in its smallest resolved bin: it has not turned over at the detection floor. |
| `spatial-dimension:<kpi>` (tile sampling) | The adjacent-tile excess-variance 95% CI excludes 1, so adjacent tiles are not independent samples. |
| `acquisition:<parent>` | Only if that parent's measurements are otherwise valid; with a validity failure, the validity rim carries the consequence. |
| Observation spatial / scale / composition | Only on a surviving leave-one-out departure. |

Every consequential reference rim triggers a reference action (`_reference_actions`), in this order:
- REIMAGE an invalid parent;
- ZOOM, to resolve sub-floor fines;
- SPACE fields by the correlation range;
- EXTEND one coherent capture, beyond a variogram still rising;
- BASELINE, adding reference micrographs, with its MDC projection.

With no consequential rim, the brief says **NO SAME-REGIME EXPANSION JUSTIFIED**. Reference rims are ordinary rims of
`reports/Batch_1/field.json`, so they feed the Marker Frontier's blindspot index with no special case.

## Hero (decision-brief/1, reference mode; wording chosen by the computed state)

| Block | States |
|---|---|
| ROLE (status readout) | REFERENCE · "6 parent micrographs, each compared with the other 5" |
| DATASET SELF-AUDIT | SAMPLING ASSUMPTION CHALLENGED / REFERENCE SUPPORT LIMITED / REFERENCE STRUCTURE RESOLVED, plus one indicator each for reference support, validity, tile sampling and scale floor |
| SURVIVING SIGNAL | REFERENCE HETEROGENEITY (≥ 2 parents) / LOCAL DEPARTURE / NO STRONG INTERNAL DEPARTURE; non-surviving departures and the largest reference influence as context |
| OPEN LIMITS | Consequential reference-derived rims (reference support itself is stated once, in the self-audit block) |
| NEXT ACQUISITION | Tier-1 reference actions, or NO SAME-REGIME EXPANSION JUSTIFIED |

A local departure is described as a departure within the reference, never as a defect. `brief.check` rejects
"defect", any QC verdict and a departure not tested in its own leave-one-out frame.

## What Batch_1 shows today (computed, not chosen)

**No strong internal departure.**
- 0 of the 5 additive-valid reference micrographs leave their leave-one-out 95% envelope on a robust KPI. With 5
  micrographs, at least one such excursion is expected by chance with probability 0.48.
- One departure, M2148 solid chord (z = +2.9, a single-field micrograph), fails scrutiny: the KPI is
  acquisition-sensitive, and the worst tested acquisition change could explain 55% of it.
- No parent dominates the reference: the largest leave-one-out influence is 0.21 MDC (M2080, additive D50).

**Sampling assumption challenged.**
- Adjacent-tile variance is 1.9× the short-range prediction for additive density (95% CI 1.1–4.2), whose variogram is
  still rising at 400 µm.
- It is 3.6× for porosity (95% CI 2.0–7.8), with a range of about 175 µm.
- Adjacent reference tiles are therefore not independent samples.

**Open limits.**
- *Validity:* M2316 is in the reference, but its additive contrast-to-noise is 3.2, below 4, so its high-Z
  measurements are not trustworthy. The additive reference rests on 5 micrographs.
- *Scale floor:* the reference fines distribution peaks in its smallest resolved bin (4.95 vs at most 2.90 per
  1,000 µm²). Normal fines below 0.36 µm are unobserved, in the reference too, which is exactly where Batch_3's
  surviving excess sits.
- *Reference support:* estimating the reference is 34% of a 3-field envelope for additive density. This is close to the
  ⅓ rule.

**Next acquisition.** Re-image M2316 → resolve sub-floor fines → space porosity fields ≥ 175 µm apart → one longer
additive-density capture beyond 400 µm → +5 reference micrographs.

## Deliberately not built

- **Covariance between markers across parents.** It was not built because with 5–6 parents a correlation estimate is
  not defensible.
- **A high-dimensional anomaly model.**
- **Detector-persistence statistics beyond the existing SE porosity cross-check.**

Reference variance is exposed as what the data supports:
- centre;
- between-parent and tile-sampling spread;
- baseline share;
- spatial class, tile excess and range;
- per-parent influence;
- validity;
- the floor-truncated size distribution.
