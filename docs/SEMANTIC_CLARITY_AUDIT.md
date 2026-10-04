# Semantic clarity audit

Audit date: 2026-10-04

Scope: the complete reader journey through the product UI: identity and verdict, four-part decision brief, Examiner
Control Matrix, detail panel and proof trail, imaging / inspection bay, service hatch, Marker Frontier, evidence rails,
and evidence drawer. This is a language audit only. It does not propose changes to the scientific derivation,
thresholds, states, gates, proof references, or navigation behavior.

## Executive finding

The product is scientifically careful, but it often exposes the names of its internal abstractions before explaining
their practical meaning. A domain expert can reconstruct the intended meaning, but a first-time technical reader has
to translate terms such as `scrutiny`, `field`, `outer rim`, `decision-consequential`, `marker admission`, and
`literature convergence` while also interpreting the evidence.

The clearest parts use a direct pattern:

> object + observed state + consequence + next action

Examples already working well include “Chemistry … is not measured; BSE alone cannot identify it” and “Repeat M2060
under the approved acquisition settings.” The least clear parts name a system concept without first saying what the
user should understand or do.

The recommended approach is a two-layer vocabulary:

1. Put plain operational wording in headings, controls, and first lines.
2. Keep the governed scientific term beside it as secondary text, a tooltip, or technical detail.

This preserves precision without making internal vocabulary the entry cost for understanding the interface.

## Priority 1: navigation and orientation

### Examiner lenses

The five lens names are concise but require prior knowledge of the model. `FIELD` and `OUTER RIM` are particularly
opaque without the documentation.

| Current | Recommended display | Technical term retained as |
|---|---|---|
| SIGNAL | MEASUREMENTS | `Signal` in the subtitle or tooltip |
| SCRUTINY | RELIABILITY CHECKS | `Scrutiny` in the subtitle or tooltip |
| FIELD | UNCERTAINTY SOURCES | `Epistemic field` in the subtitle or tooltip |
| OUTER RIM | KNOWN LIMITS | `Outer rim` in the subtitle or tooltip |
| NEXT CAPTURE | NEXT MEASUREMENT | `Next capture` in the subtitle or tooltip |

Recommended deck description:

- Current: “proof and challenge surface · read the evidence through five lenses”
- Clearer: “Inspect the measurements, reliability checks, uncertainty sources, known limits, and next measurement.”

`Proof and challenge surface` is meaningful to the builders, but it does not tell a user what the control does.

### Verdict readout

`QC VERDICT`, `REJECT`, and `ACCEPT` are clear. The statistical line needs one small clarification.

- Current: “batch p = 0.017 against α = 0.05”
- Clearer: “combined batch p = 0.017 · rejection threshold α = 0.05”

Do not replace the p-value with a confidence score or probability of failure. The tooltip should state that the
p-value is the calibrated batch test result, not the probability that the batch is bad.

### Page identity

- Current: “EVIDENCE INSTRUMENT”
- Recommended: keep it. It is short and accurately describes the product.
- Current: “vs approved Batch_1”
- Clearer: “compared with approved baseline Batch_1”

`Baseline` makes the role of the approved reference immediately visible.

## Priority 1: four-part decision brief

The four-region structure is sound. Most improvements are local wording changes.

### Data Support

`DATA SUPPORT` can sound like data quality or IT support. The region actually answers whether the available evidence
is enough for several distinct questions.

- Preferred heading: `WHAT THE DATA CAN SUPPORT`
- Short alternative: `EVIDENCE COVERAGE`

Recommended row wording:

| Current label and state | Clearer visible wording |
|---|---|
| ATTRIBUTION · CHANGE MODALITY | CAUSE / IDENTITY · DIFFERENT MEASUREMENT NEEDED |
| LOT PREVALENCE · EXPANSION NEEDED | LOT PREVALENCE · MORE INDEPENDENT SECTIONS NEEDED |
| TESTED REGIME · CHANGE MODALITY | TESTED RANGE · DIFFERENT MEASUREMENT NEEDED |
| ATTRIBUTION · NOT APPLICABLE | CAUSE / IDENTITY · NO DEVIATION TO EXPLAIN |
| TESTED REGIME · NO EXPANSION JUSTIFIED AT TESTED SCALES | TESTED RANGE · CURRENT RESULT DOES NOT JUSTIFY MORE OF THIS CAPTURE |

The last state must not be shortened to “No more data needed.” That would overstate the finding. The existing scope—
“for this decision” and “at tested scales”—must remain visible or immediately adjacent.

Recommended Batch 3 support sentence:

- Current: “6 independent incoming micrographs; outside the 99% envelope and consistent across fields: M2060.”
- Clearer: “Six independent incoming micrographs support the QC test. M2060 is outside the approved 99% range and the
  shift is consistent across its fields.”

This makes the conclusion explicit before the evidence.

### Surviving Evidence

`SURVIVING EVIDENCE` describes the algorithmic process, not the reader outcome.

- Preferred heading: `EVIDENCE THAT PASSED CHECKS`
- Compact alternative: `RELIABLE EVIDENCE`
- Keep “survives scrutiny” as the governed technical phrase in secondary detail.

Recommended explanatory sentence:

- Current: “Additive particle number density in M2060 is above the approved envelope and survives scrutiny.”
- Clearer: “M2060 has more additive particles than the approved range. The result remains after consistency and
  acquisition checks.”

Recommended context line:

- Current: “Did not survive: M2068 Additive D50 (inconsistent across fields), M2088 Porosity (acquisition could
  explain it), M2088 Pore size (inconsistent across fields).”
- Clearer: “Other apparent differences were excluded from the decision: M2068 additive size and M2088 pore size vary
  across fields; the M2088 porosity shift could be explained by acquisition.”

`Excluded from the decision` tells the user what “did not survive” means operationally.

### Limits

`LIMITS` is clear. The state line `SCALE · COMPOSITION · EXTENT · PREVALENCE` is technically accurate but reads as a
taxonomy rather than a conclusion. Keep the taxonomy, then add a single plain sentence:

> The current images cannot resolve the smallest particles or their chemistry, do not bound the spatial extent, and
> are too few to estimate lot prevalence precisely.

Recommended individual labels:

| Current | Clearer |
|---|---|
| SCALE | SMALLEST PARTICLES |
| COMPOSITION | CHEMISTRY |
| EXTENT | SPATIAL EXTENT |
| PREVALENCE | LOT PREVALENCE |

The technical rim type can remain in proof detail.

### Acquisition Policy

`ACQUISITION POLICY` is precise but bureaucratic. The content is an ordered measurement plan.

- Preferred heading: `NEXT MEASUREMENTS`
- Secondary label: `Acquisition policy`

Recommended program wording:

| Current | Clearer |
|---|---|
| VERIFY FIRST | VERIFY THE KEY RESULT FIRST |
| REPEAT · M2060 | REPEAT M2060 · approved settings |
| ZOOM · resolve scale | HIGHER MAGNIFICATION · resolve the smallest particles |
| EDS · chemistry (future) | EDS · identify composition |
| EXTEND · extent | EXTEND MOSAIC · bound the affected region |
| SECTIONS · independent sections | NEW SECTIONS · estimate lot prevalence |
| then, lower tiers | LATER OPTIONS |

`Future` should describe availability, not scientific importance. If EDS is unavailable, show “capability required”
as an operational status while preserving its rank and rationale.

### Scope line

The current scope sentence combines audience guidance, sample counts, model structure, calibration, and a Bayesian
disclaimer. It is accurate but too dense for the main surface.

Recommended visible line:

> Applies to this dataset and approved baseline Batch_1 only.

Recommended expandable technical detail:

> Approved baseline: 5–6 micrographs. Model: two-level random effects for material, tile sampling, and baseline
> support. Simulation-calibrated; not Bayesian.

## Priority 1: Marker Frontier

The Frontier contains the largest concentration of internal vocabulary. Its logic is coherent, but the overview
often reads like documentation for the implementation rather than guidance for a laboratory decision.

### Title and purpose

- Current: “Which new markers the current blindspots pull in, and when converging evidence would justify a new
  measurement capability.”
- Clearer: “Tracks measurements that could close known evidence gaps, and shows when the evidence justifies adding a
  new laboratory capability.”

`Blindspot`, `pull in`, and `converging evidence` all require interpretation in the current sentence.

### Lane names

| Current | Recommended |
|---|---|
| CURRENT CAPTURE MARKERS | MEASUREMENTS POSSIBLE NOW |
| marker admission · observable with today's capture | Candidate markers that can be tested with current images |
| NEW CAPABILITY CASES | CAPABILITIES THE LAB MAY NEED |
| capability expansion · needs a measurement the lab lacks | New instruments or modalities required to answer an open question |

Keep `Marker Admission` and `Capability Expansion` as technical process labels in the drawer or tooltip.

### Case language

| Current | Clearer |
|---|---|
| OPEN CONSEQUENTIAL BLINDSPOT | OPEN GAP THAT COULD AFFECT THE DECISION |
| RESEARCH CASE OPEN | EVIDENCE COLLECTION UNDERWAY |
| CLOSES | ADDRESSES |
| DECISION VALUE | EFFECT ON THE CURRENT DECISION |
| decision-consequential in Batch_3 | could change the Batch_3 decision |
| controller already acts: ZOOM | current plan already includes: higher magnification |
| Why current capture cannot substitute. | Why current images are insufficient. |
| OPEN CAPABILITY CASE | VIEW EVIDENCE |
| OPEN EVIDENCE | VIEW EVIDENCE |
| TESTED AND SET ASIDE | TESTED AND RULED OUT FOR NOW |

`Consequential` should not be replaced everywhere. In formal proof detail it identifies an exact engine flag. In the
overview, “could affect/change the decision” gives the reader the consequence first.

### State names

The state machine should remain unchanged. Display text can explain each state instead of relying on the enum alone.

| State | Plain explanation beside it |
|---|---|
| CANDIDATE | linked to a known gap; evidence not yet attached |
| BUILDING | evidence is being assembled |
| SUPPORTED | scientific relevance is supported |
| TRACKABLE | relevant and measurable with current capture |
| ADMITTED | approved for routine tracking |
| UNAVAILABLE | current capture cannot measure it |
| CONFOUNDED | a tested confound explains the signal |
| REJECTED | failed a required gate or was rejected in review |
| WATCHING | capability need is being monitored |
| BUILDING CASE | capability case has a consequential need or converging demand |
| CRITICAL MASS | all evidence gates for recommendation are met |
| RECOMMENDED | evidence gates and recorded review support adoption |
| INTEGRATED | capability has been adopted into the workflow |

`CRITICAL MASS` is particularly risky without its explanation because it may be read as a paper count. The UI should
state that it means the required categorical gates are met, not that a numeric score crossed a threshold.

### Evidence gates

Gate names should be phrased as questions in the overview. The governed names can stay in technical detail.

| Technical gate | Overview question |
|---|---|
| SCIENTIFIC RELEVANCE | Is it scientifically relevant? |
| MEASURABILITY | Can current capture measure it? |
| ROBUSTNESS | Does it hold after confound checks? |
| BLINDSPOT CLOSURE | Does it close a decision gap? |
| ADMISSION | Is it ready for adoption? |
| MARKER DEMAND | Do enough credible markers require it? |
| LITERATURE CONVERGENCE | Does independent literature support it? |
| CONSEQUENTIAL CLOSURE | Would it resolve a decision-relevant gap? |
| NON-SUBSTITUTABILITY | Can existing methods answer the question? |
| INTEGRATION CASE | Is there an acceptable implementation plan? |

Recommended rail legend:

- Current: `met · partly supported · contested · failed / blocked · open`
- Clearer: `met · partial evidence · conflicting evidence · failed / unavailable · no evidence yet`

The existing sentence “A rail shows which gates have evidence, not a probability” is excellent and should remain.

### Research state

The overview currently exposes producer and fixture language:

- `awaiting research agent (qte77)` → `literature review not yet attached`
- `no literature yet` → `no literature evidence attached`
- `FIXTURE bundle present (does not advance any gate)` → show only in developer mode

The source agent belongs in provenance. It does not help a laboratory user interpret the case.

### Counts

- `0 strong direct` → `0 strong direct sources`
- `current data: needs acquisition` → `data test: additional capture needed`
- `1 marker demand` → `1 credible marker requires this capability` when the demand is credible; otherwise state the
  counted and credible totals separately.
- `burden: medium` → `implementation burden: medium`

## Priority 2: detail panel and proof trail

The panel is rigorous but mixes results, model vocabulary, and debugging identifiers at one level.

### Recommended information order

1. What was observed.
2. Why it matters for the decision.
3. Why the result is considered reliable or excluded.
4. What remains unknown.
5. What measurement comes next.
6. Technical proof and source identifiers.

### Terminology replacements

| Current | Clearer |
|---|---|
| approved envelope | approved range (technical: population envelope) |
| fields beyond 95% | fields outside the approved 95% range |
| acquisition share | amount potentially explained by acquisition |
| KPI robustness | metric stability across robustness tests |
| envelope composition | sources of expected variation |
| baseline support | uncertainty from estimating the approved baseline |
| spatial sampling | uncertainty from where fields were sampled |
| minimum detectable change | smallest change this dataset can reliably distinguish |
| verdict without it | decision if this evidence is removed |
| pivotal | changes the decision when removed |
| reference-linked | reused from the approved baseline; excluded from independent evidence |

`Reference-linked` is an important rule, but it needs its consequence every time it first appears.

### Raw identifiers

Strings such as `marker:high_z_composition`, `Batch_3/missing_dimensions/M2060:composition`, and raw proof paths are
valuable for auditability but should sit behind `Technical references`. They interrupt comprehension when placed in
the main evidence narrative.

## Priority 2: imaging / inspection bay

The bay is visually clear but its introduction assumes the reader knows what “registered” means.

- Current: “registered micrograph, segmentation and profile on one µm axis”
- Clearer: “Aligned image, detected features, and measurement profile on the same distance scale.”

Recommended control and legend wording:

| Current | Clearer |
|---|---|
| Additive density | Additive particles per 1,000 µm² |
| Additive area | Additive area fraction |
| detected high-Z objects | detected high-contrast particles |
| not captured | area outside the captured image |
| approved local band (visual aid) | approved local range (visual guide only) |
| open edge | deviation continues to image edge |
| native scale, scroll | native image scale · scroll horizontally |
| composition: not acquired | chemistry not measured |
| prospective capture | proposed next capture |

`High-Z` and `BSE` should be expanded once per view: “high atomic-number (high-Z)” and “backscattered-electron
(BSE) image.” After that, the abbreviations are appropriate.

## Priority 2: service hatch

The service hatch is intentionally technical, so its density is acceptable. Its headings can still lead with purpose.

| Current | Clearer |
|---|---|
| Raw statistical proof | Statistical details and audit trail |
| Engine decision record | Why the engine reached this decision |
| Reference (approved micrographs) | Approved baseline statistics |
| All rims (incl. non-consequential) | All known limits, including those that do not affect this decision |
| Brief governance (what the hero leaves out, and why) | What the summary omits and why |

Keep exact p-values, combination method, calibration values, and raw IDs here.

## Priority 2: paper evidence drawer

The paper record is one of the clearest technical areas after the visual pass. Its four dimensions—directness, method,
transferability, and direction—work well. Improvements are mostly labels and sentence order.

- `PAPERS` → `LITERATURE EVIDENCE`
- `PROJECT RECORDS AND ENGINE FACTS` → `INTERNAL EVIDENCE`
- `EVIDENCE STATE` → `GATE STATUS`
- `to advance` → `still needed`
- `basis` → `supported by`
- `fixture, not counted` → keep in development fixtures only

For each paper, keep the current order: title, source metadata, assessment dimensions, claim, explanation. Do not
collapse contradictory evidence or reduce it to a color.

## Ambiguous words that need a glossary or first-use explanation

| Term | First-use explanation |
|---|---|
| approved envelope | the range expected from approved baseline material |
| field | one imaged area within a micrograph |
| independent micrograph | a micrograph that is not reused from the approved baseline and is treated as one independent unit |
| scrutiny | checks for spatial consistency, acquisition effects, and metric robustness |
| consequential | capable of changing the current decision or its justified next action |
| outer rim | a known limit beyond what the current evidence can establish |
| marker | a defined, interpretable measurement candidate—not a biological marker by default |
| capability | an instrument, modality, or workflow the lab would need to make a measurement |
| blindspot | a known question the current measurement vocabulary cannot answer |
| gate | a categorical requirement; not a score or probability |
| baseline support | uncertainty caused by estimating the approved reference from a finite sample |

## Wording that should remain protected

These distinctions carry scientific meaning and should not be casually simplified:

- `independent micrograph` versus field or tile;
- `approved reference` / `approved baseline` versus a universal normal range;
- `outside the envelope` versus proven defect;
- `could explain` versus caused;
- `survives scrutiny` versus validated or confirmed;
- `consequential` versus severe;
- `not acquired` versus absent;
- `extent not bounded` versus present everywhere;
- `prevalence estimate` versus population prevalence known with certainty;
- `supportive`, `contradictory`, and `neutral` literature direction;
- `met`, `partial`, `contested`, `failed`, and `open` gate states;
- `fixture evidence does not count`;
- `critical mass` as a conjunction of categorical gates, never a paper count or confidence score.

Avoid the following substitutions:

| Avoid | Reason |
|---|---|
| “proved”, “confirmed”, “validated” | overstates the evidence |
| “defect” | the system detects departure from the approved envelope, not universal defect |
| “probability the batch is bad” | misstates the calibrated p-value |
| “no more data needed” | overstates a decision-scoped stop or no-expansion state |
| “chemical identity” from BSE | composition was not measured |
| “prevalence is 1 in 6” without the interval | hides the extreme sampling uncertainty |

## Recommended implementation order

### Pass A: high-value, low-risk display copy

Change navigation labels, region headings, lane headings, button labels, introductory sentences, and service-hatch
headings. Keep schema values and internal enums unchanged. This should produce the largest clarity gain with minimal
risk.

### Pass B: first-use explanations

Add one-line explanations or tooltips for p-value, approved envelope, independent micrograph, field, scrutiny,
consequential, marker, capability, and gate. Explanations should be available by keyboard and should not depend on
color or hover alone.

### Pass C: governed claim wording

Update deterministic templates in `qc/brief.py` only after exact expected text is revised in tests. Preserve every
value reference, proof reference, state, focus target, and forbidden-overstatement check.

### Pass D: progressive disclosure

Move raw IDs, proof paths, model internals, and producer names into technical detail while keeping them accessible for
audit. Do not remove them from the product.

## Acceptance checks for a wording pass

1. A first-time reader can state the verdict, decisive observation, main unknowns, and next action without knowing the
   terms epistemic field, outer rim, or marker admission.
2. Every plain-language statement still resolves to the same proof reference.
3. No sentence converts uncertainty into certainty or association into cause.
4. `not acquired`, `not observed`, `not measurable`, and `not present` remain distinct.
5. The Batch 2 “no deviation” state does not imply universal equivalence or that no further unknowns exist.
6. The Batch 3 prevalence statement retains its confidence interval.
7. Frontier gate states, case states, contradictory evidence, and fixture exclusion remain unchanged.
8. Technical users can still reach raw values, identifiers, model details, and provenance.

## Overall assessment

The product does not need a conceptual rewrite. Its information architecture is strong and its scientific caution is
a major asset. The semantic problem is that the interface often leads with the system's internal nouns. Leading with
the practical meaning, then retaining the exact technical term as secondary detail, would make the product much easier
to understand without weakening its scientific contracts.
