// Evidence Stack model: the specimen (real micrographs) plus ONLY spatially registered analysis layers.
// Every layer shares the specimen's x/y frame (µm along the section, µm across the field height).
// Non-spatial epistemic state (population support, decision, acquisition regime) is deliberately absent here.
import { HUE, MATERIAL } from './palette.js';
import { MASK_OF_DIMENSION, SPATIAL_LAYER_DIMS } from './adapter.js';

export const RUN_GAP_UM = 60;   // display spacing between unconnected runs; true separation is unknown (contract)
const oid = (e, d) => `${e}:${d}`;

export function registration(M, entity) {
  const p = M.F.spatial_profiles.find(x => x.entity === entity);
  if (!p) return null;
  const H = Object.fromEntries(M.F.provenance.fields.map(f => [f.id, f.height_um]));
  let off = 0;
  const runs = p.runs.map(r => {
    const run = { offsetUm: off, lengthUm: r.length_um,
      fields: r.fields.map(f => ({ id: f.field, batch: f.batch, x0Um: off + f.x0_um, widthUm: f.width_um, heightUm: H[f.field] || 50 })) };
    off += r.length_um + RUN_GAP_UM;
    return run;
  });
  const height = Math.max(...runs.flatMap(r => r.fields.map(f => f.heightUm)));
  return { runs, totalUm: off - RUN_GAP_UM, heightUm: height, separationKnown: runs.length <= 1 };
}

// per-column colouring of a profile against the approved local band (direction hue, chroma by excess)
export function profileCells(profile, regRuns) {
  const b = profile.reference_band, half = Math.max(b.hi - b.mean, 1e-12);
  return profile.runs.map((r, i) => {
    const off = regRuns[i].offsetUm, cells = [];
    r.column_centres_um.forEach((x, j) => {
      // nearest 100-um window mean (windows lie fully inside the run); edge columns use the edge window
      let w = 0, best = Infinity;
      r.window_centres_um.forEach((c, k) => { const d = Math.abs(c - x); if (d < best) { best = d; w = k; } });
      const v = r.window_means.length ? r.window_means[w] : r.column_values[j];
      let hue = MATERIAL.ivory, chroma = 0.08, state = 'inside';
      if (v > b.hi) { hue = HUE.above; chroma = Math.min(0.95, 0.35 + 0.6 * (v - b.hi) / half); state = 'above'; }
      else if (v < b.lo) { hue = HUE.below; chroma = Math.min(0.95, 0.35 + 0.6 * (b.lo - v) / half); state = 'below'; }
      cells.push({ x0Um: off + x - profile.column_um / 2, widthUm: profile.column_um, value: r.column_values[j], window: v, hue, chroma, state });
    });
    return { cells, openStart: r.open_at_start, openEnd: r.open_at_end, offsetUm: off, lengthUm: r.length_um };
  });
}

// stage visibility of layer kinds
const VISIBLE_FROM = { specimen: 0, mask: 1, profile: 0, extent: 3, missing: 3, prospective: 4 };

export function stackLayers(M, entity, stage, { action = null, assets = {} } = {}) {
  const s = typeof stage === 'number' ? stage : 0;
  const reg = registration(M, entity); if (!reg) return { reg: null, layers: [] };
  const fields = reg.runs.flatMap(r => r.fields);
  const hasBse = fields.some(f => assets[f.id] && assets[f.id].bse), hasSeg = fields.some(f => assets[f.id] && assets[f.id].seg);
  const dev = d => { const o = M.OBS[oid(entity, d)]; return o && ['deviant', 'out'].includes(o.reference_relation.status); };
  const layers = [];
  layers.push({ id: 'specimen', kind: 'specimen', label: 'Specimen · BSE micrographs', status: 'measured', available: hasBse,
    description: `${fields.length} field${fields.length > 1 ? 's' : ''} of ${entity} (${Math.round(reg.totalUm)} µm captured${reg.separationKnown ? '' : '; separation between runs unknown'}).`, linkedKeys: [] });
  const maskLinks = m => Object.entries(MASK_OF_DIMENSION).filter(([, v]) => v === m).map(([d]) => oid(entity, d)).filter(id => M.OBS[id]);
  layers.push({ id: 'mask_highz', kind: 'mask', label: 'Detected high-Z objects', status: 'analysis', available: hasSeg, phase: 2,
    description: 'Segmentation of the BSE-bright phase (objects the additive KPIs are computed from).', linkedKeys: maskLinks('mask_highz') });
  layers.push({ id: 'mask_pores', kind: 'mask', label: 'Detected pores', status: 'analysis', available: hasSeg, phase: 0,
    description: 'Segmentation of BSE-dark pores (basis of porosity, pore size and chord lengths).', linkedKeys: maskLinks('mask_pores') });
  for (const d of SPATIAL_LAYER_DIMS) {
    const p = M.PROF[oid(entity, d)]; if (!p) continue;
    const c = M.columns.find(x => x.id === d);
    layers.push({ id: `profile:${d}`, kind: 'profile', dimension: d, label: `${c.short} · 100-µm windows`, status: 'approximate', available: true,
      description: `${c.label}: 25-µm columns (full field height) coloured by the surrounding 100-µm window mean vs the approved local band ` +
                   `(${fmtBand(p.reference_band, c)}). Visual aid; the decision uses the micrograph mean.`,
      cells: profileCells(p, reg.runs), linkedKeys: [oid(entity, d)], deviating: dev(d) });
  }
  const spatialRims = M.F.rims.filter(r => r.type === 'spatial' && r.scope === 'observation' && r.target.startsWith(entity + ':'));
  const openDims = spatialRims.filter(r => r.basis.open_edges && r.basis.open_edges.length).map(r => r.target.split(':')[1]);
  const extentProfile = openDims.length ? M.PROF[oid(entity, openDims[0])] : null;
  layers.push({ id: 'extent', kind: 'extent', label: 'Observed extent', status: 'measured', available: true,
    description: extentProfile ? `Capture ends while ${M.columns.find(x => x.id === openDims[0]).short.toLowerCase()} is still outside the approved band: ` +
      `open at ${spatialRims.find(r => r.target.endsWith(openDims[0])).basis.open_edges.join(' and ')}.` : 'Captured extent; no deviation reaches its edges.',
    runs: reg.runs.map((r, i) => ({ offsetUm: r.offsetUm, lengthUm: r.lengthUm,
      openStart: !!(extentProfile && extentProfile.runs[i].open_at_start), openEnd: !!(extentProfile && extentProfile.runs[i].open_at_end) })),
    linkedKeys: spatialRims.map(r => r.target), dimension: openDims[0] || null });
  const miss = M.MISS[oid(entity, 'composition')];
  layers.push({ id: 'missing:composition', kind: 'missing', label: 'Composition — not acquired', status: 'not acquired', available: false,
    description: miss && miss.consequential ? 'Not acquired. Consequential: the surviving deviation is in the high-Z phase whose chemistry is unknown.'
                                              : 'Not acquired (no EDS / spectroscopy). Nothing is drawn because nothing was measured.',
    consequential: !!(miss && miss.consequential), linkedKeys: [oid(entity, 'composition')] });
  const pro = prospective(M, entity, reg, action);
  if (pro) layers.push(pro);
  const A = s === 4 && action != null ? M.actions[action] : null;
  const actsHere = A && A.targets.entities.includes(entity);
  // NEXT CAPTURE: the layers the selected action works on stay salient (never invented geometry)
  const addressed = L => !!actsHere && (L.kind === 'prospective' ||
    (L.kind === 'missing' && A.targets.dimensions.includes('composition')) ||
    (L.kind === 'profile' && A.targets.observations.includes(oid(entity, L.dimension))) ||
    (A.verb === 'ZOOM' && L.id === 'mask_highz'));
  for (const L of layers) {
    L.visible = s >= (VISIBLE_FROM[L.kind] ?? 0) && (L.kind !== 'profile' || s >= 2 || L.deviating) && (L.kind !== 'prospective' || s === 4);
    L.quiet = (s === 3 && !(L.kind === 'extent' || L.kind === 'missing' || (L.kind === 'profile' && spatialRims.some(r => r.target.endsWith(L.dimension)))))
           || (s === 4 && L.kind !== 'specimen' && !addressed(L));
  }
  const note = !A ? null : !actsHere ? `${A.verb} does not act on ${entity}.`
    : pro ? null : `${A.verb} has no spatial footprint in the evidence: nothing is drawn on the specimen.`;
  return { reg, layers, note };
}

// geometry for a NEXT CAPTURE action, only where the action has a defensible spatial footprint
export function prospective(M, entity, reg, actionIndex) {
  if (actionIndex == null) return null;
  const A = M.actions[actionIndex];
  if (!A || !A.targets.entities.includes(entity)) return null;
  const fieldW = median(reg.runs.flatMap(r => r.fields.map(f => f.widthUm)));
  if (A.verb === 'EXTEND' && A.effect && A.effect.open_edges) {
    const regions = [];
    reg.runs.forEach(r => {
      if (A.effect.open_edges.includes('start')) regions.push({ x0Um: r.offsetUm - fieldW, widthUm: fieldW, side: 'start' });
      if (A.effect.open_edges.includes('end')) regions.push({ x0Um: r.offsetUm + r.lengthUm, widthUm: fieldW, side: 'end' });
    });
    return { id: 'prospective', kind: 'prospective', action: A.id, label: 'Prospective capture · next field', status: 'prospective', available: true,
      regions: regions.slice(0, 1), description: `${A.title}: one additional field (${Math.round(fieldW)} µm, the standard field width) beyond the open ` +
        `edge; the true extent of the anomaly is unknown, so repeat until the profile re-enters the band.`, linkedKeys: A.reach.keys };
  }
  if (A.verb === 'REPEAT') {
    return { id: 'prospective', kind: 'prospective', action: A.id, label: 'Prospective capture · same region', status: 'prospective', available: true,
      regions: reg.runs.map(r => ({ x0Um: r.offsetUm, widthUm: r.lengthUm, side: 'same' })),
      description: `${A.title}: re-image the same footprint under approved settings.`, linkedKeys: A.reach.keys };
  }
  return null;   // ZOOM, EDS, SECTIONS, SPACE, BASELINE: no footprint defined by the evidence
}

export function layerForKey(key) {
  if (key.kind === 'missing') return 'missing:composition';
  if (SPATIAL_LAYER_DIMS.includes(key.dimension)) return `profile:${key.dimension}`;
  return MASK_OF_DIMENSION[key.dimension] || null;
}

const median = a => { const s = [...a].sort((x, y) => x - y); return s.length ? s[Math.floor(s.length / 2)] : 175; };
const fmtBand = (b, c) => `${(b.lo * c.factor).toPrecision(3)}–${(b.hi * c.factor).toPrecision(3)} ${c.unit}`;
