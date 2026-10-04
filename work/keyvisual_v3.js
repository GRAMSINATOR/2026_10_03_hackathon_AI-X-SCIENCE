// ---------------------------------------------------------------------------------------------------
// Five-stage projection.  Each stage asks a different question, so the category (hue) changes with the stage:
//   SIGNAL   measured deviation           SCRUTINY  reliability / acquisition / independence
//   FIELD    what bounds the envelope      OUTER RIM consequential unresolved limits     NEXT CAPTURE action reach
// Returns {category, hue, chroma 0..1, finish, emissive (exceptional only), ghost, quiet, ring, ringStrength, showValue}.
export function keyVisual(M, key, stage, sel = {}) {
  const s = typeof stage === 'number' ? stage : STAGES.indexOf(stage);
  const e = M.ENT[key.entity];
  const v = { category: 'in_family', hue: MATERIAL.ivory, chroma: 0, finish: 'gloss', emissive: 0, ghost: false, quiet: false,
              ring: null, ringStrength: 0, showValue: true };
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
  const set = (cat, hue, chroma, emissive = 0) => { v.category = cat; v.hue = hue; v.chroma = chroma; v.emissive = emissive; };
  if (s === 0) {                                        // SIGNAL: measured deviation only
    set(deviating ? dirCat : 'in_family', dirHue, chromaFromExceedance(rr.exceedance_ratio), rr.status === 'out' ? 0.3 : 0);
  } else if (s === 1) {                                 // SCRUTINY: does the evidence hold?
    if (linked) { set('provenance', HUE.provenance, 0.42); v.ghost = true; }
    else if (deviating && o.scrutiny.outcome === 'survives') set('survives', dirHue, chromaFromExceedance(rr.exceedance_ratio), rr.status === 'out' ? 0.3 : 0);
    else if (deviating) { const f = FAIL_PRECEDENCE.find(([c]) => o.scrutiny.failed.includes(c)); const cat = f ? f[1] : 'acquisition'; set(cat, CATEGORY[cat].hue, 0.52); }
    else if (untested) set('acquisition', HUE.acquisition, 0.22);
    else set('in_family', dirHue, chromaFromExceedance(rr.exceedance_ratio) * 0.5);
    if (untested || o.acquisition_explains_deviation) v.finish = 'matte';
  } else if (s === 2) {                                 // FIELD: which part of the envelope dominates
    const vs = o.variance_shares;
    const [cat, share] = [['spatial_sampling', vs.spatial_sampling], ['baseline_support', vs.baseline_support], ['material_spread', vs.approved_material]]
      .sort((a, b) => b[1] - a[1])[0];
    set(cat, CATEGORY[cat].hue, 0.08 + 0.5 * Math.max(0, Math.min(1, (share - 0.4) / 0.6)));
    if (linked) v.ghost = true;
  } else if (s === 3) {                                 // OUTER RIM: consequential unresolved limits
    v.quiet = true; v.category = 'settled';
    const types = o.rims.map(r => M.RIM[r]).filter(Boolean);
    const t = RIM_PRECEDENCE.find(x => types.some(r => r.type === x));
    if (t) { const cons = types.some(r => r.type === t && r.consequential); v.quiet = false; set('rim_' + t, RIM_HUE[t], cons ? 0.75 : 0.34, cons ? 0.1 : 0); }
    else if (untested) { v.quiet = false; set('rim_acquisition', HUE.acquisition, 0.3); }
    if (untested || o.acquisition_explains_deviation) v.finish = 'matte';
    if (linked) v.ghost = true;
  } else {                                              // NEXT CAPTURE: what the selected action addresses / why
    v.quiet = true; v.category = 'settled';
    const A = sel.action != null ? M.actions[sel.action] : null;
    if (A && A.reach.keys.includes(key.id)) { v.quiet = false; set('action_target', A.reach.hue, 0.75, 0.16); }
    else if (A && A.reach.causeKeys.includes(key.id)) { v.quiet = false; set('action_cause', A.reach.hue, 0.32); }
    if (linked) v.ghost = true;
  }
  return applySelection(M, key, s, sel, v);
}

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
