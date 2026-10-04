// Decision brief hero: what the system knows, what it does not, whether the data is enough, and what to measure next.
// Pure rendering of decision-brief/1: every word and number comes from the brief, every click traces a claim to its proof.
import { useMemo } from 'react';

const VERDICT_HUE = { REJECT: '#c8392c', ACCEPT: '#1d8f50', INVESTIGATE: '#b07800', REFERENCE: '#2f62c4' };
// semantic class hues (presentation only): one hue per kind of statement, never a severity scale
export const HERO_HUE = { data_support: '#1677b8', surviving_evidence: '#6a3fd6', limits: '#c2307a', acquisition_policy: '#0f8a6a' };
const SUPPORT_TONE = { sufficient: 'ok', at_minimum: 'thin', partial: 'thin', expansion_needed: 'open', change_modality: 'open',
  reacquire: 'bad', not_applicable: 'na', no_expansion_justified: 'ok' };

function Block({ k, title, hue, claim, onTrace, traced, children, className = '' }) {
  const go = () => claim && onTrace(claim);
  return (
    <div className={`hb hb-${k} ${className} ${traced && claim && traced === claim.id ? 'traced' : ''}`} style={{ '--hue': hue }}
         role="button" tabIndex={0} aria-label={`${title}: trace to proof`} onClick={go}
         onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } }}>
      <span className="hb-ch">{title}</span>
      {children}
    </div>
  );
}

function Chip({ c, onTrace, traced, children, className = '' }) {
  return (
    <button className={`hb-chip ${className} ${traced === c.id ? 'traced' : ''}`} onClick={e => { e.stopPropagation(); onTrace(c); }}
            title="trace this claim to its proof">{children}</button>
  );
}

export default function Hero({ brief, onTrace, traced }) {
  const C = useMemo(() => Object.fromEntries(brief.claims.map(c => [c.id, c])), [brief]);
  const H = brief.hero;
  const dec = C['decision.verdict'], scope = C[H.decision.footer];
  const [qc, ...supRest] = H.data_support.claims.map(i => C[i]);
  const ev = H.surviving_evidence.claims.map(i => C[i]);
  const evMain = ev.find(c => c.kind === 'surviving_evidence') || ev.find(c => c.kind === 'evidence_summary');
  const evRest = ev.filter(c => c !== evMain);
  const lims = H.limits.claims.map(i => C[i]);
  const steps = H.acquisition_policy.claims.map(i => C[i]);
  return (
    <section className="hero" aria-label="decision brief">
      <Block k="decision" title="DECISION" hue={VERDICT_HUE[H.decision.state]} claim={dec} onTrace={onTrace} traced={traced}>
        <div className="hb-state hb-verdict">{H.decision.state}</div>
        <p className="hb-text">{dec.text}</p>
        <p className="hb-fact">{dec.fact}</p>
      </Block>

      <Block k="support" title="DATA SUPPORT" hue={HERO_HUE.data_support} claim={qc} onTrace={onTrace} traced={traced}>
        <div className="hb-state">{H.data_support.state}</div>
        {H.data_support.qualifier && <div className="hb-qual">{H.data_support.qualifier}</div>}
        <p className="hb-text">{qc.text}</p>
        <div className="hb-chips">
          {supRest.map(c => (
            <Chip key={c.id} c={c} onTrace={onTrace} traced={traced} className={`tone-${SUPPORT_TONE[c.status] || 'na'}`}>
              <b>{c.label}</b><span>{c.state_label}</span>
            </Chip>))}
        </div>
      </Block>

      <Block k="evidence" title="SURVIVING EVIDENCE" hue={HERO_HUE.surviving_evidence} claim={evMain} onTrace={onTrace} traced={traced}>
        <div className="hb-state">{H.surviving_evidence.state}</div>
        <p className="hb-text">{evMain.text}</p>
        {evMain.fact && <p className="hb-fact">{evMain.fact}</p>}
        {evRest.length > 0 && (
          <p className="hb-aside">{evRest.map((c, i) => (
            <span key={c.id}>{i > 0 && ' · '}<button className={traced === c.id ? 'traced' : ''} onClick={e => { e.stopPropagation(); onTrace(c); }}>{c.text}</button></span>))}</p>)}
      </Block>

      <Block k="limits" title="LIMITS" hue={HERO_HUE.limits} claim={lims[0]} onTrace={onTrace} traced={traced}>
        <div className="hb-state hb-state-list">{H.limits.state}</div>
        <ul className="hb-lims">
          {lims.map(c => (
            <li key={c.id}><Chip c={c} onTrace={onTrace} traced={traced} className="lim"><b>{c.label}</b><span>{c.text}</span></Chip></li>))}
        </ul>
      </Block>

      <Block k="policy" title="ACQUISITION POLICY" hue={HERO_HUE.acquisition_policy} claim={steps[0]} onTrace={onTrace} traced={traced} className="wide">
        <div className="hb-policy">
          <div className="hb-state">{H.acquisition_policy.state}</div>
          {/* ranked steps in one tray: chroma steps down with rank (explicit: earlier = do first) */}
          <div className="seq" role="list">
            {steps.map((c, i) => (
              <button key={c.id} role="listitem" className={`seg ${traced === c.id ? 'traced' : ''}`} style={{ '--i': i, zIndex: steps.length - i }}
                      onClick={e => { e.stopPropagation(); onTrace(c); }} title={c.text}>
                <b>{c.label}</b><span>{stepText(c)}</span>
              </button>))}
            <span className="seq-end" aria-hidden="true">→</span>
          </div>
          {H.acquisition_policy.later.length > 0 && (
            <p className="hb-later">then, lower tiers: {H.acquisition_policy.later.map(l => l.step).join(' · ')}</p>)}
        </div>
      </Block>
      {scope && (
        <button className={`hero-scope ${traced === scope.id ? 'traced' : ''}`} onClick={() => onTrace(scope)} title="trace the scope of this decision">
          <b>SCOPE</b> {scope.text}</button>)}
    </section>
  );
}

// the segment already shows the verb; drop it from the step phrase ("REPEAT · repeat M2060" -> "REPEAT · M2060")
const stepText = c => (c.step.toLowerCase().startsWith(c.label.toLowerCase() + ' ') ? c.step.slice(c.label.length + 1) : c.step);
