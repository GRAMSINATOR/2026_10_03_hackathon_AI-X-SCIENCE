// Contract (epistemic-field/1) -> view model.  Indexing and presentation mapping only: every scientific
// decision (status, survival, rims, leverage, actions) is read from the contract, never recomputed here.
import { ADDRESS_HUE, CATEGORY, CHROMA, FAIL_PRECEDENCE, HUE, MATERIAL, RIM_HUE, RIM_PRECEDENCE, chromaFromExceedance } from './palette.js';

export const STAGES = ['SIGNAL', 'SCRUTINY', 'FIELD', 'OUTER RIM', 'NEXT CAPTURE'];
export const SPATIAL_LAYER_DIMS = ['additive_density', 'additive_area_frac', 'porosity'];
// which registered detection mask a dimension is derived from (segmentation provenance, not a statistical claim)
export const MASK_OF_DIMENSION = {
  additive_area_frac: 'mask_highz', additive_density: 'mask_highz', additive_d50_um: 'mask_highz',
  porosity: 'mask_pores', pore_size_um: 'mask_pores', solid_chord_x_um: 'mask_pores',
};
const oid = (e, d) => `${e}:${d}`;

export function buildModel(F) {
  if (F.schema_version !== 'epistemic-field/1') throw new Error(`unsupported contract ${F.schema_version}`);
  const dims = F.dimensions, DIM = Object.fromEntries(dims.map(d => [d.id, d]));
  const OBS = Object.fromEntries(F.observations.map(o => [o.id, o]));
  const ENT = Object.fromEntries(F.entities.map(e => [e.id, e]));
  const MISS = Object.fromEntries(F.missing_dimensions.map(m => [m.id, m]));
  const RIM = Object.fromEntries(F.rims.map(r => [r.id, r]));
  const PROF = Object.fromEntries(F.spatial_profiles.map(p => [p.id, p]));
  // presentation order: independent entities first (by id), reference-linked after
  const rowsOrder = [...F.entities].sort((a, b) => (a.independence.reference_linked - b.independence.reference_linked) || a.id.localeCompare(b.id));
  const rows = rowsOrder.map((e, i) => ({
    id: e.id, index: i, nFields: e.n_fields, sectionUm: e.geometry.known_section_um,
    refLinked: e.independence.reference_linked, pivotal: !!(e.leverage && e.leverage.flips), leverage: e.leverage,
    untestedAcq: e.acquisition.outside_tested_range.length > 0, differsAcq: e.acquisition.differs_from_approved.length,
    validityReasons: e.validity.reasons,
  }));
  const columns = dims.map((d, j) => ({
    id: d.id, index: j, acquired: d.acquired, label: d.label, short: d.short_label,
    unit: d.display ? d.display.unit : '', factor: d.display ? d.display.factor : 1, cls: d.robustness ? d.robustness.cls : null,
    mdc: d.reference ? d.reference.mdc95_3tiles : null, spatial: d.spatial_support || null,
  }));
  const keys = [];
  rows.forEach(r => columns.forEach(c => {
    const id = oid(r.id, c.id);
    if (c.acquired) {
      const o = OBS[id];
      keys.push({ id, entity: r.id, dimension: c.id, row: r.index, col: c.index, kind: 'observation', obs: o,
                  valueText: formatValue(o.value, c), refLinked: r.refLinked });
    } else {
      keys.push({ id, entity: r.id, dimension: c.id, row: r.index, col: c.index, kind: 'missing', missing: MISS[id], refLinked: r.refLinked });
    }
  }));
  const actions = F.actions.map(a => ({ ...a, reach: actionReach(a, F, RIM, OBS) }));
  return { F, DIM, OBS, ENT, MISS, RIM, PROF, rows, columns, keys, actions,
           meta: { batch: F.context.batch, reference: F.context.reference, verdict: F.decision.verdict, p: F.decision.p_batch,
                   role: F.context.role || 'incoming',
                   nIndependent: F.decision.n_independent, pivotal: F.decision.pivotal, linked: F.decision.reference_linked,
                   reasons: F.decision.reasons } };
}

export function formatValue(v, c) {
  if (v == null) return '–';
  const x = v * (c.factor || 1);
  return Math.abs(x) >= 100 ? x.toFixed(0) : x.toPrecision(3);
}

// What an action ADDRESSES (targets) and what CAUSED it (trigger rims and facts), mapped onto field elements.
export function actionReach(a, F, RIM, OBS) {
  const keys = new Set(a.targets.observations);
  const sockets = new Set();
  if (a.targets.dimensions.includes('composition')) a.targets.entities.forEach(e => sockets.add(oid(e, 'composition')));
  const cause = new Set(); let batch = false;
  for (const rid of a.triggered_by) {
    const r = RIM[rid]; if (!r) continue;
    if (r.scope === 'observation') cause.add(r.target);
    else if (r.scope === 'batch') batch = true;
    else if (r.scope === 'entity' && r.basis && r.basis.observations) r.basis.observations.forEach(x => cause.add(x));
    else if (r.scope === 'entity' && r.type === 'composition') sockets.add(oid(r.target, 'composition'));
  }
  for (const f of a.trigger_facts) {
    if (f.collection === 'observations' && OBS[f.id]) cause.add(f.id);
    if (f.collection === 'decision') batch = true;
  }
  const cols = new Set(a.targets.dimensions.filter(d => d !== 'composition'));
  return { keys: [...keys], causeKeys: [...cause].filter(k => !keys.has(k)), rows: [...a.targets.entities], cols: [...cols],
           sockets: [...sockets], batch, hue: ADDRESS_HUE[a.addresses] || HUE.capture };
}

// ---------------------------------------------------------------------------------------------------
// Five-stage projection.  Each stage asks a different question, so the category (hue) changes with the stage:
//   SIGNAL   measured deviation           SCRUTINY  reliability / acquisition / independence
//   FIELD    what bounds the envelope      OUTER RIM consequential unresolved limits     NEXT CAPTURE action reach
// Returns {category, hue, chroma 0..1, finish, emissive (exceptional only), ghost, quiet, ring, ringStrength, showValue}.
// Stage projection of one key (presentation only; every input is a contract field).
//   chroma = relevance in the current stage, on the CHROMA ladder (palette.js); ink = typographic contrast tier
//   SIGNAL     exceedance |z|/q95 (reference-linked micrographs at half: no independent weight)
//   SCRUTINY   survivors keep their signal chroma; failures drop to <= clear in the hue of their cause
//   FIELD      dominant envelope share x proximity to the decision threshold (an envelope matters where it can flip status)
//   OUTER RIM  consequential limits rich (faint emission on the pivotal micrograph); others pastel; settled recede to white
//   NEXT       the selected action's targets rich, its triggers clear, everything else recedes
export function keyVisual(M, key, stage, sel = {}) {
  const s = typeof stage === 'number' ? stage : STAGES.indexOf(stage);
  const e = M.ENT[key.entity];
  const v = { category: 'in_family', hue: MATERIAL.ivory, chroma: 0, finish: 'gloss', emissive: 0, ghost: false, quiet: false,
              ring: null, ringStrength: 0, showValue: true, sub: '', ink: 'full' };
  const linked = e.independence.reference_linked, untested = e.acquisition.outside_tested_range.length > 0;
  if (key.kind === 'missing') {
    v.finish = 'socket'; v.showValue = false; v.category = 'not_acquired';
    if (s === 3 && key.missing && key.missing.consequential) { v.ring = HUE.composition; v.ringStrength = 1; }
    return applySelection(M, key, s, sel, v);
  }
  const o = key.obs, rr = o.reference_relation;
  if (rr.status === 'not_measurable') { v.finish = 'glass'; v.showValue = false; v.category = 'not_measurable'; return applySelection(M, key, s, sel, v); }
  const deviating = rr.status === 'deviant' || rr.status === 'out';
  const dirCat = rr.direction < 0 ? 'below' : 'above', dirHue = HUE[dirCat];
  const x = rr.exceedance_ratio, sig = chromaFromExceedance(x) * (linked ? 0.5 : 1);
  const extreme = rr.status === 'out' && x >= 2.5 && !linked;          // the emission tail: far beyond q99, independent
  const pivotal = !!(e.leverage && e.leverage.flips);
  const set = (cat, hue, chroma, emissive = 0) => { v.category = cat; v.hue = hue; v.chroma = chroma; v.emissive = emissive; };
  const zText = `z ${rr.z >= 0 ? '+' : '−'}${Math.abs(rr.z).toFixed(1)}`;
  if (linked) v.ghost = true;
  if (s === 0) {                                        // SIGNAL: measured deviation only (quantitative, two families)
    set(deviating ? dirCat : 'in_family', dirHue, sig, extreme ? 0.1 : 0);
    v.ink = deviating ? 'full' : 'medium'; v.sub = zText;
  } else if (s === 1) {                                 // SCRUTINY: does the evidence hold?
    if (linked) { set('provenance', HUE.provenance, 0.35); v.ink = 'soft'; }
    else if (deviating && o.scrutiny.outcome === 'survives') set('survives', dirHue, sig, extreme ? 0.1 : 0);
    else if (deviating) {
      const f = FAIL_PRECEDENCE.find(([c]) => o.scrutiny.failed.includes(c)), cat = f ? f[1] : 'acquisition';
      set(cat, CATEGORY[cat].hue, Math.min(CHROMA.clear, Math.max(CHROMA.pastel, 0.6 * sig))); v.ink = 'medium';
    } else if (untested) { set('acquisition', HUE.acquisition, CHROMA.pastel); v.ink = 'medium'; }
    else { set('in_family', dirHue, 0); v.ink = 'medium'; }
    if (untested || o.acquisition_explains_deviation) v.finish = 'matte';
    v.sub = { provenance: 'ref-linked', survives: 'survives', acquisition: deviating ? 'acq. could explain' : 'untested acq.', spatial_inconsistent: 'inconsistent' }[v.category] || zText;
  } else if (s === 2) {                                 // FIELD: which part of the envelope dominates, where it matters
    const vs = o.variance_shares;
    const [cat, share] = [['spatial_sampling', vs.spatial_sampling], ['baseline_support', vs.baseline_support], ['material_spread', vs.approved_material]]
      .sort((a, b) => b[1] - a[1])[0];
    const dominance = ramp(share, 0.4, 0.9, 0, 1), relevance = ramp(x, 0.5, 1.2, 0.15, 1);
    let c = cat === 'material_spread' ? CHROMA.pastel * relevance : 0.06 + 0.86 * dominance * relevance;
    if (linked) c *= 0.5;
    set(cat, CATEGORY[cat].hue, c);
    v.ink = c >= CHROMA.clear ? 'full' : 'medium';
    v.sub = `${{ spatial_sampling: 'spatial', baseline_support: 'baseline', material_spread: 'material' }[cat]} ${Math.round(100 * share)}%`;
  } else if (s === 3) {                                 // OUTER RIM: consequential unresolved limits dominate
    v.quiet = true; v.category = 'settled'; v.ink = 'soft';
    const types = o.rims.map(r => M.RIM[r]).filter(Boolean);
    const t = RIM_PRECEDENCE.find(r => types.some(x2 => x2.type === r));
    if (t) {
      const cons = types.some(r => r.type === t && r.consequential); v.quiet = false;
      set('rim_' + t, RIM_HUE[t], cons ? 0.86 : CHROMA.pastel + 0.04, cons && pivotal ? 0.08 : 0); v.ink = cons ? 'full' : 'medium';
    } else if (untested) { v.quiet = false; set('rim_acquisition', HUE.acquisition, CHROMA.pastel + 0.04); v.ink = 'medium'; }
    if (untested || o.acquisition_explains_deviation) v.finish = 'matte';
    v.sub = t ? RIM_PRECEDENCE.filter(r => types.some(x2 => x2.type === r)).join(' · ') : untested ? 'untested acq.' : '';
  } else {                                              // NEXT CAPTURE: what the selected action addresses / why
    v.quiet = true; v.category = 'settled'; v.ink = 'soft';
    const A = sel.action != null ? M.actions[sel.action] : null;
    if (A && A.reach.keys.includes(key.id)) { v.quiet = false; set('action_target', A.reach.hue, 0.86, 0.06); v.ink = 'full'; }
    else if (A && A.reach.causeKeys.includes(key.id)) { v.quiet = false; set('action_cause', A.reach.hue, CHROMA.clear); v.ink = 'full'; }
    v.sub = v.category === 'action_target' ? `${A.verb.toLowerCase()} target` : v.category === 'action_cause' ? 'trigger' : '';
  }
  return applySelection(M, key, s, sel, v);
}
const ramp = (x, x0, x1, y0, y1) => y0 + (y1 - y0) * Math.max(0, Math.min(1, ((x ?? 0) - x0) / (x1 - x0)));

function applySelection(M, key, s, sel, v) {
  if (s === 4 && key.kind === 'missing' && sel.action != null) {
    const A = M.actions[sel.action];
    if (A && A.reach.sockets.includes(key.id)) { v.ring = A.reach.hue; v.ringStrength = 1; v.category = 'action_target'; }
  }
  if (key.kind === 'missing') v.quiet = !v.ring;            // an empty socket is quiet unless a rule rings it
  v.selected = sel.key === key.id;
  v.linked = !!(sel.linkedKeys && sel.linkedKeys.includes(key.id));
  v.recede = false;                                          // selection is optical (sheen) only; the field stays readable
  return v;
}

export function categoryInfo(v) {
  const c = CATEGORY[v.category] || CATEGORY.in_family;
  return { id: v.category, label: c.label, hue: c.hue || v.hue };
}

// row / column / frame accents for the instrument body (non-key structure)
export function structureVisual(M, stage, sel = {}) {
  const s = typeof stage === 'number' ? stage : STAGES.indexOf(stage);
  const pop = M.F.rims.find(r => r.type === 'population');
  const out = { rows: {}, cols: {}, rail: null };
  M.rows.forEach(r => { out.rows[r.id] = { accent: null, label: r.refLinked ? 'reference-linked' : null }; });
  if (s === 3) {
    M.rows.forEach(r => { if (r.pivotal) out.rows[r.id].accent = HUE.population; });
    if (pop) out.rail = { hue: HUE.population, strength: pop.consequential ? 1 : 0.35 };
    M.columns.forEach(c => { if (c.spatial && c.spatial.cls !== 'short-range') out.cols[c.id] = { accent: HUE.spatial }; });
  }
  if (s === 4 && sel.action != null) {
    const A = M.actions[sel.action];
    A.reach.rows.forEach(id => { if (out.rows[id]) out.rows[id].accent = A.reach.hue; });
    A.reach.cols.forEach(id => { out.cols[id] = { accent: A.reach.hue }; });
    if (A.reach.batch) out.rail = { hue: A.reach.hue, strength: 1 };
  }
  return out;
}

// concise, data-derived interpretation line (prose built only from contract fields)
// what an observation is compared with: the approved population (incoming) or the other reference parents (self-audit)
export const isReference = M => M.meta.role === 'reference';
export const frameWord = M => (isReference(M) ? 'the other reference micrographs' : 'approved');
export const envelopeWord = M => (isReference(M) ? 'its leave-one-out envelope' : 'the approved envelope');

export function interpretation(M, stage, sel = {}) {
  const s = typeof stage === 'number' ? stage : STAGES.indexOf(stage);
  const F = M.F, sum = F.summary;
  const fmtObs = id => { const o = M.OBS[id], c = M.columns.find(x => x.id === o.dimension);
    return `${o.entity} ${c.short.toLowerCase()} ${formatValue(o.value, c)} vs ${formatValue(o.reference_relation.approved_mean, c)} ${c.unit}`; };
  if (sel.key) return keyInterpretation(M, sel.key, s);
  if (s === 0) {
    if (!sum.n_deviating) return `No observation lies outside ${envelopeWord(M)}.`;
    const top = [...sum.deviating].sort((a, b) => M.OBS[b].reference_relation.exceedance_ratio - M.OBS[a].reference_relation.exceedance_ratio)[0];
    return `${sum.n_deviating} observation${sum.n_deviating > 1 ? 's' : ''} outside ${envelopeWord(M)}; strongest: ${fmtObs(top)}.`;
  }
  if (s === 1) {
    const linked = F.decision.reference_linked.length;
    return `${sum.n_surviving} of ${sum.n_deviating} ${isReference(M) ? 'local departures' : 'deviations'} survive scrutiny` + (sum.surviving.length ? ` (${sum.surviving.join(', ')})` : '') +
      `.${linked ? ` ${linked} micrograph${linked > 1 ? 's are' : ' is'} reference-linked and carr${linked > 1 ? 'y' : 'ies'} no independent weight.` : ''}`;
  }
  if (s === 2) {
    const ms = F.observations.filter(o => o.variance_shares);
    const sp = ms.filter(o => o.variance_shares.spatial_sampling >= o.variance_shares.baseline_support).length;
    return `Envelope widths: spatial sampling is the larger reducible part in ${sp} of ${ms.length} observations; baseline support in ${ms.length - sp}.`;
  }
  if (s === 3) {
    const cons = F.rims.filter(r => r.consequential);
    return cons.length ? `${cons.length} consequential limit${cons.length > 1 ? 's' : ''}: ` + cons.map(r => `${r.type} (${r.target})`).join(' · ') + '.'
      : isReference(M) ? 'No consequential limit: the reference supports its role at the tested scales.' : 'No consequential limit: remaining rims do not affect the decision.';
  }
  if (s === 4) {
    const A = sel.action != null ? M.actions[sel.action] : M.actions[0];
    if (!A) return 'No capture recommended.';
    const outcomes = {
      acquisition: 'separates acquisition from material', scale: 'resolves scale truncation',
      spatial_extent: 'bounds spatial extent', composition: 'resolves composition identity',
      spatial_sampling: 'improves independent spatial sampling', validity: 'restores measurement validity',
      population: A.verb === 'BASELINE' ? 'narrows baseline uncertainty' : 'constrains lot prevalence',
    };
    return `${A.title} — ${outcomes[A.addresses] || `addresses ${A.addresses.replaceAll('_', ' ')}`}.`;
  }
  return '';
}

export function keyInterpretation(M, id, s) {
  const k = M.keys.find(x => x.id === id); if (!k) return '';
  const c = M.columns.find(x => x.id === k.dimension);
  if (k.kind === 'missing') return `${k.entity} · ${c.label}: not acquired` + (k.missing.consequential ? ' — consequential: the surviving deviation depends on it.' : '.');
  const o = k.obs, rr = o.reference_relation;
  if (rr.status === 'not_measurable') return `${k.entity} · ${c.short}: not measurable (${M.ENT[k.entity].validity.reasons.join('; ')}).`;
  const base = `${k.entity} · ${c.short}: ${formatValue(o.value, c)} ${c.unit} vs ${frameWord(M)} ${formatValue(rr.approved_mean, c)} (z ${rr.z >= 0 ? '+' : ''}${rr.z.toFixed(1)}, ${rr.status})`;
  if (s === 1 && o.scrutiny.outcome !== 'not_applicable') return `${base} — ${o.scrutiny.outcome}${o.scrutiny.failed.length ? ': ' + o.scrutiny.failed.join(', ').replaceAll('_', ' ') : ''}.`;
  if (s === 2) { const v = o.variance_shares; return `${base} — envelope: material ${pct(v.approved_material)}, spatial sampling ${pct(v.spatial_sampling)}, baseline ${pct(v.baseline_support)}.`; }
  if (s === 3 && o.rims.length) return `${base} — ${o.rims.map(r => M.RIM[r].statement).join(' ')}`;
  return base + '.';
}
const pct = x => `${Math.round(100 * x)}%`;
