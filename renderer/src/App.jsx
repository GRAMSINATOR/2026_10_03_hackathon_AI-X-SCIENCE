// Page order = information hierarchy: decision brief (what is known / not known / enough? / next) -> Examiner Control
// Matrix (the proof and challenge surface) -> registered spatial evidence -> raw statistical proof (on demand).
import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import Instrument from './scene/Instrument.jsx';
import Panel from './ui/Panel.jsx';
import Hero from './ui/Hero.jsx';
import SpatialEvidence from './ui/SpatialEvidence.jsx';
import MarkerFrontier from './ui/MarkerFrontier.jsx';   // recursive-research layer (marker-frontier/1); loads its own payload
import { buildModel, interpretation, STAGES, formatValue, SPATIAL_LAYER_DIMS, MASK_OF_DIMENSION } from './model/adapter.js';
import { navTarget } from './model/brief.js';
import { loadPayload } from './data.js';

export default function App() {
  const [payload, setPayload] = useState(null), [err, setErr] = useState(null);
  useEffect(() => { loadPayload().then(setPayload).catch(e => setErr(String(e))); }, []);
  if (err) return <div className="fatal">Could not load the evidence payload: {err}</div>;
  if (!payload) return <div className="fatal muted">Loading evidence…</div>;
  return <Main payload={payload} />;
}

function Main({ payload }) {
  const M = useMemo(() => buildModel(payload.field), [payload]);
  const brief = payload.brief || null;
  const strongest = useMemo(() => [...M.F.summary.deviating].sort((a, b) =>
    M.OBS[b].reference_relation.exceedance_ratio - M.OBS[a].reference_relation.exceedance_ratio)[0] || null, [M]);
  const [stage, setStage] = useState(0);
  const [selKey, setSelKey] = useState(strongest), [selAction, setSelAction] = useState(0);
  const [entity, setEntity] = useState((strongest || '').split(':')[0] || M.meta.pivotal[0] || M.rows[0].id);
  const [kpi, setKpi] = useState(strongest ? strongest.split(':')[1] : 'additive_density');
  const [overlays, setOverlays] = useState(() => {        // start with the overlay that belongs to the selected evidence
    const m = strongest && MASK_OF_DIMENSION[strongest.split(':')[1]];
    return { highz: m === 'mask_highz', pores: m === 'mask_pores' };
  });
  const [trace, setTrace] = useState(null);              // the brief claim currently being examined
  const examRef = useRef(null), spatialRef = useRef(null);
  const action = stage === 4 && M.actions.length ? selAction : null;
  useEffect(() => { if (action != null) { const e = M.actions[action].targets.entities[0]; if (e) setEntity(e); } }, [action, M]);
  const sel = useMemo(() => ({ key: selKey, action }), [selKey, action]);
  const selectKey = useCallback(id => {
    const k = M.keys.find(x => x.id === id); setSelKey(id); setEntity(k.entity);
    if (SPATIAL_LAYER_DIMS.includes(k.dimension)) setKpi(k.dimension);
    const mask = MASK_OF_DIMENSION[k.dimension];
    if (mask) setOverlays({ highz: mask === 'mask_highz', pores: mask === 'mask_pores' });
  }, [M]);
  const onSelectKey = useCallback(id => { setTrace(null); selectKey(id); }, [selectKey]);   // manual examination ends a trace
  const clear = useCallback(() => setSelKey(null), []);
  // SUMMARY -> CLAIM -> PROOF: the claim's focus reference decides lens, key and action; the claim itself travels along
  const onTrace = useCallback(claim => {
    const t = navTarget(M, claim.focus);
    setStage(t.stage);
    if (t.action != null) setSelAction(t.action);
    if (t.key && M.keys.some(x => x.id === t.key)) selectKey(t.key); else setSelKey(null);
    setTrace(claim);
    requestAnimationFrame(() => (t.spatial ? spatialRef : examRef).current?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  }, [M, selectKey]);
  useEffect(() => { window.__qa = { setStage, selectKey: onSelectKey, setSelAction, setEntity, setKpi, setOverlays, clear,
    trace: id => { const c = brief && brief.claims.find(x => x.id === id); if (c) onTrace(c); } }; }, [onSelectKey, clear, onTrace, brief]);
  const k = selKey && M.keys.find(x => x.id === selKey);
  return (
    <div className="app">
      <header className="bar">
        <div className="ident"><span className="brand">EVIDENCE INSTRUMENT</span><b>{M.meta.batch}</b><span className="muted">vs approved {M.meta.reference}</span></div>
        <span className="bar-note">decision brief · every statement traces to its proof below</span>
      </header>

      {brief && <Hero brief={brief} onTrace={onTrace} traced={trace && trace.id} />}

      <section className="examiner" ref={examRef} aria-label="Examiner Control Matrix">
        <div className="ex-head">
          <div><h2>EXAMINER CONTROL MATRIX</h2><span>proof and challenge surface · read the evidence through five lenses</span></div>
          <nav className="stages" aria-label="examiner lens">
            {STAGES.map((s, i) => <button key={s} className={i === stage ? 'on' : ''} onClick={() => setStage(i)} aria-pressed={i === stage}><span>{i + 1}</span>{s}</button>)}
          </nav>
        </div>
        <div className="main">
          <Instrument M={M} stage={stage} sel={sel} onSelectKey={onSelectKey} onClear={clear} />
          <Panel M={M} stage={stage} selKey={selKey} action={action} setAction={setSelAction} trace={trace} onClearTrace={() => setTrace(null)} />
        </div>
        <p className="interp" aria-live="polite">{interpretation(M, stage, { action })}</p>
      </section>

      <div ref={spatialRef}>
        <SpatialEvidence M={M} entity={entity} setEntity={setEntity} stage={stage} action={action} assets={payload.assets} imagery={payload.imagery !== false}
                         kpi={kpi} setKpi={setKpi} overlays={overlays} setOverlays={setOverlays} highlightKpi={k && k.entity === entity ? k.dimension : null} />
      </div>

      <details className="audit">
        <summary>Raw statistical proof</summary>
        <div className="auditbody">
          <section><h4>Engine decision record</h4><ul>{M.meta.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
            <p className="muted">severity p = {fmt(M.F.decision.tests.severity_p)} · count p = {fmt(M.F.decision.tests.count_p)} · {M.F.decision.tests.combination} ·
              P(any of {M.F.decision.n_independent} outside 99% | approved) = {fmt(M.F.decision.null_calibration.p_any_outside_99)}</p></section>
          <section><h4>Reference (approved micrographs)</h4><table><tbody>{M.columns.filter(c => c.acquired).map(c => { const r = M.DIM[c.id].reference; return (
            <tr key={c.id}><td>{c.short}</td><td>{formatValue(r.mean, c)} ± {formatValue(r.sd, c)} {c.unit} · n {r.n_micrographs} · MDC ±{formatValue(r.mdc95_3tiles, c)}</td></tr>); })}</tbody></table></section>
          <section><h4>All rims (incl. non-consequential)</h4><ul>{M.F.rims.map(r => <li key={r.id}>{r.type} · {r.target}{r.consequential ? ' · consequential' : ''} — {r.statement}</li>)}</ul></section>
          {brief && <section><h4>Brief governance (what the hero leaves out, and why)</h4><ul>{brief.governance.suppressed.map((s, i) =>
            <li key={i}>{s.candidate} — {s.reason}{s.into ? ` → ${s.into}` : ''}</li>)}</ul></section>}
        </div>
      </details>

      <MarkerFrontier field={M.F} brief={brief} onTrace={onTrace} />
    </div>
  );
}
const fmt = x => (x == null ? '—' : x.toFixed(3));
