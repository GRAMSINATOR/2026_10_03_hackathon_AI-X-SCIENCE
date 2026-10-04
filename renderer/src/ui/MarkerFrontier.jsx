// MARKER FRONTIER: the recursive-research layer under the current decision. Pure rendering of marker-frontier/1 (built
// and checked in qc/frontier.py): two lanes (track with current capture | requires new capability), a recessed evidence
// rail per case (one categorical segment per gate, never a probability) and an evidence tray where the depth lives.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import './frontier.css';
import {
  railSegments, lanes, blindspotChips, decisionValue, markerCounts, capabilityCounts, papersFor, recordsFor, basisLabel,
  assessmentDims, transferDetail, researchState, openPull, briefClaimFor, stateWord, testWord, casesById, GATE_WORD,
} from '../model/frontier.js';

// payload: a <script id="frontier-payload"> tag injected by qc.frontier.inject, or (dev) a fixture from ../fixtures
export async function loadFrontier() {
  const el = document.getElementById('frontier-payload');
  if (el) {
    try { const d = JSON.parse(el.textContent); if (d && d.schema_version === 'marker-frontier/1') return d; } catch { /* fall through */ }
  }
  if (import.meta.env && import.meta.env.DEV) {
    const name = new URLSearchParams(location.search).get('frontier') || 'marker_frontier.json';
    const r = await fetch('/' + name);
    if (r.ok) return r.json();
  }
  return null;
}

export default function MarkerFrontier({ frontier: given = null, field = null, brief = null, onTrace = null }) {
  const [doc, setDoc] = useState(given);
  useEffect(() => {
    if (given) { setDoc(given); return; }
    let live = true;
    loadFrontier().then(d => live && setDoc(d)).catch(() => live && setDoc(null));
    return () => { live = false; };
  }, [given]);
  if (!doc) return null;
  return <Frontier doc={doc} batch={field && field.context ? field.context.batch : null} brief={brief} onTrace={onTrace} />;
}

function Frontier({ doc, batch, brief, onTrace }) {
  const L = useMemo(() => lanes(doc), [doc]);
  const pull = useMemo(() => openPull(doc, batch), [doc, batch]);
  const [stack, setStack] = useState([]);            // tray navigation: [{kind, id}]; capability -> unlocked marker -> back
  const opener = useRef(null);
  const open = useCallback((kind, id, el) => { if (el) opener.current = el; setStack([{ kind, id }]); }, []);
  const push = useCallback((kind, id) => setStack(s => [...s, { kind, id }]), []);
  const close = useCallback(() => { setStack([]); requestAnimationFrame(() => opener.current && opener.current.focus()); }, []);
  const trace = useCallback(chip => {
    const c = briefClaimFor(brief, chip);
    if (c && onTrace) { setStack([]); onTrace(c); }
  }, [brief, onTrace]);
  useEffect(() => {                                   // QA hook (same convention as the instrument's window.__qa)
    window.__frontier = { open: (kind, id) => setStack([{ kind, id }]), close: () => setStack([]) };
  }, []);
  const top = stack[stack.length - 1];
  const ctx = { doc, batch, brief, trace, canTrace: chip => !!(onTrace && briefClaimFor(brief, chip)) };
  return (
    <section className="mf" aria-label="Marker Frontier">
      <header className="mf-head">
        <div className="mf-layer" aria-hidden="true"><span>CURRENT DECISION</span><i /><b>EXPANDING WHAT THE SYSTEM CAN KNOW</b></div>
        <div className="mf-title">
          <h2>MARKER FRONTIER</h2>
          <p>Which new markers the current blindspots pull in, and when converging evidence would justify a new measurement capability.</p>
        </div>
        <ul className="mf-research" aria-label="research state">{researchState(doc).map(t => <li key={t} className={t.startsWith('FIXTURE') ? 'fx' : ''}>{t}</li>)}</ul>
      </header>

      <div className="mf-lanes">
        <section className="mf-lane lane-m" aria-label="Track with current capture: marker admission">
          <div className="mf-lane-h"><span className="mf-ch">TRACK WITH CURRENT CAPTURE</span><em>marker admission</em></div>
          {L.active.map(m => <MarkerCard key={m.id} m={m} ctx={ctx} onOpen={el => open('marker', m.id, el)} />)}
          {!L.active.length && <p className="mf-empty">No active marker case. The open blindspots below are where a current-capture marker could help.</p>}
          {L.setAside.length > 0 && (
            <div className="mf-aside">
              <h4>TESTED AND SET ASIDE</h4>
              {L.setAside.map(m => <AsideRow key={m.id} m={m} ctx={ctx} onOpen={el => open('marker', m.id, el)} />)}
            </div>)}
        </section>
        <section className="mf-lane lane-c" aria-label="Requires new capability: capability expansion">
          <div className="mf-lane-h"><span className="mf-ch">REQUIRES NEW CAPABILITY</span><em>capability expansion</em></div>
          {L.capabilities.map(c => <CapabilityCard key={c.id} c={c} ctx={ctx} onOpen={el => open('capability', c.id, el)}
                                                   onMarker={(id, el) => open('marker', id, el)} />)}
          {!L.capabilities.length && <p className="mf-empty">No capability case. A marker that current capture cannot observe creates one.</p>}
        </section>
      </div>

      {pull.length > 0 && (
        <div className="mf-pull">
          <h4>OPEN BLINDSPOTS WITHOUT A RESEARCH CASE <span>the pull on the research agent; what the controller does meanwhile</span></h4>
          <ul>{pull.map(b => (
            <li key={b.key} className={b.current ? 'cur' : ''} title={b.statement}>
              <b>{b.label}</b>{!b.current && <em>{b.batch}</em>}
              {b.actions.length > 0 && <span>controller acts: {[...new Set(b.actions.map(a => a.verb))].join(' · ')}</span>}
            </li>))}</ul>
        </div>)}

      <Legend />
      {top && <Tray key={top.kind + top.id} top={top} depth={stack.length} ctx={ctx} onClose={close} onBack={() => setStack(s => s.slice(0, -1))} onPush={push} />}
    </section>
  );
}

// ---------------------------------------------------------------- primitives
function Rail({ segs, size = 'card' }) {
  return (
    <div className={`mf-rail r-${size}`} role="img" aria-label={segs.map(s => `${s.label}: ${s.word}`).join('; ')}>
      {segs.map((s, i) => <span key={s.gate} className={`mf-seg s-${s.state}`} style={{ '--i': i, zIndex: segs.length - i }} title={`${s.label}: ${s.word}`} />)}
    </div>
  );
}

function RailLabels({ segs }) {
  return <ol className="mf-rlab">{segs.map(s => <li key={s.gate} className={`s-${s.state}`}>{s.short}</li>)}</ol>;
}

function State({ s, kind }) {
  return <span className={`mf-state st-${s.toLowerCase()} k-${kind}`}>{stateWord(s)}</span>;
}

function Quals({ q }) {
  return q.length ? <span className="mf-quals">{q.map(x => <i key={x} className={x === 'FIXTURE' ? 'fx' : ''}>{x}</i>)}</span> : null;
}

function Chips({ chips, ctx }) {
  if (!chips.length) return <span className="mf-none">none</span>;
  return (
    <span className="mf-chips">
      {chips.map(ch => {
        const can = ctx.canTrace(ch);
        const cls = `mf-bs ${ch.consequential ? 'cons' : ''} ${ch.current ? 'cur' : ''} ${ch.external ? 'gen' : ''}`;
        const body = <>{ch.label}{!ch.external && !ch.current && ch.batch && <em>{ch.batch}</em>}{ch.external && <em>general</em>}</>;
        return can
          ? <button key={ch.key} className={cls + ' go'} title={`${ch.statement || ch.label} · open in the Examiner Matrix`}
                    onClick={e => { e.stopPropagation(); ctx.trace(ch); }}>{body}</button>
          : <span key={ch.key} className={cls} title={ch.statement || ch.label}>{body}</span>;
      })}
    </span>
  );
}

function Counts({ items }) {
  return (
    <ul className="mf-counts">
      {items.map(x => x.text
        ? <li key={x.k} className="tx">{x.k}:<b>{x.v}</b></li>
        : <li key={x.k} className={`${x.warn ? 'warn' : ''} ${x.fixture ? 'fx' : ''}`}><b>{x.v}</b>{x.k}</li>)}
    </ul>
  );
}

function Legend() {
  return (
    <div className="mf-legend" aria-label="rail legend">
      <span><i className="mf-key s-met" />met</span><span><i className="mf-key s-partial" />partly supported</span>
      <span><i className="mf-key s-contested" />contested</span><span><i className="mf-key s-failed" />failed / blocked</span>
      <span><i className="mf-key s-open" />open</span>
      <em>A rail shows which gates have evidence, not a probability. Fixture evidence never fills a segment.</em>
    </div>
  );
}

// ---------------------------------------------------------------- cards
function MarkerCard({ m, ctx, onOpen }) {
  const segs = railSegments(ctx.doc, 'marker', m);
  const dv = decisionValue(ctx.doc, m, ctx.batch);
  const chips = blindspotChips(ctx.doc, m, ctx.batch);
  return (
    <article className={`mf-card ${dv && dv.current ? 'current' : ''} ${m.fixture ? 'is-fx' : ''}`}>
      <div className="mf-card-h"><h3>{m.name}</h3><State s={m.status} kind="m" /></div>
      <Quals q={m.qualifiers} />
      <p className="mf-prop">{m.proposition}</p>
      <dl className="mf-dl">
        <dt>CLOSES</dt><dd><Chips chips={chips} ctx={ctx} /></dd>
        {dv && <><dt>DECISION VALUE</dt><dd className="mf-dv">{dv.text}</dd></>}
      </dl>
      <Rail segs={segs} /><RailLabels segs={segs} />
      <div className="mf-foot"><Counts items={markerCounts(m)} />
        <button className="mf-open" onClick={e => onOpen(e.currentTarget)}>OPEN EVIDENCE <span aria-hidden="true">→</span></button></div>
    </article>
  );
}

function AsideRow({ m, ctx, onOpen }) {
  const segs = railSegments(ctx.doc, 'marker', m);
  return (
    <div className="mf-row">
      <State s={m.status} kind="m" />
      <div className="mf-row-t"><b>{m.name}</b><span>{m.status_basis}</span></div>
      <Rail segs={segs} size="mini" />
      <button className="mf-open sm" onClick={e => onOpen(e.currentTarget)} aria-label={`open evidence: ${m.name}`}>EVIDENCE <span aria-hidden="true">→</span></button>
    </div>
  );
}

function CapabilityCard({ c, ctx, onOpen, onMarker }) {
  const { M } = casesById(ctx.doc);
  const segs = railSegments(ctx.doc, 'capability', c);
  const chips = blindspotChips(ctx.doc, c, ctx.batch);
  const dv = decisionValue(ctx.doc, c, ctx.batch);
  const nCons = new Set(chips.filter(x => x.consequential).map(x => x.label)).size;
  const nRes = chips.filter(x => !x.external).length, nGen = chips.length - nRes;
  return (
    <article className={`mf-card cap ${dv && dv.current ? 'current' : ''} ${c.fixture ? 'is-fx' : ''}`}>
      <div className="mf-card-h"><h3>{c.name}</h3><State s={c.status} kind="c" /></div>
      <Quals q={c.qualifiers} />
      <dl className="mf-dl">
        <dt>UNLOCKS</dt>
        <dd><span className="mf-big">{c.markers_unlocked.length}</span> marker{c.markers_unlocked.length === 1 ? '' : 's'}
          <span className="mf-chips">{c.markers_unlocked.map(id => (
            <button key={id} className={`mf-mk ${M[id].fixture ? 'fx' : ''}`} onClick={e => { e.stopPropagation(); onMarker(id, e.currentTarget); }}>
              {M[id].name}{M[id].fixture && <em>fixture</em>}</button>))}</span></dd>
        <dt>CLOSES</dt>
        <dd><span className="mf-big">{nRes}</span> blindspot{nRes === 1 ? '' : 's'}{nCons > 0 && <> · <b className="mf-consn">{nCons} consequential</b></>}
          {nGen > 0 && <span className="mf-muted-i"> · {nGen} vocabulary gap{nGen === 1 ? '' : 's'}</span>}
          <Chips chips={chips} ctx={ctx} /></dd>
      </dl>
      {c.why_current_workflow_cannot_resolve && <p className="mf-prop why"><b>Why current capture cannot substitute.</b> {c.why_current_workflow_cannot_resolve}</p>}
      <Rail segs={segs} /><RailLabels segs={segs} />
      <div className="mf-foot"><Counts items={capabilityCounts(c)} />
        <button className="mf-open" onClick={e => onOpen(e.currentTarget)}>OPEN CAPABILITY CASE <span aria-hidden="true">→</span></button></div>
    </article>
  );
}

// ---------------------------------------------------------------- evidence tray
function Tray({ top, depth, ctx, onClose, onBack, onPush }) {
  const { M, C } = casesById(ctx.doc);
  const c = top.kind === 'marker' ? M[top.id] : C[top.id];
  const ref = useRef(null);
  useEffect(() => {
    const k = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', k);
    ref.current && ref.current.focus();
    return () => window.removeEventListener('keydown', k);
  }, [onClose]);
  if (!c) return null;
  const kind = top.kind === 'marker' ? 'marker' : 'capability';
  const segs = railSegments(ctx.doc, kind, c);
  const papers = papersFor(ctx.doc, c.id);
  const records = recordsFor(ctx.doc, c);
  return (
    <div className="mf-tray-wrap">
      <div className="mf-scrim" onClick={onClose} aria-hidden="true" />
      <aside ref={ref} tabIndex={-1} className="mf-tray" role="dialog" aria-modal="true" aria-label={`${kind} case: ${c.name}`}>
        <header className="mf-tray-h">
          <div className="mf-tray-nav">
            {depth > 1 && <button className="mf-back" onClick={onBack}>← back</button>}
            <span className="mf-eyebrow">{kind === 'marker' ? 'MARKER CASE' : 'CAPABILITY CASE'} · {c.id}</span>
            <button className="mf-x" onClick={onClose} aria-label="close evidence tray">×</button>
          </div>
          <div className="mf-card-h"><h3>{c.name}</h3><State s={c.status} kind={kind[0]} /></div>
          <Quals q={c.qualifiers} />
          <p className="mf-basis">{c.status_basis}</p>
        </header>
        <div className="mf-tray-b">
          <TraySection title="SUMMARY">
            {kind === 'marker' ? <MarkerSummary m={c} ctx={ctx} /> : <CapabilitySummary c={c} ctx={ctx} onPush={onPush} />}
          </TraySection>

          <TraySection title="EVIDENCE STATE">
            <Rail segs={segs} size="tray" /><RailLabels segs={segs} />
            <table className="mf-gates"><tbody>
              {[...segs.map(s => s.gate), ...(kind === 'marker' ? ['non_redundancy'] : [])].map(g => {
                const G = c.gates[g], nx = c.next.find(n => n.gate === g);
                const label = (ctx.doc.rails[kind].find(r => r.gate === g) || {}).label || 'NON-REDUNDANCY';
                return (
                  <tr key={g} className={`s-${G.state}`}>
                    <td><i className={`mf-key s-${G.state}`} />{label}</td>
                    <td><b>{GATE_WORD[G.state]}</b>
                      {G.basis.length > 0 && <div className="mf-gb">basis: {G.basis.join(', ')}</div>}
                      {G.excluded_fixture.length > 0 && <div className="mf-gb fx">fixture, not counted: {G.excluded_fixture.join(', ')}</div>}
                      {nx && <div className="mf-gn">to advance: {nx.text}</div>}</td>
                  </tr>);
              })}
            </tbody></table>
          </TraySection>

          <TraySection title={`PAPERS (${papers.length})`}>
            {!papers.length && <p className="mf-empty">No literature attached yet. Papers appear here automatically when a research bundle assesses <code>{c.id}</code> (docs/MARKER_FRONTIER.md).</p>}
            {papers.map(p => <Paper key={p.id} p={p} />)}
          </TraySection>

          <TraySection title={`PROJECT RECORDS AND ENGINE FACTS (${records.length})`}>
            {!records.length && <p className="mf-empty">None.</p>}
            {records.map(r => (
              <div key={r.id} className={`mf-rec ${r.fixture ? 'is-fx' : ''}`}>
                <div className="mf-rec-h"><span className="mf-tag">{r.kind.replace('_', ' ')}</span><b>{r.title}</b></div>
                {r.rows.map((a, i) => <p key={i}><span className={`mf-out o-${a.outcome}`}>{a.gate.replace('_', ' ')} · {a.outcome}</span> {a.claim}</p>)}
                {!r.rows.length && r.asBasis && <p className="mf-muted">cited as basis in this case</p>}
                <p className="mf-src">{r.source ? `${r.source.path} · ${r.source.locator || ''}` : r.field_ref ? `epistemic-field/1 · ${r.field_ref.batch} · ${r.field_ref.collection} · ${r.field_ref.id}${r.field_ref.path ? ' › ' + r.field_ref.path : ''}` : ''}
                  {r.preview && <span> = {r.preview}</span>}</p>
              </div>))}
          </TraySection>

          <TraySection title="PROVENANCE">
            <table className="mf-kv"><tbody>
              <tr><td>bundle</td><td>{c.bundle}{c.extended_by.length ? ` (extended by ${c.extended_by.join(', ')})` : ''}{c.fixture && <span className="mf-tag fx">FIXTURE</span>}</td></tr>
              <tr><td>origin</td><td>{c.provenance.kind || '—'}{c.provenance.basis ? ` · ${c.provenance.basis}` : ''}</td></tr>
              <tr><td>review</td><td>{c.review ? `${c.review.decision} · ${c.review.by} · ${c.review.date}${c.review.note ? ' · ' + c.review.note : ''}` : 'none recorded'}</td></tr>
            </tbody></table>
          </TraySection>
        </div>
      </aside>
    </div>
  );
}

function TraySection({ title, children }) {
  return <section className="mf-ts"><h4>{title}</h4>{children}</section>;
}

function MarkerSummary({ m, ctx }) {
  const chips = blindspotChips(ctx.doc, m, ctx.batch);
  const t = m.existing_data_test;
  const cc = m.current_capture_compatible === true ? 'yes' : m.current_capture_compatible === false ? 'no' : 'unknown';
  return (
    <>
      <p className="mf-lead">{m.proposition}</p>
      <table className="mf-kv"><tbody>
        <tr><td>closes</td><td><Chips chips={chips} ctx={ctx} />{chips.filter(x => x.statement).map(x => <p key={x.key} className="mf-muted">{x.label}: {x.statement}</p>)}</td></tr>
        {m.decision_refs.length > 0 && <tr><td>decisions affected</td><td>{m.decision_refs.map((d, i) => <div key={i}>{d.batch} · {d.collection}{d.id ? ' · ' + d.id : ''}{d.path ? ' › ' + d.path : ''}{!d.resolved && <b className="bad"> unresolved</b>}</div>)}
          {decisionValue(ctx.doc, m, ctx.batch) && <p className="mf-muted">{decisionValue(ctx.doc, m, ctx.batch).text}</p>}</td></tr>}
        <tr><td>why relevant</td><td>{m.why_relevant || '—'}</td></tr>
        <tr><td>scientific definition</td><td>{m.scientific_definition || '—'}</td></tr>
        <tr><td>measurement definition</td><td>{m.measurement_definition || '—'}</td></tr>
        <tr><td>current capture</td><td>compatible: <b>{cc}</b> · test: {testWord(t.status)}{t.note ? ` · ${t.note}` : ''}
          {m.capture_requirements && <p className="mf-muted">{m.capture_requirements}</p>}
          {t.requires_actions.length > 0 && <p className="mf-muted">controller action: {t.requires_actions.map(a => `${a.verb} (${a.batch}, tier ${a.tier})`).join(' · ')}</p>}
          {m.required_capabilities.length > 0 && <p className="mf-muted">requires capability: {m.required_capabilities.join(', ')}</p>}</td></tr>
        <tr><td>known confounds</td><td>{m.known_confounds.length ? m.known_confounds.map(x => (
          <div key={x.id}>{x.label} · <b>{x.controlled === true ? 'controlled' : x.controlled === false ? 'not controlled' : 'unassessed'}</b>
            {(x.basis || []).length > 0 && <span className="mf-muted"> ({x.basis.map(b => basisLabel(ctx.doc, b).text).join('; ')})</span>}</div>)) : '—'}</td></tr>
        {m.known_failure_modes.length > 0 && <tr><td>failure modes</td><td>{m.known_failure_modes.join(' · ')}</td></tr>}
        {m.redundant_with.length > 0 && <tr><td>overlaps</td><td>{m.redundant_with.map((r, i) => <div key={i}>{typeof r.ref === 'string' ? r.ref : r.ref.id}{r.increment ? ` · adds: ${r.increment}` : ''}</div>)}</td></tr>}
      </tbody></table>
    </>
  );
}

function CapabilitySummary({ c, ctx, onPush }) {
  const { M } = casesById(ctx.doc);
  const chips = blindspotChips(ctx.doc, c, ctx.batch);
  const I = c.integration || {};
  return (
    <>
      <p className="mf-lead">{c.why_current_workflow_cannot_resolve || '—'}</p>
      <table className="mf-kv"><tbody>
        <tr><td>unlocks</td><td>{c.markers_unlocked.map(id => (
          <button key={id} className={`mf-mk ${M[id].fixture ? 'fx' : ''}`} onClick={() => onPush('marker', id)}>{M[id].name} · {stateWord(M[id].status)}{M[id].fixture && <em>fixture</em>}</button>))}
          <p className="mf-muted">{c.marker_demands.length} counted demand{c.marker_demands.length === 1 ? '' : 's'} · {c.credible_demands.length} credible (scientific relevance met)</p></td></tr>
        <tr><td>closes</td><td><Chips chips={chips} ctx={ctx} />{chips.filter(x => x.statement).map(x => <p key={x.key} className="mf-muted">{x.label}: {x.statement}</p>)}</td></tr>
        <tr><td>decisions affected</td><td>{c.decisions_affected.length ? c.decisions_affected.map(d => `${d.action} (${d.batch})`).join(' · ') : '—'}</td></tr>
        <tr><td>substitutes</td><td>{(c.existing_capability_substitutes || []).length ? c.existing_capability_substitutes.map(s => (
          <div key={s.id} className="mf-sub"><b>{s.label}</b> · <span className={`mf-out o-${s.ruled_out === true ? 'passed' : s.ruled_out === false ? 'failed' : 'inconclusive'}`}>
            {s.ruled_out === true ? 'ruled out' : s.ruled_out === false ? 'adequate substitute' : 'not assessed'}</span>
            {(s.basis || []).length > 0 && <div className="mf-muted">basis: {s.basis.map(b => basisLabel(ctx.doc, b).text).join('; ')}</div>}
            {s.note && <div className="mf-muted">{s.note}</div>}</div>)) : 'none listed'}</td></tr>
        <tr><td>integration</td><td>{c.integration ? <>
          burden <b>{I.burden || '—'}</b> · acquisition cost <b>{I.acquisition_cost_class || '—'}</b> · accepted <b>{I.acceptable === true ? 'yes' : I.acceptable === false ? 'no' : 'not decided'}</b>
          {I.workflow_effect && <p className="mf-muted">{I.workflow_effect}</p>}
          {(I.requirements || []).length > 0 && <p className="mf-muted">requires: {I.requirements.join(' · ')}</p>}
          {(I.data_interface_requirements || []).length > 0 && <p className="mf-muted">data interface: {I.data_interface_requirements.join(' · ')}</p>}</> : 'not assessed'}</td></tr>
      </tbody></table>
    </>
  );
}

function Paper({ p }) {
  return (
    <div className={`mf-paper ${p.fixture ? 'is-fx' : ''}`}>
      <div className="mf-paper-h">
        {p.url ? <a href={p.url} target="_blank" rel="noopener noreferrer">{p.title}</a> : <span className="mf-ptitle">{p.title}</span>}
        {p.fixture && <span className="mf-tag fx">FIXTURE · not counted</span>}
      </div>
      <p className="mf-pmeta">{[p.venue, p.year, (p.authors || []).slice(0, 3).join(', ') + ((p.authors || []).length > 3 ? ' et al.' : '')].filter(Boolean).join(' · ')}
        {p.doi && <> · <a href={`https://doi.org/${p.doi}`} target="_blank" rel="noopener noreferrer">doi:{p.doi}</a></>}
        {!p.url && !p.fixture && <b className="bad"> no canonical link</b>}</p>
      {p.rows.map((a, i) => (
        <div key={i} className="mf-assess">
          <span className={`mf-label l-${a.label.replace(/\s+/g, '-').toLowerCase()}`}>{a.label}</span>
          <span className="mf-gate">{a.gate.replace(/_/g, ' ')}</span>
          <ul className="mf-dims">{assessmentDims(a).map(([k, v]) => <li key={k}><span>{k}</span>{v}</li>)}</ul>
          <p className="mf-claim">{a.claim}</p>
          {a.note && <p className="mf-why">Why this matters: {a.note}</p>}
          <p className="mf-muted">transferability · {transferDetail(a)} · independence group {p.independence_group}</p>
        </div>))}
    </div>
  );
}

