// marker-frontier/1 helpers (presentation only). States, gates, counts and order are derived and checked in Python
// (qc/frontier.py); here they are mapped to words and rail segments. Nothing in this file decides a state.

export const GATE_WORD = { met: 'met', partial: 'partly supported', contested: 'contested', failed: 'failed', open: 'open' };
// short stage names for the card rail; the full names come from the document (frontier.rails)
const SHORT = {
  scientific_relevance: 'BASIS', measurability: 'TESTABLE NOW', robustness: 'ROBUSTNESS', blindspot_closure: 'INQUIRY VALUE',
  admission: 'PROMOTION', marker_demand: 'MARKER POOL', literature_convergence: 'LITERATURE', consequential_closure: 'INQUIRY VALUE',
  non_substitutability: 'NO SUBSTITUTE', integration_case: 'LAB FIT',
};
export const STATE_WORD = { BUILDING_CASE: 'BUILDING CASE', CRITICAL_MASS: 'CRITICAL MASS' };
export const stateWord = s => STATE_WORD[s] || s;
const TERMINAL = new Set(['REJECTED', 'CONFOUNDED']);
export const isTerminal = c => TERMINAL.has(c.status);
const TEST_WORD = { passed: 'passed on current data', failed: 'failed on current data', inconclusive: 'inconclusive on current data',
  requires_acquisition: 'needs a new acquisition (current modality)', not_run: 'not run yet', not_observable: 'not observable with current capture' };
export const testWord = s => TEST_WORD[s] || s;
export const representationWord = s => (s || 'other').replaceAll('_', ' ');
const TEST_SHORT = { passed: 'passed', failed: 'failed', inconclusive: 'inconclusive', requires_acquisition: 'needs acquisition',
  not_run: 'not run', not_observable: 'not observable' };
const plural = (n, w) => (n === 1 ? w : w + 's');
const MEAS_FAIL = 'BLOCKED';   // a failed measurability gate = current capture cannot observe it (routes to a capability)

// the rail: one categorical segment per gate, in the document's stage order. Never a fraction.
export function railSegments(frontier, kind, c) {
  const stages = frontier.rails[kind];
  return stages.map(({ gate, label }) => {
    const state = c.gates[gate].state;
    return { gate, label, short: SHORT[gate] || label, state,
             word: gate === 'measurability' && state === 'failed' ? MEAS_FAIL.toLowerCase() : GATE_WORD[state] };
  });
}
export const railSummary = segs => segs.map(s => `${s.label}: ${s.word}`).join('; ');

export function casesById(frontier) {
  const M = Object.fromEntries(frontier.markers.map(m => [m.id, m]));
  const C = Object.fromEntries(frontier.capabilities.map(c => [c.id, c]));
  return { M, C, P: Object.fromEntries(frontier.papers.map(p => [p.id, p])), R: Object.fromEntries(frontier.records.map(r => [r.id, r])),
           B: Object.fromEntries(frontier.blindspots.map(b => [b.key, b])) };
}

// lanes in the document's rule order; tested-and-set-aside markers are split off so the overview stays short
export function lanes(frontier) {
  const { M, C } = casesById(frontier);
  const markers = frontier.lanes.current_capture.map(id => M[id]);
  return { active: markers.filter(m => !isTerminal(m)), setAside: markers.filter(isTerminal), capabilities: frontier.lanes.new_capability.map(id => C[id]) };
}

// Opportunity hierarchy derived in qc/frontier.py. Fallback keeps older marker-frontier/1 documents renderable.
export function opportunityView(frontier) {
  const { M, C } = casesById(frontier), O = frontier.opportunity_map;
  if (!O) {
    const L = lanes(frontier);
    return { currentFrontier: L.active.slice(0, 3), computableNow: L.active, needsCapture: [], observabilityGaps: [],
             setAside: L.setAside, attractors: L.capabilities, roadmap: [], rankingPolicy: [] };
  }
  const take = ids => (ids || []).map(id => M[id]).filter(Boolean);
  return {
    currentFrontier: take(O.current_frontier),
    computableNow: take(O.candidate_markers.computable_now),
    needsCapture: take(O.candidate_markers.needs_targeted_capture),
    observabilityGaps: take(O.candidate_markers.requires_new_observability),
    setAside: take(O.candidate_markers.set_aside),
    attractors: (O.tooling_attractors || []).map(id => C[id]).filter(Boolean),
    roadmap: O.roadmap || [], rankingPolicy: O.ranking_policy || [], question: O.question, localLoop: O.local_loop,
  };
}

export function vorticesFor(frontier, c) {
  const V = Object.fromEntries((frontier.vortices || []).map(v => [v.id, v]));
  return (c.vortex_refs || []).map(id => V[id]).filter(Boolean);
}

// blindspot chips of a case: resolved first (consequential first), then general vocabulary gaps; `current` = this batch
export function blindspotChips(frontier, c, batch) {
  const { B } = casesById(frontier);
  const keys = c.closes || [];
  const res = keys.map(k => B[k]).filter(Boolean).map(b => ({ key: b.key, label: b.label, statement: b.statement, batch: b.batch,
    consequential: b.consequential, current: b.batch === batch, external: false, ref: { collection: b.collection, id: b.id }, actions: b.actions }));
  const seen = new Set();   // one chip per blindspot: a missing dimension and its rim are the same limit
  const chips = res.sort((a, b) => (b.consequential - a.consequential) || (b.current - a.current) || a.key.localeCompare(b.key))
    .filter(x => { const t = x.label.replace(' (not acquired)', ''); if (seen.has(t)) return false; seen.add(t); return true; });
  const gen = (c.general_gaps || []).map(g => ({ key: 'general:' + g.general, label: g.label, statement: 'general vocabulary gap (no loaded field instantiates it)',
    external: true, consequential: false, current: false }));
  return [...chips, ...gen];
}

// decision value line: only when the case closes a consequential blindspot (the engine's consequential flag)
export function decisionValue(frontier, c, batch) {
  const { B } = casesById(frontier);
  const cons = (c.closes_consequential || []).map(k => B[k]).filter(Boolean);
  if (!cons.length) return null;
  const acts = [...new Set(cons.flatMap(b => b.actions.map(a => a.verb)))];
  const batches = [...new Set(cons.map(b => b.batch))];
  return { current: batches.includes(batch), batches, actions: acts,
           text: `decision-consequential in ${batches.join(', ')}` + (acts.length ? ` · controller already acts: ${acts.join(', ')}` : '') };
}

export function markerCounts(m) {
  const k = m.counts;
  const out = [{ k: 'supporting', v: k.supporting }, { k: 'strong direct', v: k.strong_direct }, { k: 'contradictory', v: k.contradictory, warn: k.contradictory > 0 }];
  if (k.fixture_papers) out.push({ k: 'fixture', v: k.fixture_papers, fixture: true });
  out.push({ k: 'current data', v: TEST_SHORT[m.existing_data_test.status] || m.existing_data_test.status, text: true });
  return out;
}

export function capabilityCounts(c) {
  const k = c.counts;
  const out = [{ k: plural(k.marker_demands, 'marker demand'), v: k.marker_demands }, { k: 'strong direct', v: k.strong_direct },
               { k: 'contradictory', v: k.contradictory, warn: k.contradictory > 0 }];
  if (k.fixture_papers) out.push({ k: 'fixture', v: k.fixture_papers, fixture: true });
  out.push({ k: 'burden', v: k.integration_burden || 'unassessed', text: true });
  return out;
}

// papers bearing on one case: each with the assessments for this case only; supportive by strength, then contradictory,
// then neutral (contradictions are listed, never filtered out)
const RANK = { 'STRONG DIRECT': 4, 'STRONG TRANSFERABLE': 3, SUPPORTING: 2, INDIRECT: 1, WEAK: 0 };
const DIR = { SUPPORTIVE: 0, CONTRADICTORY: 1, NEUTRAL: 2 };
export function papersFor(frontier, id) {
  return frontier.papers.map(p => ({ ...p, rows: p.assessments.filter(a => a.target === id) })).filter(p => p.rows.length)
    .sort((a, b) => (DIR[a.rows[0].direction] - DIR[b.rows[0].direction]) || (RANK[b.rows[0].strength] - RANK[a.rows[0].strength])
      || (a.fixture - b.fixture) || a.id.localeCompare(b.id));
}

export function recordsFor(frontier, c) {
  const basis = new Set([...(c.existing_capability_substitutes || []).flatMap(s => s.basis || []),
                         ...(c.known_confounds || []).flatMap(x => x.basis || [])].filter(x => typeof x === 'string'));
  return frontier.records.map(r => ({ ...r, rows: r.assessments.filter(a => a.target === c.id), asBasis: basis.has(r.id) }))
    .filter(r => r.rows.length || r.asBasis);
}

export function basisLabel(frontier, x) {
  if (typeof x === 'string') {
    const { R, P } = casesById(frontier);
    const s = R[x] || P[x];
    return { text: s ? s.title : x, fixture: !!(s && s.fixture), ok: !!s };
  }
  return { text: `engine · ${x.batch} · ${x.collection}${x.id ? ' · ' + x.id : ''}${x.path ? ' › ' + x.path : ''}`, ok: true };
}

const DIM_WORD = { direct: 'direct', adjacent: 'adjacent', indirect: 'indirect', strong: 'strong', moderate: 'moderate', weak: 'weak',
                   high: 'high', partial: 'partial', low: 'low' };
export function assessmentDims(a) {
  return [['directness', DIM_WORD[a.directness]], ['method', DIM_WORD[a.method_strength]],
          ['transferability', DIM_WORD[a.transferability_class]], ['direction', a.direction.toLowerCase()]];
}
export const transferDetail = a => Object.entries(a.transferability || {}).map(([k, v]) => `${k} ${v}`).join(' · ');

// research state of the whole surface (what has and has not arrived)
export function researchState(frontier) {
  const c = frontier.context;
  const parts = [];
  if (!c.bundles.length) parts.push('no research bundle loaded');
  else parts.push(c.literature_present ? 'literature present' : 'no literature yet');
  if (!c.research_agent_present) parts.push('awaiting research agent (qte77)');
  if (c.fixture_present) parts.push('FIXTURE bundle present (does not advance any gate)');
  return parts;
}

// open consequential blindspots with no research case: the pull on the research agent, with what the controller does now
export function openPull(frontier, batch) {
  const { B } = casesById(frontier);
  return frontier.open_blindspots.map(k => B[k]).filter(Boolean)
    .sort((a, b) => ((b.batch === batch) - (a.batch === batch)) || a.key.localeCompare(b.key))
    .map(b => ({ ...b, current: b.batch === batch }));
}

// a blindspot is traceable into the Examiner Matrix only through a claim the decision brief already makes about it
export function briefClaimFor(brief, chip) {
  if (!brief || !chip.ref || chip.batch !== brief.source.batch) return null;
  return brief.claims.find(c => c.kind === 'limit' && (c.id === `limit.${chip.ref.id}` ||
    (c.focus && c.focus.collection === chip.ref.collection && c.focus.id === chip.ref.id))) || null;
}
