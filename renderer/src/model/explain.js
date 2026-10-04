// Explanation panel model: rich, contract-driven detail for the selected key, colour-linked to the key categories.
// Sections are {id, title, hue, rows?: [[label, value]], notes?: [{text, hue}], bar?: [{label, share, hue}]}.
import { CATEGORY, HUE, MATERIAL, RIM_HUE, mix } from './palette.js';
import { formatValue, keyVisual, categoryInfo, STAGES } from './adapter.js';

const pct = x => `${Math.round(100 * x)}%`;
const FAIL_TEXT = {
  acquisition_could_explain: ['the worst tested acquisition change could explain ≥ 50% of the deviation', HUE.acquisition],
  spatially_inconsistent: ['not consistent across the micrograph’s fields', HUE.spatial],
  moderate_robustness_dimension: ['KPI is acquisition-sensitive (moderate robustness class)', HUE.acquisition],
};
const STAGE_MEANING = {
  above: 'Measured above the approved population envelope.', below: 'Measured below the approved population envelope.',
  in_family: 'Inside the approved envelope for this micrograph’s sampling.',
  survives: 'The deviation survives scrutiny: robust KPI, consistent across fields, not explained by tested acquisition changes.',
  acquisition: 'Reliability is limited by acquisition: tested acquisition changes could produce this, or the KPI is acquisition-sensitive.',
  spatial_inconsistent: 'The apparent deviation is not consistent across the fields of this micrograph.',
  provenance: 'This micrograph continues an approved baseline section: shown, but it carries no independent weight.',
  spatial_sampling: 'This envelope is mostly spatial sampling: more fields of this micrograph would narrow it.',
  baseline_support: 'This envelope is mostly baseline-estimation uncertainty: more approved micrographs would narrow it.',
  material_spread: 'This envelope is mostly genuine approved material spread: more sampling would not narrow it much.',
  rim_spatial: 'Spatial support fades here: the evidence reaches the edge of what was captured, or varies on larger scales.',
  rim_scale: 'Resolution limit: the deviating population piles up at the detection floor of the current pixel size.',
  rim_composition: 'Composition unresolved: the deviation is in a phase whose chemistry was never measured.',
  rim_population: 'Population support limit.', rim_acquisition: 'Acquired outside the range whose acquisition effects were tested.',
  settled: 'No consequential limit attached to this observation.',
  action_target: 'Addressed by the selected next capture.', action_cause: 'Part of the evidence that triggered the selected next capture.',
  not_measurable: 'Not measurable: the validity gate failed for this KPI family.', not_acquired: 'This dimension was never acquired.',
};

export function explainKey(M, keyId, stage, sel = {}) {
  const k = M.keys.find(x => x.id === keyId); if (!k) return null;
  const c = M.columns.find(x => x.id === k.dimension), e = M.ENT[k.entity], row = M.rows.find(r => r.id === k.entity);
  const v = keyVisual(M, k, stage, sel), cat = categoryInfo(v), sections = [];
  sections.push({ id: 'category', title: cat.label, hue: cat.hue === MATERIAL.ivory ? null : cat.hue, notes: [{ text: STAGE_MEANING[cat.id] || '' }] });
  if (k.kind === 'missing') {
    const m = k.missing;
    sections.push({ id: 'composition', title: 'Composition', hue: HUE.composition, rows: [['acquired', 'no (no EDS / spectroscopy)'],
      ['consequential', m.consequential ? 'yes' : 'no'],
      ...(m.basis.dependent_observations.length ? [['depends on it', m.basis.dependent_observations.join(', ')]] : []),
      ...(m.basis.fines_bse_intensity_u != null ? [['fine-object BSE intensity', `u = ${m.basis.fines_bse_intensity_u.toFixed(2)}` +
        (m.basis.approved_fines_bse_intensity_range ? ` (approved ${m.basis.approved_fines_bse_intensity_range.map(x => x.toFixed(2)).join('–')})` : '')]] : [])] });
    pushActions(M, k, sections);
    return { title: `${k.entity} · ${c.label}`, subtitle: STAGES[stage], sections };
  }
  const o = k.obs, rr = o.reference_relation, f = x => formatValue(x, c);
  if (rr.status === 'not_measurable') {
    sections.push({ id: 'validity', title: 'Validity gate', hue: HUE.acquisition, notes: e.validity.reasons.map(t => ({ text: t })) });
    return { title: `${k.entity} · ${c.label}`, subtitle: STAGES[stage], sections };
  }
  const dirHue = rr.direction < 0 ? HUE.below : HUE.above, dev = rr.status !== 'in';
  sections.push({ id: 'measurement', title: 'Measurement', hue: dev ? dirHue : null, rows: [
    ['value', `${f(o.value)} ${c.unit}  (${rr.status})`],
    ['approved', `${f(rr.approved_mean)} ± ${f(M.DIM[c.id].reference.sd)} ${c.unit}`],
    ['95% envelope here', `${f(rr.envelope95[0])} – ${f(rr.envelope95[1])} ${c.unit}`],
    ['z vs thresholds', `${rr.z >= 0 ? '+' : ''}${rr.z.toFixed(2)}  (q95 ${rr.q95.toFixed(2)}, q99 ${rr.q99.toFixed(2)})`],
    ['fields', Object.entries(o.per_field).map(([id, x]) => `${id.split('__')[1]} ${f(x)}`).join(' · ')],
    ...(rr.beyond_reference_support ? [['reference support', 'outside every approved field (extrapolation)']] : [])] });
  const sc = o.scrutiny;
  if (sc.outcome !== 'not_applicable' || row.refLinked || row.untestedAcq) {
    const notes = [];
    if (row.refLinked) notes.push({ text: 'reference-linked: physical continuation of an approved section', hue: HUE.provenance });
    sc.failed.forEach(code => notes.push({ text: FAIL_TEXT[code][0], hue: FAIL_TEXT[code][1] }));
    if (sc.outcome === 'survives') notes.push({ text: 'robust KPI, consistent across fields, tested acquisition changes explain ' +
      `${pct(sc.acquisition_share || 0)}` + (sc.conditional_on_untested_acquisition ? ' (conditional: untested acquisition)' : ''), hue: dirHue });
    sections.push({ id: 'scrutiny', title: `Scrutiny · ${sc.outcome.replace('_', ' ')}`, hue: sc.outcome === 'survives' ? dirHue : sc.failed.length ? FAIL_TEXT[sc.failed[0]][1] : null,
      rows: [['fields beyond 95%', `${sc.fields_beyond_95} / ${sc.n_fields}`],
             ['acquisition share', sc.acquisition_share == null ? '—' : `${pct(sc.acquisition_share)} (worst tested: ${M.DIM[c.id].robustness.worst_perturbation})`],
             ['KPI robustness', M.DIM[c.id].robustness.cls]], notes });
  }
  const vs = o.variance_shares, D = M.DIM[c.id];
  sections.push({ id: 'envelope', title: 'Envelope composition', hue: null,
    bar: [{ label: 'approved material', share: vs.approved_material, hue: HUE.material }, { label: 'spatial sampling', share: vs.spatial_sampling, hue: HUE.spatial },
          { label: 'baseline support', share: vs.baseline_support, hue: HUE.population }],
    rows: [['minimum detectable change', `±${f(D.reference.mdc95_3tiles)} ${c.unit} (3 fields, ${D.reference.n_micrographs} approved micrographs)`],
           ...(D.spatial_support ? [['spatial structure', D.spatial_support.cls === 'short-range' ? 'short-range (any extra area helps)'
             : D.spatial_support.cls === 'fov-scale' ? `≈${Math.round(D.spatial_support.range_um)} µm: comparable to the field width`
             : `> ${Math.round(D.spatial_support.range_um)} µm: larger than the coherent capture`]] : [])] });
  const rims = [...o.rims.map(r => M.RIM[r]), ...M.F.rims.filter(r => (r.scope === 'entity' && r.target === k.entity && r.type !== 'scale') ||
                (r.scope === 'dimension' && r.target === c.id))].filter((r, i, a) => r && a.indexOf(r) === i);
  if (rims.length) sections.push({ id: 'limits', title: 'Limits (outer rim)', hue: null,
    notes: rims.map(r => ({ text: `${r.type}${r.consequential ? ' · consequential' : ''} — ${r.statement}`, hue: RIM_HUE[r.type] || HUE.acquisition })) });
  const acq = e.acquisition;
  sections.push({ id: 'acquisition', title: 'Acquisition', hue: acq.outside_tested_range.length || o.acquisition_explains_deviation ? HUE.acquisition : null,
    rows: [['vs approved micrographs', acq.differs_from_approved.length ? `${acq.differs_from_approved.length} metrics differ (${acq.differs_from_approved.slice(0, 3).map(d => d.label).join(', ')})` : 'within approved range'],
           ['vs tested range', acq.outside_tested_range.length ? `outside: ${acq.outside_tested_range.map(d => d.label).join(', ')}` : 'within the range whose effects were tested']] });
  if (e.leverage) sections.push({ id: 'leverage', title: 'Decision leverage', hue: e.leverage.flips ? HUE.population : null, rows: [
    ['verdict without it', `${e.leverage.verdict_without} (p = ${e.leverage.p_without.toFixed(2)})`],
    ['pivotal', e.leverage.flips ? (e.leverage.cause === 'min_independent_count' ? 'yes — batch would have too few independent micrographs' : 'yes — carries the decisive evidence') : 'no']] });
  else sections.push({ id: 'leverage', title: 'Decision leverage', hue: HUE.provenance, notes: [{ text: 'reference-linked: excluded from the batch test' }] });
  const miss = M.MISS[`${k.entity}:composition`];
  if (miss && miss.consequential && miss.basis.dependent_observations.includes(k.id))
    sections.push({ id: 'composition', title: 'Composition', hue: HUE.composition, notes: [{ text: 'this deviation is in the high-Z phase, whose chemistry was not acquired' }] });
  pushActions(M, k, sections);
  return { title: `${k.entity} · ${c.label}`, subtitle: STAGES[stage], sections: focus(sections, stage) };
}

// each stage leads with the section it projects; only those keep their category accent, so colour stays tied to the keys
const STAGE_FOCUS = [['measurement'], ['scrutiny', 'acquisition'], ['envelope'], ['limits', 'composition', 'acquisition'], ['actions']];
function focus(sections, stage) {
  const f = STAGE_FOCUS[stage] || [], rank = s => (s.id === 'category' ? -1 : f.includes(s.id) ? f.indexOf(s.id) : 99);
  return sections.map((s, i) => ({ ...s, hue: s.id === 'category' || f.includes(s.id) ? s.hue : null, i }))
    .sort((a, b) => rank(a) - rank(b) || a.i - b.i);
}

function pushActions(M, k, sections) {
  const acts = M.actions.filter(a => a.reach.keys.includes(k.id) || a.reach.causeKeys.includes(k.id) || a.reach.sockets.includes(k.id));
  if (acts.length) sections.push({ id: 'actions', title: 'Next capture involving this evidence', hue: null,
    notes: acts.map(a => ({ text: `${a.verb} · ${a.title} (tier ${a.tier}, ${a.status})`, hue: a.reach.hue })) });
}

// stage-level overview (nothing selected): decision + what this stage projects
export function explainStage(M, stage, action) {
  const F = M.F, d = F.decision, sections = [];
  // the decision itself lives in the brief above; the examiner overview starts from the lens's own evidence
  sections.push({ id: 'independence', title: 'Independence', hue: null, rows: [['independent micrographs', String(d.n_independent)],
    ['pivotal', d.pivotal.join(', ') || '—'], ['reference-linked', d.reference_linked.join(', ') || '—']] });
  if (stage === 4 && action != null) sections.push(explainAction(M, action));
  if (stage <= 2) {   // nearest to (or beyond) the envelope, in the current stage's key colours
    const top = M.keys.filter(k => k.kind === 'observation' && k.obs.reference_relation.exceedance_ratio != null)
      .sort((a, b) => b.obs.reference_relation.exceedance_ratio - a.obs.reference_relation.exceedance_ratio).slice(0, 6);
    sections.push({ id: 'nearest', title: 'Nearest the approved envelope', hue: null,
      notes: top.map(k => { const v = keyVisual(M, k, stage, {}), c = M.columns.find(x => x.id === k.dimension), rr = k.obs.reference_relation;
        return { text: `${k.entity} · ${c.short}: ${k.valueText} ${c.unit} · z ${rr.z >= 0 ? '+' : '−'}${Math.abs(rr.z).toFixed(1)} · ${(rr.exceedance_ratio).toFixed(2)}× q95 · ${rr.status}` +
          (k.obs.scrutiny && k.obs.scrutiny.outcome !== 'not_applicable' ? ` · ${k.obs.scrutiny.outcome.replace('_', ' ')}` : ''),
          hue: v.chroma > 0.05 ? mix(MATERIAL.ivory, v.hue, Math.max(0.35, v.chroma)) : '#c9c7c0' }; }) });
  }
  if (stage === 3) sections.push({ id: 'limits', title: 'Limits (outer rim)', hue: null,
    notes: [...F.rims].sort((a, b) => b.consequential - a.consequential).map(r => ({ text: `${r.type} · ${r.target}${r.consequential ? ' · consequential' : ''} — ${r.statement}`,
      hue: RIM_HUE[r.type] || HUE.acquisition })) });
  return { title: M.meta.batch, subtitle: STAGES[stage], sections };
}

function effectText(M, e) {
  if (!e) return null;
  if (e.kind === 'spatial_extent') return `extends the ${Math.round(e.known_extent_um)} µm coherent capture past its open ${e.open_edges.join(' and ')} edge`;
  if (e.kind === 'prevalence_ci_width') return `prevalence 95% CI width ${pct(e.current)} → ` +
    e.projected.map(p => `${pct(p.ci_width)} (+${p.added_sections})`).join(', ') + ` sections, if ${e.assumption}`;
  if (e.kind === 'field_spacing') return `fields ≥ ${Math.round(e.min_spacing_um)} µm apart sample independent structure (${e.basis})`;
  if (e.kind === 'minimum_detectable_change') return `MDC (3 fields), +5 approved micrographs: ` + e.projected.map(p => {
    const c = M.columns.find(x => x.id === p.dimension); return c ? `${c.short} ±${formatValue(p.mdc95_now, c)} → ±${formatValue(p.mdc95_with_plus5, c)}` : null; }).filter(Boolean).join(' · ');
  return null;
}

// the selected next capture: why it is proposed (evidence + rationale) and what it would change
export function explainAction(M, i) {
  const A = M.actions[i];
  return { id: 'action', title: `${A.verb} · ${A.title}`, hue: A.reach.hue,
    rows: [['addresses', A.addresses.replace('_', ' ')], ['tier · status · cost', `${A.tier} · ${A.status} · ${A.cost}`],
           ...(effectText(M, A.effect) ? [['expected effect', effectText(M, A.effect)]] : [])],
    notes: [...A.evidence.map(t => ({ text: t, hue: A.reach.hue })), { text: A.rationale }] };
}

export function legendFor(M, stage, sel = {}) {
  const seen = new Map();
  M.keys.forEach(k => { const v = keyVisual(M, k, stage, sel); if (v.category !== 'settled' && v.category !== 'in_family') { const ci = categoryInfo(v); if (!seen.has(ci.label)) seen.set(ci.label, ci.hue); } });
  return [...seen.entries()].map(([label, hue]) => ({ label, hue }));
}
export { CATEGORY };
