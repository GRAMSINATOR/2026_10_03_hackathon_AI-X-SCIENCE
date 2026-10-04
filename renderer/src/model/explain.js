// Explanation panel model: rich, contract-driven detail for the selected key, colour-linked to the key categories.
// Sections are {id, title, hue, rows?: [[label, value]], notes?: [{text, hue}], bar?: [{label, share, hue}]}.
import { CATEGORY, HUE, MATERIAL, RIM_HUE, mix } from './palette.js';
import { formatValue, keyVisual, categoryInfo, STAGES, isReference } from './adapter.js';

const pct = x => `${Math.round(100 * x)}%`;
const spatialRows = D => {
  const s = D.spatial_support, u = D.uncertainty_model;
  if (!s) return [];
  const h = s.scale_dependent_heterogeneity || [], last = h[h.length - 1], ms = s.scale_model_sensitivity;
  const rows = [['observation / uncertainty', `${u.observation_family.replaceAll('_', ' ')} · ${u.uncertainty_adapter.replaceAll('_', ' ')}`]];
  if (last && u.observation_family === 'spatial_count_process')
    rows.push(['scale descriptor', `${last.window_um} µm windows: Fano ${last.fano.toFixed(2)} (${last.n_parents} parents; Poisson is only a comparator)`]);
  else if (last && last.normalized_fluctuation)
    rows.push(['scale descriptor', `${last.window_um} µm windows: variance / p(1−p) ${last.normalized_fluctuation.parent_equal.toPrecision(3)} (${last.n_parents} parents)`]);
  if (ms && ms.parent_bootstrap?.median != null && ms.parent_bootstrap?.interval95?.length === 2)
    rows.push(['variance-slope audit', `current ${ms.operational_unweighted_beta.toFixed(2)} · support-weighted ${ms.support_weighted_beta.toFixed(2)} · parent bootstrap ${ms.parent_bootstrap.median.toFixed(2)} [${ms.parent_bootstrap.interval95.map(x => x.toFixed(2)).join(', ')}]`]);
  return rows;
};
const FAIL_TEXT = {
  acquisition_could_explain: ['the worst tested acquisition change could explain ≥ 50% of the deviation', HUE.acquisition],
  spatially_inconsistent: ['not consistent across the micrograph’s fields', HUE.spatial],
  moderate_robustness_dimension: ['KPI is acquisition-sensitive (moderate robustness class)', HUE.acquisition],
};
const STAGE_MEANING = {
  above: 'Measured above the selected reference-frame envelope.', below: 'Measured below the selected reference-frame envelope.',
  in_family: 'Inside the selected reference-frame envelope for this micrograph’s sampling.',
  survives: 'The deviation survives scrutiny: robust KPI, consistent across fields, not explained by tested acquisition changes.',
  acquisition: 'Reliability is limited by acquisition: tested acquisition changes could produce this, or the KPI is acquisition-sensitive.',
  spatial_inconsistent: 'The apparent deviation is not consistent across the fields of this micrograph.',
  provenance: 'This micrograph continues a reference-frame section: shown, but it carries no independent weight.',
  spatial_sampling: 'This envelope is mostly spatial sampling: more fields of this micrograph would narrow it.',
  baseline_support: 'This envelope is mostly reference-estimation uncertainty: more independent reference parents would narrow it.',
  material_spread: 'This envelope is mostly variation among reference parents: more target sampling would not narrow it much.',
  rim_spatial: 'Spatial support fades here: the evidence reaches the edge of what was captured, or varies on larger scales.',
  rim_scale: 'Resolution limit: the deviating population piles up at the detection floor of the current pixel size.',
  rim_composition: 'Composition unresolved: the deviation is in a phase whose chemistry was never measured.',
  rim_population: 'Population support limit.', rim_acquisition: 'Acquired outside the range whose acquisition effects were tested.',
  settled: 'No consequential limit attached to this observation.',
  action_target: 'Addressed by the selected next capture.', action_cause: 'Part of the evidence that triggered the selected next capture.',
  not_measurable: 'Not measurable: the validity gate failed for this KPI family.', not_acquired: 'This dimension was never acquired.',
};

// in a self-audit, an observation is compared with the other reference micrographs
const REF_WORDS = [['the selected reference-frame envelope', 'the envelope of the other reference micrographs'], ['reference-frame envelope', 'leave-one-out envelope'],
                   ['reference micrographs', 'other reference micrographs'], ['reference material', 'other reference material'], ['reference frame', 'other reference parents']];
export const inFrame = (M, t) => (t && isReference(M) ? REF_WORDS.reduce((s, [a, b]) => s.split(a).join(b), t) : t);

export function explainKey(M, keyId, stage, sel = {}) {
  const k = M.keys.find(x => x.id === keyId); if (!k) return null;
  const c = M.columns.find(x => x.id === k.dimension), e = M.ENT[k.entity], row = M.rows.find(r => r.id === k.entity);
  const v = keyVisual(M, k, stage, sel), cat = categoryInfo(v), sections = [];
  sections.push({ id: 'category', title: inFrame(M, cat.label), hue: cat.hue === MATERIAL.ivory ? null : cat.hue, notes: [{ text: inFrame(M, STAGE_MEANING[cat.id] || '') }] });
  if (k.kind === 'missing') {
    const m = k.missing;
    sections.push({ id: 'composition', title: 'Composition', hue: HUE.composition, rows: [['acquired', 'no (no EDS / spectroscopy)'],
      ['consequential', m.consequential ? 'yes' : 'no'],
      ...(m.basis.dependent_observations.length ? [['depends on it', m.basis.dependent_observations.join(', ')]] : []),
      ...(m.basis.fines_bse_intensity_u != null ? [['fine-object BSE intensity', `u = ${m.basis.fines_bse_intensity_u.toFixed(2)}` +
        (m.basis.approved_fines_bse_intensity_range ? ` (selected reference ${m.basis.approved_fines_bse_intensity_range.map(x => x.toFixed(2)).join('–')})` : '')]] : [])] });
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
    ...(rr.frame === 'leave_one_out'
      ? [['other reference micrographs', `${f(rr.approved_mean)} ${c.unit} (leave-one-out frame of ${rr.frame_n})`]]
      : [['selected reference', `${f(rr.approved_mean)} ± ${f(M.DIM[c.id].reference.sd)} ${c.unit}`]]),
    ['95% envelope here', `${f(rr.envelope95[0])} – ${f(rr.envelope95[1])} ${c.unit}`],
    ['z vs thresholds', `${rr.z >= 0 ? '+' : ''}${rr.z.toFixed(2)}  (q95 ${rr.q95.toFixed(2)}, q99 ${rr.q99.toFixed(2)})`],
    ['fields', Object.entries(o.per_field).map(([id, x]) => `${id.split('__')[1]} ${f(x)}`).join(' · ')],
    ...(rr.beyond_reference_support ? [['reference support', rr.frame === 'leave_one_out' ? 'outside every other reference field' : 'outside every selected-reference field (extrapolation)']] : [])] });
  const sc = o.scrutiny;
  if (sc.outcome !== 'not_applicable' || row.refLinked || row.untestedAcq) {
    const notes = [];
    if (row.refLinked) notes.push({ text: 'reference-linked: physical continuation of a selected-reference section', hue: HUE.provenance });
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
    bar: [{ label: 'reference-parent spread', share: vs.approved_material, hue: HUE.material }, { label: 'spatial sampling', share: vs.spatial_sampling, hue: HUE.spatial },
          { label: 'baseline support', share: vs.baseline_support, hue: HUE.population }],
    rows: [['minimum detectable change', `±${f(D.reference.mdc95_3tiles)} ${c.unit} (3 fields, ${D.reference.n_micrographs} reference parents)`],
           ...(D.spatial_support ? [['spatial structure', D.spatial_support.cls === 'short-range' ? 'short-range (any extra area helps)'
             : D.spatial_support.cls === 'fov-scale' ? `≈${Math.round(D.spatial_support.range_um)} µm: comparable to the field width`
             : `> ${Math.round(D.spatial_support.range_um)} µm: larger than the coherent capture`], ...spatialRows(D)] : [])] });
  const rims = [...o.rims.map(r => M.RIM[r]), ...M.F.rims.filter(r => (r.scope === 'entity' && r.target === k.entity && r.type !== 'scale') ||
                (r.scope === 'dimension' && r.target === c.id))].filter((r, i, a) => r && a.indexOf(r) === i);
  if (rims.length) sections.push({ id: 'limits', title: 'Limits (outer rim)', hue: null,
    notes: rims.map(r => ({ text: `${r.type}${r.consequential ? ' · consequential' : ''} — ${r.statement}`, hue: RIM_HUE[r.type] || HUE.acquisition })) });
  const acq = e.acquisition;
  sections.push({ id: 'acquisition', title: 'Acquisition', hue: acq.outside_tested_range.length || o.acquisition_explains_deviation ? HUE.acquisition : null,
    rows: [['vs selected reference', acq.differs_from_approved.length ? `${acq.differs_from_approved.length} metrics differ (${acq.differs_from_approved.slice(0, 3).map(d => d.label).join(', ')})` : 'within reference range'],
           ['vs tested range', acq.outside_tested_range.length ? `outside: ${acq.outside_tested_range.map(d => d.label).join(', ')}` : 'within the range whose effects were tested']] });
  if (isReference(M)) {   // a self-audit has no decision to lever; show how far this parent moves the reference instead
    const top = Object.entries(e.reference_influence || {}).filter(([, v]) => v.shift_over_mdc != null)
      .sort((a, b) => b[1].shift_over_mdc - a[1].shift_over_mdc).slice(0, 3);
    sections.push({ id: 'leverage', title: 'Reference influence (left out)', hue: null,
      rows: top.map(([dk, v]) => { const cc = M.columns.find(x => x.id === dk);
        return [cc ? cc.short : dk, `mean moves ${formatValue(Math.abs(v.mean_shift), cc || c)} ${cc ? cc.unit : ''} · ${v.shift_over_mdc.toFixed(2)} × MDC`]; }) });
  } else if (e.leverage) sections.push({ id: 'leverage', title: 'Decision leverage', hue: e.leverage.flips ? HUE.population : null, rows: [
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
    sections.push({ id: 'nearest', title: 'Nearest the reference-frame envelope', hue: null,
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
  if (e.kind === 'minimum_detectable_change') return `MDC (3 fields), +5 reference parents: ` + e.projected.map(p => {
    const c = M.columns.find(x => x.id === p.dimension); return c ? `${c.short} ±${formatValue(p.mdc95_now, c)} → ±${formatValue(p.mdc95_with_plus5, c)}` : null; }).filter(Boolean).join(' · ');
  return null;
}

const RESOLUTION = {
  acquisition: 'Acquisition vs material change',
  scale: 'Scale truncation',
  spatial_extent: 'Spatial extent',
  composition: 'Composition identity',
  population: 'Lot prevalence',
  spatial_sampling: 'Independent spatial sampling',
  validity: 'Measurement validity',
};

const targetName = A => A.targets.entities.join(', ');

function listLabel(M, A) {
  const target = targetName(A), dim = A.targets.dimensions[0] && M.columns.find(c => c.id === A.targets.dimensions[0]);
  if (A.verb === 'REPEAT') return `${target} · reference-frame acquisition settings`;
  if (A.verb === 'ZOOM') return `${target || 'Reference'} fines · higher magnification`;
  if (A.verb === 'EDS') return `${target} fines vs reference additive`;
  if (A.verb === 'EXTEND') return target ? `${target} mosaic · beyond captured edge` : `${dim ? dim.short : 'Reference'} · longer coherent capture`;
  if (A.verb === 'SECTIONS') return 'Independent lot cross-sections';
  if (A.verb === 'SPACE') return `${dim ? dim.short : target} · independent field spacing`;
  if (A.verb === 'BASELINE') return 'Reference frame · +5 independent parents';
  if (A.verb === 'REIMAGE') return `${target} · reference-frame BSE settings`;
  return A.title;
}

function whyText(M, A) {
  const target = targetName(A);
  const pivotal = A.targets.entities.some(id => M.ENT[id] && M.ENT[id].leverage && M.ENT[id].leverage.flips);
  if (A.addresses === 'acquisition') return `Tests whether the ${pivotal ? 'decision-driving ' : ''}deviation in ${target} is acquisition-driven.`;
  if (A.addresses === 'scale') return `Resolves the fines truncated by the current pixel size${target ? ` in ${target}` : ''}.`;
  if (A.addresses === 'composition') return `Tests whether ${target ? `${target} fines` : 'the fines'} match the selected-reference additive.`;
  if (A.addresses === 'spatial_extent') return `Bounds how far the observed deviation extends beyond the captured edge${target ? ` in ${target}` : ''}.`;
  if (A.addresses === 'spatial_sampling') return 'Spaces fields beyond the measured correlation range.';
  if (A.addresses === 'validity') return 'Restores measurements blocked by the current image quality.';
  if (A.addresses === 'population' && A.verb === 'SECTIONS') return 'Measures how widely the result extends across the lot.';
  if (A.addresses === 'population' && A.verb === 'BASELINE') return 'Narrows uncertainty in the selected reference-frame envelopes.';
  return A.rationale.split(/(?<=[.!?])\s/)[0];
}

function leverageText(M, A) {
  const pivotal = A.targets.entities.map(id => [id, M.ENT[id] && M.ENT[id].leverage]).filter(([, l]) => l && l.flips);
  if (!pivotal.length) return null;
  if (pivotal.length === 1) {
    const [id, l] = pivotal[0];
    if (l.cause === 'min_independent_count') return `DECISION-DRIVING — too few independent micrographs without ${id}.`;
    return `DECISION-DRIVING — verdict changes to ${l.verdict_without} without ${id}.`;
  }
  return `DECISION-DRIVING — verdict depends on ${pivotal.map(([id]) => id).join(', ')}.`;
}

// A presentation-only summary of the contract action. It does not rank, infer confidence, or change action semantics.
export function actionPresentation(M, i) {
  const A = M.actions[i];
  if (!A) return null;
  const resolution = A.addresses === 'population' && A.verb === 'BASELINE' ? 'Baseline uncertainty' : RESOLUTION[A.addresses] || A.addresses.replaceAll('_', ' ');
  return {
    action: A,
    listLabel: listLabel(M, A),
    why: whyText(M, A),
    resolves: resolution,
    grounding: A.status === 'future' ? 'PROSPECTIVE' : A.status.toUpperCase(),
    tier: `T${A.tier}`,
    cost: `${A.cost.toUpperCase()} COST`,
    leverage: leverageText(M, A),
  };
}

// Lower evidence layer for the selected next capture: trigger facts, full rationale and any computed effect.
export function explainAction(M, i) {
  const A = M.actions[i];
  return { id: 'action', title: 'Evidence / rationale', hue: A.reach.hue,
    rows: [...(effectText(M, A.effect) ? [['expected effect', effectText(M, A.effect)]] : [])],
    notes: [...A.evidence.map(t => ({ text: t, hue: A.reach.hue })), { text: `Rationale — ${A.rationale}` }] };
}

export function legendFor(M, stage, sel = {}) {
  const seen = new Map();
  M.keys.forEach(k => { const v = keyVisual(M, k, stage, sel); if (v.category !== 'settled' && v.category !== 'in_family') { const ci = categoryInfo(v); if (!seen.has(inFrame(M, ci.label))) seen.set(inFrame(M, ci.label), ci.hue); } });
  return [...seen.entries()].map(([label, hue]) => ({ label, hue }));
}
export { CATEGORY };
