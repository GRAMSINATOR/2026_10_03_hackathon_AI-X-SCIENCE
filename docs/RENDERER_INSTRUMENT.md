# Evidence Instrument renderer (primary)

```
qc.field  ──►  reports/<batch>/field.json (epistemic-field/1)  ──►  qc/instrument.py (inject contract + assets)
                                                                     ──►  renderer/dist/index.html (React + React Three Fiber)
```

## Code layout

* `renderer/src/model/` is pure JS (no three.js) and is unit-tested. It holds every mapping from contract to view state:
  * `adapter.js`: keys, the five-stage projection, action reach, interpretation;
  * `explain.js`: explanation panel and legend;
  * `stack.js`: µm registration and prospective capture;
  * `palette.js`: materials, hue families, stage palettes, the chroma ladder, OKLab mixing;
  * `wave.js`: population wave.
* `renderer/src/scene/` holds the only WebGL: the key matrix (`Instrument.jsx`) and its geometry, textures and environment
  (`resources.js`).
* `renderer/src/ui/` is plain DOM/SVG:
  * `Panel.jsx`: the detail panel;
  * `SpatialEvidence.jsx`: the flat registered strip.

## Rules

* The renderer makes no scientific decision. Status, survival, rims, leverage and actions are read from the contract.
* Colour, chroma, material, depth and lighting exist only in the visual layer. The contract never says "green" or "glowing".

## Build, tests and QA

* Build: `cd renderer && npm install && npm run build` produces one self-contained HTML file.
* Dev: `npm run dev` (`?fixture=epistemic_field.Batch_2.json`).
* Tests: `npm test`.
* Visual QA at 1920×1080: `python work/qa_flat.py [scenario …]`. It includes a check that a key press does not animate.
* Frame budget: `python work/qa_frames.py`.
* Demo surface: the Streamlit app runs in presentation mode by default. `QC_DEV=1` (or `?dev=1`) adds the
  `instrument | legacy` renderer switch and the legacy colour key. The legacy V1 renderer (`qc/hero.py`) is kept for
  parity checks.
* `refs/` holds local visual references for development. It is git-ignored and never bundled.

## Layout

```
[ identity                                                                                  ]
[ DECISION                          | DATA SUPPORT                ]   decision brief hero (docs/DECISION_BRIEF.md)
[ SURVIVING EVIDENCE                | LIMITS                      ]   every block and chip traces to its proof
[ ACQUISITION POLICY (segmented step tray)                        ]
[ scope of the decision                                                                     ]
[ EXAMINER CONTROL MATRIX · lens selector (SIGNAL … NEXT CAPTURE)                           ]
[ Evidence Instrument (key matrix)                       | detail panel + proof trail       ]   panel height = instrument height
[ one-sentence lens interpretation                                                          ]
[ flat registered spatial evidence (recessed imaging bay, native scale, horizontal scroll)  ]
[ raw statistical proof (collapsed): engine decision record, reference, all rims, brief governance ]
```

* The decision is presented once, in the hero's DECISION block. The old header verdict chip is gone, and so is the
  panel's decision overview.
* The key matrix is now the **Examiner Control Matrix**, the proof and challenge surface. The five stages are its lenses.
* Clicking a hero claim turns the claim's `focus` reference into a lens, a pressed key and an open action, then
  scrolls there. The panel opens with the proof trail (brief › section › claim › proof): the claim exactly as stated,
  then each proof reference with its raw field value.
* The app's metrics and proof tabs sit in one collapsed expander.

## Instrument: physical object, straight-on

* **Camera.** Orthographic, tilted 0.2 rad only so that key walls read. There is no perspective, orbit or receding
  slab, and every key has identical apparent size.
* **Key.** One shared, analytically built geometry (`keyGeometry`):
  * rounded-rect footprint 1.28 × 0.52, corner r 0.14;
  * exactly flat top: a separate cap with pure up-normals;
  * a 0.05 rolled top-edge bevel and vertical walls;
  * 0.70 body height, of which 0.32 stands above the plate.
  * Gaps are 0.15 everywhere. Rows, columns and labels come from one layout function.
* **Plate.** White molded polymer, extruded with one socket per cell: a 0.04 seam with a softened rim and a recessed
  floor. A missing dimension keeps its socket. It holds no key, shows an occluded cavity, and the panel states "NOT
  ACQUIRED".
* **Material.**
  * Keys are lacquered resin: clear-coat 0.75, roughness 0.34. A matte finish marks an acquisition concern; glass marks
    "not measurable".
  * A reference-linked micrograph is drawn ghosted (towards grey), because it carries no independent weight.
* **Lighting.** One diffuse key light from the top-right:
  * a procedural PMREM studio with a large softbox at the upper right and a weak front-left fill;
  * a matching directional light plus a hemisphere light;
  * linear tone mapping, so data hues are never desaturated.
  * Key tops do not mirror the softbox; bevels do. Lower-left-facing walls sit in soft shade.
  * Contact shadows are one shared blurred decal per key, offset to the lower-left. No shadow maps are used.
* **Selection = depth.**
  * The selected key seats to 0.04 above the plate (from 0.32), immediately, as a latched state.
  * There is no spring, easing or interpolation.
  * Its wall disappears, its contact shadow tightens and its environment response drops (occlusion).
  * Footprint, colour, text and size are unchanged; this is tested.
  * Keyboard: arrows move an independent focus ring, Enter/Space presses, Escape releases, and a live region announces
    the focused key.
* **Typography.** Value and second line keep the same size and position on every key. Salience changes only the ink
  contrast (full / medium / soft). Saturated keys switch to white ink.

## Colour: representational and stage-dependent

The grammar:
* material = instrument identity;
* depth = selection;
* hue = semantic distinction *within the current stage*;
* chroma = relevance;
* emission = extreme tail only.

Each stage uses only the hue families it needs (`STAGE_PALETTE`). The panel legend is labelled with the stage, because a
hue has no meaning across stages.

| Stage | Model | Hues | Chroma (relevance) |
|---|---|---|---|
| SIGNAL | quantitative, two families | coral above · sky below | exceedance \|z\|/q95: white < 0.6, pastel to 1, clear → rich to 1.5, salient at ≥ 2.5; reference-linked × 0.5 |
| SCRUTINY | qualitative | survivors keep their signal hue · deep blue acquisition (matte) · green spatial inconsistency · grey reference-linked | survivors keep signal chroma; failures ≤ clear |
| FIELD | qualitative | green spatial sampling · violet baseline support · taupe material spread | dominant share × proximity to the decision threshold, so an envelope only matters where it could flip status |
| OUTER RIM | qualitative | amber scale · green spatial · magenta composition · violet population · deep blue acquisition | consequential = rich; non-consequential = pastel; settled = white with soft ink |
| NEXT CAPTURE | relational | the hue of what the selected action addresses | targets rich, triggers clear, everything else recedes |

Rules that apply across stages:
* **The ladder.** The chroma ladder is background 0 → pastel 0.2 → clear 0.45 → rich 0.72 → salient 0.94. Colours are
  mixed in OKLab, so steps are perceptually even.
* **Emission.** At most one key per stage glows (tested): an "out" observation far beyond q99, a consequential rim on
  the pivotal micrograph, or the selected action's target.
* **Validation.** Hues are validated with the dataviz palette validator on the instrument surface. Every co-occurring
  set passes the normal-vision floor. The worst deutan pair (magenta / green, ΔE 6.1) is legal because every coloured
  key prints its category (secondary encoding).

## Detail panel

* The panel leads with the selected key's category, in the key's hue. It then shows the section the stage projects:
  * measurement (SIGNAL);
  * scrutiny and acquisition (SCRUTINY);
  * envelope composition bar (FIELD);
  * limits and composition (OUTER RIM);
  * the action's evidence, rationale and expected effect (NEXT CAPTURE).
* Further sections follow: measurement, scrutiny, envelope, limits, acquisition, decision leverage, composition, and the
  next captures involving this evidence.
* Only the stage's own sections carry a hue accent.
* Text always uses ink tokens; hue appears only on bars and chips.
* With nothing selected, the panel shows:
  * the decision;
  * for SIGNAL, SCRUTINY and FIELD, the observations nearest the envelope;
  * for OUTER RIM, every rim;
  * for NEXT CAPTURE, the compact action list and the selected action.

## Flat spatial evidence (no 3D)

* **Native scale.** The stitched BSE micrograph is shown at one image pixel per screen pixel (≈ 5 px/µm), with crisp
  registered overlays: detected pores in blue, detected high-Z objects in amber.
* **Scrolling.** The strip scrolls horizontally, with the y-axis pinned.
* **Shared axis.** Beneath the micrograph, on the same µm axis:
  * the 100-µm window profile against the approved local band (labelled a visual aid; decisions are micrograph-level);
  * the 25-µm columns;
  * observed and unobserved extent (hatched);
  * open edges (green fade, from OUTER RIM onward);
  * the prospective capture (dashed field, NEXT CAPTURE);
  * the composition row, which is never filled.
* **Per-field values.** Each field label carries the field's KPI value.
* **Auto-scroll.** The view brings the relevant region into view: the prospective capture, then the open edge, then the
  strongest window.
* **Linkage.** Selecting a key switches the micrograph, the KPI and the matching overlay. The page opens with the
  selected key's overlay on.

## Performance

* `frameloop="demand"`. Measured on Batch 3 (SwiftShader, 1920×1080): 0 frames over 3 s idle. A stage change renders
  only during its 240 ms colour transition, then stops. A key press renders one frame.
* One key geometry and one plate geometry are used. Shadow, cavity and text textures are shared and memoised. There are
  no shadow maps and no post-processing, and DPR is ≤ 2.
* Bundle: 1.4 MB single file (≈ 495 kB gzip). The page with Batch 3 assets is ≈ 2.8 MB.

## Population wave

`t_i = (0.8·col + 0.6·row)`, normalised to 520 ms, plus seeded jitter of ±70 ms, with 300 ms per key.

Each key's material resolves in sequence: unresolved grey → ivory → stage colour → printed value. Keys do not move.

After about 900 ms the instrument is completely still. The wave is deterministic (FNV-1a + mulberry32), and
`prefers-reduced-motion` resolves it immediately.
