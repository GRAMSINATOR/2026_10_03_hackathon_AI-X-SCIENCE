// Human readout assembly: four readout zones cut into one molded panel (data support · surviving evidence · limits ·
// acquisition policy), plus the compact instrument-status readout that carries the QC verdict. Pure rendering of
// decision-brief/1: every word and number comes from the brief, every click traces a claim to its proof.
import { useMemo } from 'react';

const VERDICT_HUE = { REJECT: '#c8392c', ACCEPT: '#1d8f50', INVESTIGATE: '#b07800', REFERENCE: '#2f62c4' };
// semantic class hues (presentation only): one enamel colour per kind of statement, never a severity scale
export const HERO_HUE = { decision: '#55524c', data_support: '#1677b8', surviving_evidence: '#6a3fd6', limits: '#c2307a', acquisition_policy: '#0f8a6a' };
const SUPPORT_TONE = { sufficient: 'ok', at_minimum: 'thin', partial: 'thin', expansion_needed: 'open', change_modality: 'open',
  reacquire: 'bad', not_applicable: 'na', no_expansion_justified: 'ok', resolved: 'ok', limited: 'thin', challenged: 'open' };

// compact instrument-status readout: verdict lamp + verdict + the rule's numbers; traces to the decision proof
export function StatusReadout({ brief, onTrace, traced }) {
  const c = brief && brief.claims.find(x => x.id === 'decision.verdict');
  if (!c) return null;
  return (
    <button className={`status ${traced === c.id ? 'traced' : ''}`} style={{ '--hue': VERDICT_HUE[c.status] || '#55524c' }}
            onClick={() => onTrace(c)} title={`${c.text} · trace to proof`} aria-label={`QC verdict ${c.status}: trace to proof`}>
      <span className="st-cap">{c.status === 'REFERENCE' ? 'ROLE' : 'QC VERDICT'}</span>
      <span className="st-win"><span className="st-lamp" aria-hidden="true" /><b className="st-word">{c.status}</b><span className="st-fig">{c.fact}</span></span>
    </button>
  );
}

function Zone({ k, title, hue, claim, onTrace, traced, children }) {
  const go = () => claim && onTrace(claim);
  return (
    <div className={`rz rz-${k} ${traced && claim && traced === claim.id ? 'traced' : ''}`} style={{ '--hue': hue }}
         role="button" tabIndex={0} aria-label={`${title}: trace to proof`} onClick={go}
         onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } }}>
      <span className="rz-tag">{title}</span>
      {children}
    </div>
  );
}

function Row({ c, onTrace, traced, tone, children }) {
  return (
    <button className={`rz-row ${tone ? 'tone-' + tone : ''} ${traced === c.id ? 'traced' : ''}`} onClick={e => { e.stopPropagation(); onTrace(c); }}
            title="trace this claim to its proof">{children}</button>
  );
}

export default function Hero({ brief, onTrace, traced }) {
  const C = useMemo(() => Object.fromEntries(brief.claims.map(c => [c.id, c])), [brief]);
  const H = brief.hero;
  const scope = C[H.decision.footer];
  const [qc, ...supRest] = H.data_support.claims.map(i => C[i]);
  const ev = H.surviving_evidence.claims.map(i => C[i]);
  const evMain = ev.find(c => c.kind === 'surviving_evidence') || ev.find(c => c.kind === 'evidence_summary');
  const evRest = ev.filter(c => c !== evMain);
  const lims = H.limits.claims.map(i => C[i]);
  const steps = H.acquisition_policy.claims.map(i => C[i]);
  return (
    <section className="readout" aria-label="decision brief">
      <div className="ro-grid">
        <Zone k="support" title={H.data_support.title || 'DATA SUPPORT'} hue={HERO_HUE.data_support} claim={qc} onTrace={onTrace} traced={traced}>
          <div className="rz-state">{H.data_support.state}</div>
          {H.data_support.qualifier && <div className="rz-qual">{H.data_support.qualifier}</div>}
          <p className="rz-text">{qc.text}</p>
          <div className="rz-rows">
            {supRest.map(c => (
              <Row key={c.id} c={c} onTrace={onTrace} traced={traced} tone={SUPPORT_TONE[c.status] || 'na'}>
                <i className="led" /><b>{c.label}</b><span>{c.state_label}</span>
              </Row>))}
          </div>
        </Zone>

        <Zone k="evidence" title={H.surviving_evidence.title || 'SURVIVING EVIDENCE'} hue={HERO_HUE.surviving_evidence} claim={evMain} onTrace={onTrace} traced={traced}>
          <div className="rz-state">{H.surviving_evidence.state}</div>
          <p className="rz-text">{evMain.text}</p>
          {evMain.fact && <p className="rz-fact">{evMain.fact}</p>}
          {evRest.length > 0 && (
            <p className="rz-aside">{evRest.map((c, i) => (
              <span key={c.id}>{i > 0 && ' · '}<button className={traced === c.id ? 'traced' : ''} onClick={e => { e.stopPropagation(); onTrace(c); }}>{c.text}</button></span>))}</p>)}
        </Zone>

        <Zone k="limits" title={H.limits.title || 'LIMITS'} hue={HERO_HUE.limits} claim={lims[0]} onTrace={onTrace} traced={traced}>
          <div className="rz-state rz-state-list">{H.limits.state}</div>
          <div className="rz-rows">
            {lims.map(c => <Row key={c.id} c={c} onTrace={onTrace} traced={traced} tone="lim"><i className="led" /><b>{c.label}</b><span>{c.text}</span></Row>)}
          </div>
        </Zone>

        <Zone k="policy" title={H.acquisition_policy.title || 'ACQUISITION POLICY'} hue={HERO_HUE.acquisition_policy} claim={steps[0]} onTrace={onTrace} traced={traced}>
          <div className="rz-state">{H.acquisition_policy.state}</div>
          {/* ranked steps; the indicator inlay fades with rank (explicit: earlier = do first) */}
          <ol className="rz-rows rz-steps">
            {steps.map((c, i) => (
              <li key={c.id} style={{ '--i': i }}>
                <Row c={c} onTrace={onTrace} traced={traced} tone="step"><i className="n">{i + 1}</i><b>{c.label}</b><span>{stepText(c)}</span></Row>
              </li>))}
          </ol>
          {H.acquisition_policy.later.length > 0 && (
            <p className="rz-later">then, lower tiers: {H.acquisition_policy.later.map(l => l.step).join(' · ')}</p>)}
        </Zone>
      </div>
      {scope && (
        <button className={`ro-scope ${traced === scope.id ? 'traced' : ''}`} onClick={() => onTrace(scope)} title="trace the scope of this decision">
          <b>SCOPE</b> {scope.text}</button>)}
    </section>
  );
}

// the row already shows the verb; drop it from the step phrase ("REPEAT · repeat M2060" -> "REPEAT · M2060")
const stepText = c => (c.step.toLowerCase().startsWith(c.label.toLowerCase() + ' ') ? c.step.slice(c.label.length + 1) : c.step);
