// decision-brief/1 helpers (presentation only). The brief is built and checked in Python (qc/brief.py); here a claim's
// proof references are resolved against the field and its focus reference becomes an examiner target. Navigation is
// driven by the reference (collection / id / path), never by which claim it is.

export const BLOCKS = [
  ['decision', 'DECISION'], ['data_support', 'DATA SUPPORT'], ['surviving_evidence', 'SURVIVING EVIDENCE'],
  ['limits', 'LIMITS'], ['acquisition_policy', 'ACQUISITION POLICY'],
];
export const BLOCK_LABEL = Object.fromEntries(BLOCKS);

export function resolveRef(F, r) {
  let node = F[r.collection];
  if (Array.isArray(node)) node = node.find(x => x.id === r.id);
  if (node === undefined) return undefined;
  for (const part of (r.path || '').split('.').filter(Boolean)) {
    if (node == null) return undefined;
    node = Array.isArray(node) ? node[Number(part)] : node[part];
  }
  return node;
}

// the key that best represents an entity in the matrix: its surviving evidence, else its strongest deviation, else its first key
export function primaryKey(M, entity) {
  const obs = M.F.observations.filter(o => o.entity === entity);
  const surv = obs.find(o => M.F.summary.surviving.includes(o.id));
  if (surv) return surv.id;
  const dev = obs.filter(o => M.F.summary.deviating.includes(o.id))
    .sort((a, b) => b.reference_relation.exceedance_ratio - a.reference_relation.exceedance_ratio)[0];
  return (dev || obs[0] || {}).id || null;
}

// focus reference -> {stage, key, action, spatial}: which examiner lens, which key to press, which action to open
export function navTarget(M, r) {
  const c = r.collection, id = r.id, path = r.path || '';
  if (c === 'observations') {
    const stage = path.startsWith('scrutiny') ? 1 : path.startsWith('variance_shares') ? 2 : path.startsWith('rims') ? 3 : 0;
    return { stage, key: id };
  }
  if (c === 'entities') return { stage: path.startsWith('leverage') || path.startsWith('acquisition') ? 1 : 3, key: primaryKey(M, id) };
  if (c === 'rims') {
    const rim = M.F.rims.find(x => x.id === id);
    if (!rim) return { stage: 3, key: null };
    const key = rim.scope === 'observation' ? rim.target
      : rim.scope === 'entity' ? (rim.type === 'composition' ? `${rim.target}:composition` : primaryKey(M, rim.target)) : null;
    return { stage: 3, key };
  }
  if (c === 'missing_dimensions') return { stage: 3, key: id };
  if (c === 'spatial_profiles') return { stage: 3, key: id, spatial: true };
  if (c === 'actions') {
    const i = M.actions.findIndex(a => a.id === id);
    return { stage: 4, action: i < 0 ? null : i, key: i < 0 ? null : (M.actions[i].targets.observations[0] || null) };
  }
  if (c === 'dimensions') return { stage: 2, key: null };
  return { stage: 0, key: null };                     // decision, summary, context: the lens overview
}

const short = v => (typeof v === 'number' ? (Number.isInteger(v) ? String(v) : v.toPrecision(3))
  : typeof v === 'boolean' ? (v ? 'yes' : 'no') : v == null ? '—' : String(v));
// one-line rendering of a referenced value for the proof list (raw, unformatted: this is the evidence itself)
export function describeRef(F, r) {
  const v = resolveRef(F, r);
  const where = [r.collection === 'decision' || r.collection === 'summary' || r.collection === 'context' ? r.collection : `${r.collection} · ${r.id}`,
                 r.path].filter(Boolean).join(' › ');
  let value;
  const prim = o => Object.entries(o).filter(([, x]) => x == null || typeof x !== 'object').slice(0, 3).map(([k, x]) => `${k} ${short(x)}`).join(' · ');
  if (Array.isArray(v)) value = v.length ? v.slice(0, 4).map(x => (x && typeof x === 'object' ? String(x.label || x.id || x.metric || prim(x) || '{…}') : short(x))).join(', ') + (v.length > 4 ? ` … (${v.length})` : '') : '(none)';
  else if (v && typeof v === 'object') value = Object.entries(v).filter(([, x]) => x == null || typeof x !== 'object').slice(0, 5).map(([k, x]) => `${k} ${short(x)}`).join(' · ');
  else value = short(v);
  return { where, value, ok: v !== undefined };
}
