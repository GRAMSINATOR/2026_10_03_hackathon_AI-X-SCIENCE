// AGENTIC MARKER FRONTIER: the global opportunity layer around the local decision loop. Pure rendering of
// marker-frontier/1 (built and checked in qc/frontier.py): ranked marker protocols, observability-attractor payloads,
// categorical evidence rails (never probabilities), a roadmap and evidence trays where the depth lives.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import './frontier.css';
import {
  railSegments, opportunityView, vorticesFor, blindspotChips, decisionValue, markerCounts, capabilityCounts, papersFor, recordsFor, basisLabel,
  assessmentDims, transferDetail, researchState, openPull, briefClaimFor, stateWord, testWord, representationWord, casesById, GATE_WORD,
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
  const O = useMemo(() => opportunityView(doc), [doc]);
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
    <section className="mf" aria-label="Agentic Marker Frontier">
      <header className="mf-head">
        <div className="mf-layer" aria-hidden="true"><span>LOCAL EXAMINER LOOP</span><i /><b>GLOBAL OPPORTUNITY MAP</b></div>
        <div className="mf-title">
          <h2>AGENTIC MARKER FRONTIER</h2>
          <p>New protocols for perceiving the current dataset, plus the observability gaps that could justify future measurement capability.</p>
        </div>
        <ul className="mf-research" aria-label="research state">{researchState(doc).map(t => <li key={t} className={t.startsWith('FIXTURE') ? 'fx' : ''}>{t}</li>)}</ul>
      </header>

      <div className="mf-distinction">
        <div><b>NEXT CAPTURE</b><span>Local decision optimization</span><p>What should the lab do next to resolve the current decision?</p></div>
        <i aria-hidden="true" />
        <div className="active"><b>MARKER FRONTIER</b><span>Representation search</span><p>What useful new ways of perceiving this dataset should be investigated?</p></div>
        <i aria-hidden="true" />
        <div><b>OBSERVABILITY EXPANSION</b><span>Capability roadmap</span><p>What missing information would unlock valuable marker families?</p></div>
      </div>

      <section className="mf-frontier" aria-label="Current Frontier">
        <div className="mf-section-h"><span>A</span><div><h3>CURRENT FRONTIER</h3><p>Highest-priority research opportunities under the inspectable attention rules below.</p></div></div>
        <div className="mf-frontier-list">
          {O.currentFrontier.map(m => <FrontierRow key={m.id} m={m} ctx={ctx} onOpen={el => open('marker', m.id, el)} />)}
          {!O.currentFrontier.length && <p className="mf-empty">No grounded marker opportunity yet. Structured inquiry vortices will appear here when evidence supports them.</p>}
        </div>
        {O.rankingPolicy.length > 0 && <p className="mf-rank-policy"><b>ATTENTION ORDER</b> {O.rankingPolicy.join(' → ')}</p>}
      </section>

      <section className="mf-candidates" aria-label="Candidate Markers">
        <div className="mf-section-h"><span>B</span><div><h3>CANDIDATE MARKERS</h3><p>Defined observation protocols, separated by what the loaded data can support.</p></div></div>
        <div className="mf-candidate-lanes">
          <MarkerGroup title="COMPUTABLE / TESTABLE NOW" note="use the data already loaded" markers={O.computableNow} ctx={ctx} onOpen={open} />
          <MarkerGroup title="NEEDS TARGETED CAPTURE" note="same modality, new scale or sampling" markers={O.needsCapture} ctx={ctx} onOpen={open} />
        </div>
        {O.setAside.length > 0 && (
          <div className="mf-aside">
            <h4>TESTED AND DEPRIORITIZED <span>negative results remain visible</span></h4>
            {O.setAside.map(m => <AsideRow key={m.id} m={m} ctx={ctx} onOpen={el => open('marker', m.id, el)} />)}
          </div>)}
      </section>

      <section className="mf-observe" aria-label="Observability Expansion">
        <div className="mf-section-h"><span>C</span><div><h3>OBSERVABILITY EXPANSION</h3><p>Marker pools that require information the current workflow does not capture. These are scoped payload arguments, not equipment recommendations.</p></div></div>
        <div className="mf-attractors">{O.attractors.map(c => <CapabilityCard key={c.id} c={c} ctx={ctx} onOpen={el => open('capability', c.id, el)}
                                               onMarker={(id, el) => open('marker', id, el)} />)}</div>
        {!O.attractors.length && <p className="mf-empty">No observability attractor yet. New capability cases appear only when inaccessible marker opportunities name a shared requirement.</p>}
      </section>

      {pull.length > 0 && (
        <div className="mf-pull">
          <h4>UNMAPPED INQUIRY VORTICES <span>structured limits without a live marker opportunity; current controller action remains visible</span></h4>
          <ul>{pull.map(b => (
            <li key={b.key} className={b.current ? 'cur' : ''} title={b.statement}>
              <b>{b.label}</b>{!b.current && <em>{b.batch}</em>}
              {b.actions.length > 0 && <span>controller acts: {[...new Set(b.actions.map(a => a.verb))].join(' · ')}</span>}
            </li>))}</ul>
        </div>)}

      {O.roadmap.length > 0 && <Roadmap steps={O.roadmap} />}

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

function State({ s, kind, label = null }) {
  const cls = String(s).toLowerCase().replaceAll('_', '-').replaceAll(' ', '-');
  return <span className={`mf-state st-${cls} k-${kind}`}>{label || stateWord(s)}</span>;
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

function OpportunityMeta({ m }) {
  return (
    <span className="mf-ometa">
      <i>{m.observability ? m.observability.label : 'CAPTURE STATUS OPEN'}</i>
      <i>{(m.marker_kind || 'marker').toUpperCase()}</i>
      <i>{representationWord(m.representation).toUpperCase()}</i>
      {m.implementation_burden && <i>{m.implementation_burden.toUpperCase()} BURDEN</i>}
    </span>
  );
}

function VortexTags({ c, ctx }) {
  const rows = vorticesFor(ctx.doc, c);
  const kinds = [...new Set(rows.map(v => representationWord(v.kind)))];
  if (!kinds.length) return null;
  return <span className="mf-vortices">{kinds.slice(0, 3).map(kind => <i key={kind}>{kind}</i>)}</span>;
}

function FrontierRow({ m, ctx, onOpen }) {
  return (
    <article className="mf-frontier-row">
      <span className="mf-rank" aria-label={`attention rank ${m.opportunity_rank}`}>{String(m.opportunity_rank).padStart(2, '0')}</span>
      <div className="mf-frontier-main">
        <div className="mf-card-h"><h3>{m.name}</h3><State s={m.status} kind="m" label={m.investigation_state} /></div>
        <p className="mf-observable"><b>PERCEIVES</b> {m.observable}</p>
        <p className="mf-frontier-why">{m.why_relevant}</p>
        <OpportunityMeta m={m} /><VortexTags c={m} ctx={ctx} />
      </div>
      <button className="mf-open" onClick={e => onOpen(e.currentTarget)}>INSPECT BASIS <span aria-hidden="true">→</span></button>
    </article>
  );
}

function MarkerGroup({ title, note, markers, ctx, onOpen }) {
  return (
    <section className="mf-marker-group">
      <header><h4>{title}</h4><span>{note}</span></header>
      <div className="mf-mods">{markers.map(m => <MarkerCard key={m.id} m={m} ctx={ctx} onOpen={el => onOpen('marker', m.id, el)} />)}</div>
      {!markers.length && <p className="mf-empty">No supported opportunity in this class.</p>}
    </section>
  );
}

function Roadmap({ steps }) {
  return (
    <section className="mf-roadmap" aria-label="Acquisition opportunity roadmap">
      <h4>OPPORTUNITY ROADMAP <span>derived from the current opportunity topology</span></h4>
      <ol>{steps.map((s, i) => {
        const n = (s.marker_refs || s.capability_refs || []).length;
        return <li key={s.id}><b>{String(i + 1).padStart(2, '0')} · {s.label}</b><p>{s.purpose}</p>{n > 0 && <span>{n} linked opportunit{n === 1 ? 'y' : 'ies'}</span>}</li>;
      })}</ol>
    </section>
  );
}

// ---------------------------------------------------------------- cards
function MarkerCard({ m, ctx, onOpen }) {
  const segs = railSegments(ctx.doc, 'marker', m);
  const dv = decisionValue(ctx.doc, m, ctx.batch);
  const chips = blindspotChips(ctx.doc, m, ctx.batch);
  return (
    <article className={`mf-card ${dv && dv.current ? 'current' : ''} ${m.fixture ? 'is-fx' : ''}`}>
      <div className="mf-card-h"><h3>{m.name}</h3><State s={m.status} kind="m" label={m.investigation_state} /></div>
      <p className="mf-observable"><b>PERCEIVES</b> {m.observable || m.proposition}</p>
      <p className="mf-prop why"><b>Why it may matter.</b> {m.why_relevant}</p>
      <OpportunityMeta m={m} />
      <dl className="mf-dl">
        <dt>INQUIRY</dt><dd><Chips chips={chips} ctx={ctx} /></dd>
        {dv && <><dt>LEVERAGE</dt><dd className="mf-dv">{dv.text}</dd></>}
      </dl>
      <Rail segs={segs} /><RailLabels segs={segs} />
      <div className="mf-foot"><Counts items={markerCounts(m)} />
        <button className="mf-open" onClick={e => onOpen(e.currentTarget)}>INSPECT BASIS <span aria-hidden="true">→</span></button></div>
    </article>
  );
}

function AsideRow({ m, ctx, onOpen }) {
  const segs = railSegments(ctx.doc, 'marker', m);
  return (
    <div className="mf-row">
      <State s={m.status} kind="m" label={m.investigation_state} />
      <div className="mf-row-t"><b>{m.name}</b><span>{m.status_basis}</span></div>
      <Rail segs={segs} size="mini" />
      <button className="mf-open sm" onClick={e => onOpen(e.currentTarget)} aria-label={`inspect basis: ${m.name}`}>BASIS <span aria-hidden="true">→</span></button>
    </div>
  );
}

function CapabilityCard({ c, ctx, onOpen, onMarker }) {
  const { M } = casesById(ctx.doc);
  const pool = c.marker_pool || c.markers_unlocked || [];
  const segs = railSegments(ctx.doc, 'capability', c);
  const chips = blindspotChips(ctx.doc, c, ctx.batch);
  const dv = decisionValue(ctx.doc, c, ctx.batch);
  const nCons = new Set(chips.filter(x => x.consequential).map(x => x.label)).size;
  const nRes = chips.filter(x => !x.external).length, nGen = chips.length - nRes;
  return (
    <article className={`mf-card cap ${dv && dv.current ? 'current' : ''} ${c.fixture ? 'is-fx' : ''}`}>
      <div className="mf-card-h"><h3>{c.name}</h3><State s={c.status} kind="c" label={c.attractor_state} /></div>
      <p className="mf-attractor-scope">This capability would unlock a defined marker pool; it is not a procurement recommendation.</p>
      <dl className="mf-dl">
        <dt>UNLOCKS</dt>
        <dd><span className="mf-big">{pool.length}</span> marker opportunit{pool.length === 1 ? 'y' : 'ies'}
          <span className="mf-chips">{pool.map(id => (
            <button key={id} className={`mf-mk ${M[id].fixture ? 'fx' : ''}`} onClick={e => { e.stopPropagation(); onMarker(id, e.currentTarget); }}>
              {M[id].name}{M[id].fixture && <em>fixture</em>}</button>))}</span></dd>
        <dt>ADDRESSES</dt>
        <dd><span className="mf-big">{nRes}</span> observed limit{nRes === 1 ? '' : 's'}{nCons > 0 && <> · <b className="mf-consn">{nCons} decision-consequential</b></>}
          {nGen > 0 && <span className="mf-muted-i"> · {nGen} vocabulary gap{nGen === 1 ? '' : 's'}</span>}
          <Chips chips={chips} ctx={ctx} /></dd>
      </dl>
      {c.why_current_workflow_cannot_resolve && <p className="mf-prop why"><b>Why current data is insufficient.</b> {c.why_current_workflow_cannot_resolve}</p>}
      <Rail segs={segs} /><RailLabels segs={segs} />
      <div className="mf-foot"><Counts items={capabilityCounts(c)} />
        <button className="mf-open" onClick={e => onOpen(e.currentTarget)}>INSPECT PAYLOAD <span aria-hidden="true">→</span></button></div>
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
      <aside ref={ref} tabIndex={-1} className="mf-tray" role="dialog" aria-modal="true" aria-label={`${kind === 'marker' ? 'marker opportunity' : 'observability attractor'}: ${c.name}`}>
        <header className="mf-tray-h">
          <div className="mf-tray-nav">
            {depth > 1 && <button className="mf-back" onClick={onBack}>← back</button>}
            <span className="mf-eyebrow">{kind === 'marker' ? 'MARKER OPPORTUNITY' : 'OBSERVABILITY ATTRACTOR'}</span>
            <button className="mf-x" onClick={onClose} aria-label="close evidence tray">×</button>
          </div>
          <div className="mf-card-h"><h3>{c.name}</h3><State s={c.status} kind={kind[0]} label={kind === 'marker' ? c.investigation_state : c.attractor_state} /></div>
          <p className="mf-basis">{(c.ranking_factors || []).join(' · ')}</p>
        </header>
        <div className="mf-tray-b">
          <TraySection title={kind === 'marker' ? 'WHAT THIS MARKER WOULD PERCEIVE' : 'CAPABILITY PAYLOAD'}>
            {kind === 'marker' ? <MarkerSummary m={c} ctx={ctx} /> : <CapabilitySummary c={c} ctx={ctx} onPush={onPush} />}
          </TraySection>

          <TraySection title="INVESTIGATION BASIS">
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

          <TraySection title={`LITERATURE BASIS (${papers.length})`}>
            {!papers.length && <p className="mf-empty">No literature attached yet. This remains an open research task; no literature support is implied.</p>}
            {papers.map(p => <Paper key={p.id} p={p} />)}
          </TraySection>

          <TraySection title={`CURRENT-DATA AND PROJECT EVIDENCE (${records.length})`}>
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
              <tr><td>governed id</td><td><code>{c.id}</code></td></tr>
              <tr><td>derived state</td><td>{c.status} · {c.status_basis}</td></tr>
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
      <p className="mf-lead">{m.observable || m.proposition}</p>
      <table className="mf-kv"><tbody>
        <tr><td>marker form</td><td>{m.marker_kind} · {representationWord(m.representation)}</td></tr>
        {m.scientific_question && <tr><td>question</td><td>{m.scientific_question}</td></tr>}
        <tr><td>why it may matter</td><td>{m.why_relevant || '—'}</td></tr>
        <tr><td>related inquiry</td><td><Chips chips={chips} ctx={ctx} />{chips.filter(x => x.statement).map(x => <p key={x.key} className="mf-muted">{x.label}: {x.statement}</p>)}</td></tr>
        {decisionValue(ctx.doc, m, ctx.batch) && <tr><td>decision leverage</td><td>{decisionValue(ctx.doc, m, ctx.batch).text}</td></tr>}
        <tr><td>scientific definition</td><td>{m.scientific_definition || '—'}</td></tr>
        <tr><td>observation protocol</td><td>{m.measurement_definition || '—'}</td></tr>
        {m.observation_family && <tr><td>observation family</td><td>{m.observation_family.replaceAll('_', ' ')}</td></tr>}
        {m.support_model && <tr><td>support model</td><td>{m.support_model.replaceAll('_', ' ')}</td></tr>}
        {m.uncertainty_adapter && <tr><td>uncertainty adapter</td><td>{m.uncertainty_adapter.replaceAll('_', ' ')}</td></tr>}
        {m.reference_protocol && <tr><td>reference protocol</td><td>{m.reference_protocol.replaceAll('_', ' ')} · provisional</td></tr>}
        <tr><td>observability</td><td><b>{m.observability ? m.observability.label : cc === 'yes' ? 'CURRENT CAPTURE' : 'OPEN'}</b> · test: {testWord(t.status)}{t.note ? ` · ${t.note}` : ''}
          {m.capture_requirements && <p className="mf-muted">{m.capture_requirements}</p>}
          {t.requires_actions.length > 0 && <p className="mf-muted">controller action: {t.requires_actions.map(a => `${a.verb} (${a.batch}, tier ${a.tier})`).join(' · ')}</p>}
          {m.required_capabilities.length > 0 && <p className="mf-muted">requires a new capability represented by the attractor below</p>}</td></tr>
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
  const pool = c.marker_pool || c.markers_unlocked || [];
  const required = c.required_information || [];
  const chips = blindspotChips(ctx.doc, c, ctx.batch);
  const I = c.integration || {};
  return (
    <>
      <p className="mf-lead">{c.why_current_workflow_cannot_resolve || '—'}</p>
      <table className="mf-kv"><tbody>
        <tr><td>unlocks</td><td>{pool.map(id => (
          <button key={id} className={`mf-mk ${M[id].fixture ? 'fx' : ''}`} onClick={() => onPush('marker', id)}>{M[id].name} · {M[id].investigation_state || stateWord(M[id].status)}{M[id].fixture && <em>fixture</em>}</button>))}
          <p className="mf-muted">{pool.length} active opportunity{pool.length === 1 ? '' : 'ies'} · {c.credible_demands.length} with scientific basis met</p></td></tr>
        <tr><td>would expose</td><td>{required.length ? required.map(x => <div key={x}>{x}</div>) : '—'}</td></tr>
        <tr><td>related inquiry</td><td><Chips chips={chips} ctx={ctx} />{chips.filter(x => x.statement).map(x => <p key={x.key} className="mf-muted">{x.label}: {x.statement}</p>)}</td></tr>
        <tr><td>current action links</td><td>{c.decisions_affected.length ? c.decisions_affected.map(d => `${d.action} (${d.batch})`).join(' · ') : 'none'}</td></tr>
        <tr><td>lower-cost alternatives</td><td>{(c.existing_capability_substitutes || []).length ? c.existing_capability_substitutes.map(s => (
          <div key={s.id} className="mf-sub"><b>{s.label}</b> · <span className={`mf-out o-${s.ruled_out === true ? 'passed' : s.ruled_out === false ? 'failed' : 'inconclusive'}`}>
            {s.ruled_out === true ? 'ruled out' : s.ruled_out === false ? 'adequate substitute' : 'not assessed'}</span>
            {(s.basis || []).length > 0 && <div className="mf-muted">basis: {s.basis.map(b => basisLabel(ctx.doc, b).text).join('; ')}</div>}
            {s.note && <div className="mf-muted">{s.note}</div>}</div>)) : 'none listed'}</td></tr>
        <tr><td>lab fit</td><td>{c.integration ? <>
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

