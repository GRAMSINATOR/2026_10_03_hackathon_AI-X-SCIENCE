# What we can and cannot claim

## Can claim (evidence in the research log)
- **Provenance.** The 31 fields are tiles of 13 parent micrographs; tiles of one micrograph abut (edge NCC 0.41–0.76; non-neighbours
  typically |NCC| < 0.15, max 0.28) and 5 micrographs span 2–3 batch folders. Field-level statistics would be pseudo-replicated, so
  the system works per micrograph and reports the effective sample size.
- **Scale and registration.** 25.0 nm/px (TIFF XResolution); BSE, SE and InLens are pixel-registered (≤0.2 px).
- **Batch 3 → REJECT (p = 0.017; severity test p = 0.009).** Micrograph M2060 (4 tiles) has 34.4 fine high-Z (BSE-bright) objects per 1000 µm²
  against 19.5 in the approved micrographs (+77%, t = 6.7, 3/4 tiles individually outside 95%), at unchanged additive area
  fraction. The largest tested synthetic acquisition change explains ≤12% of that shift.
- **Batch 2 → ACCEPT.** All 6 independent micrographs sit inside the approved envelope on every measurable KPI.
- **Baseline audit.** M2316 (approved) has additive-to-matrix contrast-to-noise 3.2, so its additive is not measurable
  and it is excluded from those KPIs. The system says so instead of reporting a number.
- **Detection limits.** With 5–6 approved micrographs, the minimum detectable change (95%, 3-tile micrograph) is
  ±0.29 µm for additive D50, ±5.6 per 1000 µm² for additive density, ±2.5 points of additive area and ±2.3 points of
  porosity (Method tab). An approved 7-micrograph batch has a 14% chance of one micrograph outside 99%, so a single
  modest excursion only triggers INVESTIGATE.
- **The REJECT rests on one micrograph** (M2060: 4 contiguous tiles, about 0.7 mm of cross-section). Without it, Batch 3
  would be ACCEPT (batch p = 0.52): the remaining excursions (M2068 additive D50 on a robust KPI, M2088 porosity on a
  moderate one) are consistent with chance for a 6-micrograph batch.
- **Negative results.** Pseudotime/latent progression is not supported. Multiscale scaling exponents don't discriminate
  micrographs. Learned-embedding novelty is acquisition-sensitive.

## Must not claim
- The chemistry of the bright phase. It is "high-Z, BSE-bright, consistent with a Si-based additive", with no EDS.
- That M2060's shift is a supplier formulation change. It is *not explained by the tested acquisition changes*, but its
  fine objects are on the dim side (possibly partly sub-surface, or a lower-Z fine phase), and its acquisition differs.
  EDS / re-imaging is the recommended confirmation.
- 3-D particle sizes, absolute porosity or tortuosity: these are 2-D sections of non-infiltrated pores, an operational
  BSE-dark definition.
- That cracks are process-induced (they may come from cross-section preparation), or any tool-wear / failure prediction.
  The risk text gives literature-grounded *exposure hypotheses* (e.g. coarser Si-type particles fracture more readily;
  hard coarse particles raise abrasive exposure of calender rolls).
- Any trajectory, progression or "time" axis.
- Confidence beyond what 5–6 independent approved micrographs allow.
- That M2068/M2088 have a defectively coarse additive. M2068 is outside 95% on D50, but only 1/3 of its tiles agree, and its
  Batch 2 neighbour tile is normal. That is spatial heterogeneity along one cross-section, not a lot-level change.
