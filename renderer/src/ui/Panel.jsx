// Explanation panel: rich contract-driven detail; every accent uses the same category hue as the keys.
import { explainKey, explainStage, explainAction, actionPresentation, legendFor } from '../model/explain.js';
import { STAGES } from '../model/adapter.js';
import { BLOCK_LABEL, describeRef } from '../model/brief.js';
import { HERO_HUE } from './Hero.jsx';

// The traced claim keeps its governed context and proof references without presenting them as a second navigation system.
function Trace({ M, c, onClear }) {
  const hue = HERO_HUE[c.block] || '#55524c';
  const context = (BLOCK_LABEL[c.block] || c.block).replace('SURVIVING ', '').replace('ACQUISITION ', '');
  const value = c.label && c.label.toUpperCase() !== context.toUpperCase() ? c.label : null;
  return (
    <section className="px-trace" key={c.id} style={{ '--hue': hue }}>
      <header className="trace-head">
        <b>{context} proof</b>
        {value && <span>{value}</span>}
        <button onClick={onClear} aria-label="close trace">×</button>
      </header>
      <p className="tr-claim">{c.text}</p>
      {c.fact && <p className="tr-fact">{c.fact}</p>}
      {c.details.length > 0 && <ul className="tr-details">{c.details.map((d, i) => <li key={i}>{d.text}</li>)}</ul>}
      <table className="tr-refs"><tbody>{c.proof_refs.map((r, i) => { const d = describeRef(M.F, r); return (
        <tr key={i} className={d.ok ? '' : 'bad'}><td>{d.where}</td><td>{d.value}</td></tr>); })}</tbody></table>
      {c.action_refs.length > 0 && <p className="tr-acts">next capture: {c.action_refs.map(a => (M.actions.find(x => x.id === a) || {}).verb || a).join(' · ')}</p>}
    </section>
  );
}

function Section({ s }) {
  const accent = s.hue || '#5a564e';
  return (
    <section className="px-sec" style={{ borderLeftColor: accent }}>
      <h4>{s.title}</h4>
      {s.bar && (
        <>
          <div className="px-bar">{s.bar.map(p => <i key={p.label} title={`${p.label} ${Math.round(100 * p.share)}%`} style={{ width: `${100 * p.share}%`, background: p.hue }} />)}</div>
          <div className="px-barlab">{s.bar.map(p => <span key={p.label}><i style={{ background: p.hue }} />{p.label} {Math.round(100 * p.share)}%</span>)}</div>
        </>
      )}
      {s.rows && <table><tbody>{s.rows.map(([k, v]) => <tr key={k}><td>{k}</td><td>{v}</td></tr>)}</tbody></table>}
      {s.notes && s.notes.filter(n => n.text).map((n, i) => (
        <p key={i} className="px-note">{n.hue && <i style={{ background: n.hue }} />}{n.text}</p>))}
    </section>
  );
}

function SelectedAction({ M, index }) {
  const p = actionPresentation(M, index);
  if (!p) return null;
  return (
    <section className="px-rec" style={{ '--hue': p.action.reach.hue }} aria-label="selected action">
      <span className="px-rec-kicker">Selected action</span>
      <div className="px-rec-command"><b>{p.action.verb}</b><h3>{p.action.title}</h3></div>
      <dl>
        <div><dt>Why</dt><dd>{p.why}</dd></div>
        <div><dt>Resolves</dt><dd>{p.resolves}</dd></div>
      </dl>
      {p.leverage && <p className="px-rec-leverage">{p.leverage}</p>}
      <div className="px-rec-meta"><span>{p.tier}</span><span>{p.grounding}</span><span>{p.cost}</span></div>
    </section>
  );
}

export default function Panel({ M, stage, selKey, action, setAction, trace, onClearTrace }) {
  const ex = selKey ? explainKey(M, selKey, stage, { action }) : explainStage(M, stage, action);
  const legend = legendFor(M, stage, { action });
  const actionRows = stage === 4 ? M.actions.map((a, i) => actionPresentation(M, i)) : [];
  const sections = stage === 4 ? ex.sections.filter(s => !['action', 'actions', 'category'].includes(s.id)) : ex.sections;
  return (
    <aside className="panel"><div className="px-scroll">
      {trace && stage !== 4 && <Trace M={M} c={trace} onClear={onClearTrace} />}
      {stage === 4 && (
        <div className="px-actions">
          <h3>Next capture <span>{M.actions.length} ranked actions</span></h3>
          {actionRows.map((p, i) => (
            <button key={p.action.id} className={i === action ? 'on' : ''} onClick={() => setAction(i)} aria-pressed={i === action}>
              <i style={{ background: p.action.reach.hue }} /><b>{p.action.verb}</b><span>{p.listLabel}</span><em>{p.tier}</em>
            </button>))}
        </div>
      )}
      {stage === 4 && action != null && <SelectedAction M={M} index={action} />}
      {stage === 4 && action != null && <Section s={explainAction(M, action)} />}
      {trace && stage === 4 && <Trace M={M} c={trace} onClear={onClearTrace} />}
      <div className="px-head"><h3>{stage === 4 ? 'Evidence detail' : ex.title}</h3><span>{stage === 4 ? ex.title : ex.subtitle}</span></div>
      {sections.map(s => <Section key={s.id + s.title} s={s} />)}
      {legend.length > 0 && (
        <div className="px-legend"><b>KEY COLOURS · {STAGES[stage]}</b>{legend.map(l => <span key={l.label}><i style={{ background: l.hue }} />{l.label}</span>)}</div>
      )}
    </div></aside>
  );
}
