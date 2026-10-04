// Explanation panel: rich contract-driven detail; every accent uses the same category hue as the keys.
import { explainKey, explainStage, explainAction, legendFor } from '../model/explain.js';
import { STAGES } from '../model/adapter.js';
import { BLOCK_LABEL, describeRef } from '../model/brief.js';
import { HERO_HUE } from './Hero.jsx';

// SUMMARY -> CLAIM -> PROOF -> RAW: the traced claim is shown exactly as the brief states it, then its proof references
// with their raw values from the field, so the meaning cannot drift while drilling down.
function Trace({ M, c, onClear }) {
  const hue = HERO_HUE[c.block] || '#55524c';
  return (
    <section className="px-trace" key={c.id} style={{ '--hue': hue }}>
      <div className="trail" role="list" aria-label="proof trail">
        {['BRIEF', (BLOCK_LABEL[c.block] || c.block).replace('SURVIVING ', '').replace('ACQUISITION ', ''), c.label, 'PROOF'].map((t, i) => <span key={i} role="listitem" style={{ '--i': i }}>{t}</span>)}
        <button onClick={onClear} aria-label="close trace">×</button>
      </div>
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

export default function Panel({ M, stage, selKey, action, setAction, trace, onClearTrace }) {
  const ex = selKey ? explainKey(M, selKey, stage, { action }) : explainStage(M, stage, action);
  const legend = legendFor(M, stage, { action });
  return (
    <aside className="panel"><div className="px-scroll">
      {trace && <Trace M={M} c={trace} onClear={onClearTrace} />}
      {stage === 4 && (
        <div className="px-actions">
          <h3>Next capture</h3>
          {M.actions.map((a, i) => (
            <button key={a.id} className={i === action ? 'on' : ''} onClick={() => setAction(i)} aria-pressed={i === action}>
              <i style={{ background: a.reach.hue }} /><b>{a.verb}</b><span>{a.title}</span><em>{a.tier}</em>
            </button>))}
        </div>
      )}
      {stage === 4 && action != null && selKey && <Section s={explainAction(M, action)} />}
      <div className="px-head"><h3>{ex.title}</h3><span>{ex.subtitle}</span></div>
      {ex.sections.map(s => <Section key={s.id + s.title} s={s} />)}
      {legend.length > 0 && (
        <div className="px-legend"><b>KEY COLOURS · {STAGES[stage]}</b>{legend.map(l => <span key={l.label}><i style={{ background: l.hue }} />{l.label}</span>)}</div>
      )}
    </div></aside>
  );
}
