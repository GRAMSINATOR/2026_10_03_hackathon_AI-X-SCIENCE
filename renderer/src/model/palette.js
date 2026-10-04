// Material and colour grammar (presentation only; no scientific decisions).
//
//   material = instrument identity (white polymer body, lacquered keys)      depth   = selection (pressed key)
//   hue      = semantic distinction WITHIN the current stage's representation chroma  = perceptual relevance
//   pastel / near-white = weak, background, irrelevant                       emission = exceptional salience only
//
// Each stage projects a different kind of information and uses only the hue families it needs (STAGE_PALETTE). One
// category table drives the keys, the explanation panel and the legend, so the colour on a key is always the colour of
// the category named beside it. Hues validated with the dataviz palette validator on the light instrument surface
// (#ecebe7): every co-occurring set passes the normal-vision floor; the worst deutan pair (magenta / green, dE 6.1) is
// legal because every coloured key also prints its category in text (secondary encoding).

export const MATERIAL = {
  ivory: '#f4f3ef',      // key polymer (neutral = in family / settled)
  body: '#e9e8e4',       // instrument face plate (white molded polymer)
  cavity: '#b3b1ab',     // socket floor seen through the seam / an empty socket
  engrave: '#6f6c66',    // printed labels on the plate
  ink: '#1f1e1b',        // value print, full contrast
  inkSoft: '#8f8c85',    // value print on receded keys
  inkOnColour: '#ffffff',
  glass: '#dde4ea',      // not measurable (frosted)
  ghost: '#d6d5d0',      // reference-linked (no independent weight)
};

// hue families (each stage uses a subset; see STAGE_PALETTE)
export const HUE = {
  above: '#e8552a',        // SIGNAL: measured above the approved population (coral)
  below: '#3a93e8',        // SIGNAL: measured below (sky)
  spatial: '#1baf7a',      // spatial sampling / consistency / extent
  scale: '#eda100',        // resolution floor
  population: '#8455e0',   // baseline / population support, decision leverage
  composition: '#e0409b',  // composition / identity unresolved
  acquisition: '#1b4fa8',  // acquisition regime / method sensitivity / validity
  provenance: '#9aa0a8',   // reference-linked: not independent evidence
  material: '#a8977f',     // approved material spread (irreducible part of an envelope)
  capture: '#1f1e1b',      // prospective capture (flat spatial view)
};

// which families each stage projects (documentation + legend order); quantitative stages stay two-family
export const STAGE_PALETTE = [
  ['above', 'below'],                                             // SIGNAL: quantitative, diverging
  ['above', 'below', 'acquisition', 'spatial', 'provenance'],     // SCRUTINY: holds / why it fails / independence
  ['spatial', 'population', 'material'],                          // FIELD: which envelope component dominates
  ['scale', 'spatial', 'composition', 'population', 'acquisition'], // OUTER RIM: kind of unresolved limit
  ['spatial', 'scale', 'composition', 'population', 'acquisition'], // NEXT CAPTURE: what the selected action addresses
];

// chroma ladder: background -> pastel -> clear hue -> rich -> salient. Only a small subset should reach RICH/SALIENT.
export const CHROMA = { background: 0, pastel: 0.2, clear: 0.45, rich: 0.72, salient: 0.94 };

export const CATEGORY = {
  in_family: { label: 'In family', hue: MATERIAL.ivory },
  above: { label: 'Above the reference-frame envelope', hue: HUE.above },
  below: { label: 'Below the reference-frame envelope', hue: HUE.below },
  survives: { label: 'Survives scrutiny', hue: null },                       // keeps the deviation hue
  acquisition: { label: 'Acquisition / method sensitivity', hue: HUE.acquisition },
  spatial_inconsistent: { label: 'Spatially inconsistent across fields', hue: HUE.spatial },
  provenance: { label: 'Reference-linked (not independent)', hue: HUE.provenance },
  spatial_sampling: { label: 'Envelope dominated by spatial sampling', hue: HUE.spatial },
  baseline_support: { label: 'Envelope dominated by baseline support', hue: HUE.population },
  material_spread: { label: 'Envelope dominated by reference-population spread', hue: HUE.material },
  rim_spatial: { label: 'Spatial limit', hue: HUE.spatial },
  rim_scale: { label: 'Resolution (scale) limit', hue: HUE.scale },
  rim_composition: { label: 'Composition unresolved', hue: HUE.composition },
  rim_population: { label: 'Population support limit', hue: HUE.population },
  rim_acquisition: { label: 'Acquired outside the tested range', hue: HUE.acquisition },
  not_measurable: { label: 'Not measurable (validity gate)', hue: MATERIAL.glass },
  not_acquired: { label: 'Not acquired', hue: MATERIAL.cavity },
  settled: { label: 'Settled', hue: MATERIAL.ivory },
  action_target: { label: 'Addressed by the selected action', hue: null },
  action_cause: { label: 'Triggered the selected action', hue: null },
};

// action.addresses -> category hue (NEXT CAPTURE)
export const ADDRESS_HUE = {
  acquisition: HUE.acquisition, scale: HUE.scale, composition: HUE.composition, spatial_extent: HUE.spatial,
  spatial_sampling: HUE.spatial, population: HUE.population, validity: HUE.acquisition,
};
export const RIM_HUE = { spatial: HUE.spatial, scale: HUE.scale, composition: HUE.composition, population: HUE.population, acquisition: HUE.acquisition };
// several rims on one observation: show the most specific limit (renderer choice; the panel lists all)
export const RIM_PRECEDENCE = ['scale', 'spatial', 'composition', 'population', 'acquisition'];
// several scrutiny failures: name the most fundamental reason (the panel lists all)
export const FAIL_PRECEDENCE = [['acquisition_could_explain', 'acquisition'], ['spatially_inconsistent', 'spatial_inconsistent'],
                                ['moderate_robustness_dimension', 'acquisition']];

const ramp = (x, x0, x1, y0, y1) => y0 + (y1 - y0) * Math.max(0, Math.min(1, (x - x0) / (x1 - x0)));
// exceedance ratio |z|/q95 -> chroma: white well inside, pastel approaching the envelope, clear hue at it, rich beyond,
// salient only far beyond (>= 2.5 x q95)
export function chromaFromExceedance(x) {
  if (x == null || !isFinite(x)) return 0;
  if (x < 0.6) return 0;
  if (x < 1) return ramp(x, 0.6, 1, 0.04, CHROMA.pastel);
  if (x < 1.5) return ramp(x, 1, 1.5, CHROMA.clear, CHROMA.rich);
  return ramp(x, 1.5, 2.5, CHROMA.rich, CHROMA.salient);
}

export function hexToRgb(h) {
  const n = parseInt(h.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255].map(v => v / 255);
}
export function rgbToHex([r, g, b]) {
  const c = v => Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16).padStart(2, '0');
  return '#' + c(r) + c(g) + c(b);
}
// perceptual (OKLab) interpolation: equal steps of t read as equal steps of colour, so chroma 0.8 looks saturated, not a tint
const lin = v => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4), gam = v => (v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055);
function toOklab(hex) {
  const [r, g, b] = hexToRgb(hex).map(lin);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b), m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b),
        s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s, 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s, 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s];
}
function fromOklab([L, A, B]) {
  const l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3, m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3, s = (L - 0.0894841775 * A - 1.291485548 * B) ** 3;
  return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s]
    .map(v => Math.min(1, Math.max(0, gam(v))));
}
export function mix(a, b, t) {
  const A = toOklab(a), B = toOklab(b);
  return rgbToHex(fromOklab(A.map((v, i) => v + (B[i] - v) * t)));
}
