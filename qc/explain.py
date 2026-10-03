"""Plain-language explanations for a materials expert: what changed, how sure we are, what it may mean."""
import numpy as np

from .stats import ACQ, KPIS

ACQ_LABEL = dict(px_nm='pixel size (nm)', contrast_mb='matrix-to-additive BSE contrast', black_level='black level',
                 clip_black='black-clipped pixel fraction', hist_gaps='histogram gaps (contrast stretching)',
                 noise_abs='noise (grey levels)', cnr_additive='additive contrast-to-noise', sharpness='edge sharpness')

# Literature-grounded *exposure* statements (hypotheses, not measured predictions).
RISK = {
    ('additive', 'finer'): 'More numerous/finer high-Z additive particles raise additive surface area: more SEI formation and '
                           'first-cycle loss, and higher slurry viscosity/agglomeration tendency (coating uniformity).',
    ('additive', 'coarser'): 'Coarser high-Z additive: if Si-based, larger particles see higher lithiation stress and are more prone '
                             'to fracture and capacity fade (size-dependent fracture of Si, Liu et al., ACS Nano 2012). Coarse hard '
                             'particles also increase abrasive exposure of calender rolls and slitting blades.',
    ('additive', 'loading'): 'Additive loading change shifts specific capacity and the electrode swelling budget '
                             '(Si-based additives expand strongly on lithiation).',
    ('pore', 'more'): 'More open pore structure: lower electrode density (energy density), consistent with a calendering shift.',
    ('pore', 'less'): 'Denser structure: reduced electrolyte access/rate capability; over-compaction can crack particles.',
    ('structure', 'shorter'): 'Shorter in-plane solid segments: finer or more fragmented particles (milling or calendering damage).',
}


def fmt(k, v, meta=None):
    meta = meta or KPIS[k]
    return f"{v * meta['scale']:.3g}{'' if meta['unit'] in ('%', '') else ' '}{meta['unit']}"


# minimum differences that count as a different acquisition regime (instrument-level resolution of each metric)
ACQ_TOL = dict(px_nm=0.25, contrast_mb=3.0, black_level=1.0, clip_black=0.01, hist_gaps=0.05, noise_abs=1.0,
               cnr_additive=0.5, sharpness=0.03)


def acquisition_deviations(m, ref, envelope='acq_envelope'):
    """Structured: acquisition metrics of micrograph m outside an envelope (approved micrographs, or the tested range)."""
    out = []
    for a in ACQ:
        if a not in ref.get(envelope, {}):
            continue
        lo, hi = ref[envelope][a]
        v = m['acq'][a]
        tol = max(ACQ_TOL.get(a, 0.0), 0.15 * (hi - lo))
        if v < lo - tol or v > hi + tol:
            out.append(dict(metric=a, label=ACQ_LABEL[a], value=float(v), lo=float(lo), hi=float(hi), tolerance=float(tol)))
    return out


def acquisition_notes(m, ref, envelope='acq_envelope', label='baseline'):
    """Human-readable form of acquisition_deviations."""
    return [f"{d['label']} {d['value']:.3g} ({label} {d['lo']:.3g}–{d['hi']:.3g})" for d in acquisition_deviations(m, ref, envelope)]


def micrograph_text(m, ref, links):
    sc = m['score']
    head = f"{m['parent']} ({m['n_tiles']} tile{'s' if m['n_tiles'] > 1 else ''}: {', '.join(m['fids'])})"
    bad = sorted([(k, s) for k, s in sc.items() if s['status'] in ('deviant', 'out')], key=lambda x: -abs(x[1]['t']))
    lines = []
    for k, s in bad:
        R = ref['kpi'][k]
        lines.append(f"{KPIS[k]['label']}: {fmt(k, s['value'])} vs approved {fmt(k, R['mean'])} ± {fmt(k, R['sd'])} "
                     f"({s['pct']:+.0f}%, t = {s['t']:+.1f}, {'outside 99%' if s['status'] == 'out' else 'outside 95%'} envelope; "
                     f"{s['tiles_beyond95']}/{s['n_tiles']} tiles beyond 95%{'' if s['consistent'] else ' – spatially inconsistent'}).")
    interp, risks = [], []
    st = lambda k: sc[k]['status'] in ('deviant', 'out')
    tt = lambda k: sc[k]['t'] if np.isfinite(sc[k]['t']) else 0.0
    if st('additive_density') and tt('additive_density') > 0 or st('additive_d50_um') and tt('additive_d50_um') < 0:
        interp.append('additive particle-size distribution shifted toward fines' +
                      (' at unchanged additive loading' if sc['additive_area_frac']['status'] == 'in' else ''))
        risks.append(RISK[('additive', 'finer')])
        fu, rf = m['kpi'].get('additive_fines_u'), ref['secondary'].get('additive_fines_u')
        if fu is not None and rf and np.isfinite(fu) and fu <= rf['min']:
            interp.append(f"caveat: these fine objects sit at the dim end of the approved range (BSE brightness u = {fu:.2f} vs "
                          f"approved {rf['min']:.2f}-{rf['max']:.2f}); part of the excess may be sub-surface particles or a "
                          "lower-Z fine phase - EDS spot-check recommended before attributing it to the additive supplier")
    if st('additive_d50_um') and tt('additive_d50_um') > 0 or st('additive_density') and tt('additive_density') < 0:
        interp.append('coarser additive (fewer fine high-Z particles)' +
                      (' at unchanged additive loading' if sc['additive_area_frac']['status'] == 'in' else ''))
        risks.append(RISK[('additive', 'coarser')])
    if st('additive_area_frac'):
        interp.append(f"additive loading {'higher' if tt('additive_area_frac') > 0 else 'lower'}")
        risks.append(RISK[('additive', 'loading')])
    if st('porosity') or st('pore_size_um'):
        more = (tt('porosity') + tt('pore_size_um')) > 0
        se2 = m['kpi'].get('porosity_SE2')
        rse = ref['secondary'].get('porosity_SE2')
        corro = ''
        if se2 is not None and rse and np.isfinite(se2):
            corro = ' (SE-detector porosity agrees)' if (se2 > rse['mean']) == more else ' (not corroborated by SE detector)'
        interp.append(f"{'more open' if more else 'denser'} pore structure{corro}")
        risks.append(RISK[('pore', 'more' if more else 'less')])
    if st('solid_chord_x_um') and tt('solid_chord_x_um') < 0:
        interp.append('shorter in-plane solid segments')
        risks.append(RISK[('structure', 'shorter')])
    acq = acquisition_notes(m, ref)
    rob = ref.get('robustness', {})
    if acq and bad and rob:
        worst_k = bad[0][0]
        r = rob.get(worst_k)
        if r:
            obs = abs(m['score'][worst_k]['value'] - ref['kpi'][worst_k]['mean'])
            interp.append(f"acquisition check: the largest synthetic acquisition change tested ({r['worst']}) moves "
                          f"{KPIS[worst_k]['label'].lower()} by {fmt(worst_k, r['max_abs'])} = "
                          f"{100 * r['max_abs'] / max(obs, 1e-12):.0f}% of the observed deviation")
    return dict(parent=m['parent'], headline=head, status=m['status'], findings=lines, interpretation=interp, risks=risks,
                acquisition=acq, gate=m['gate_reasons'], links=links.get(m['parent'], []))


def batch_summary(batch, decision, mtexts):
    flagged = [t for t in mtexts if t['status'] in ('deviant', 'out')]
    s = f"{batch}: {decision['verdict']}. {decision['n_micrographs']} independent micrograph(s)."
    if flagged:
        main = lambda t: next((i for i in t['interpretation'] if not i.startswith(('caveat', 'acquisition check'))), 'see KPIs')
        s += ' Deviating: ' + '; '.join(f"{t['parent']} ({t['status']}) – {main(t)}" for t in flagged) + '.'
    return s


def actions(decision, mtexts, mgs):
    """Concrete next steps for a QC engineer."""
    out = []
    v = decision['verdict']
    if v == 'REJECT':
        out.append('Quarantine the lot and send the supplier the evidence pack (KPI deviations, overlays, micrograph IDs).')
    elif v == 'INVESTIGATE':
        out.append('Hold the lot pending the checks below; do not release to coating.')
    elif v == 'ACCEPT':
        out.append('Release; append these micrographs to the trend log (they can extend the approved reference after sign-off).')
    for t in mtexts:
        if any(i.startswith('caveat') for i in t['interpretation']):
            out.append(f"EDS spot-check of the fine BSE-bright objects in {t['parent']} (confirm they are the specified additive).")
        if t['status'] in ('deviant', 'out') and any('spatially inconsistent' in f for f in t['findings']):
            out.append(f"Image 2-3 more fields of {t['parent']}: the deviation is not consistent across its tiles.")
    for m in mgs:
        if m.get('gate_reasons'):
            out.append(f"Re-image {m['parent']} under the standard BSE settings (additive contrast-to-noise >= 4) before judging its additive.")
    acq = [t['parent'] for t in mtexts if t['acquisition'] and t['status'] in ('deviant', 'out')]
    if acq:
        out.append('Standardise acquisition (black level, contrast stretching, detector set) for ' + ', '.join(acq) +
                   ' - robust KPIs were checked against such changes, moderate ones were not immune.')
    if decision['n_micrographs'] < 3:
        out.append('Acquire >= 3 independent cross-sections (separate micrographs, not adjacent tiles) to certify a batch.')
    return list(dict.fromkeys(out))


def markdown_report(res, ref):
    d = res['decision']
    L = [f"# QC report - {res['batch']}", '', f"**Verdict: {d['verdict']}**  (batch p = {d['p_batch']:.3f}; "
         f"{d['n_micrographs']} independent micrographs from {res['n_fields']} fields; reference {ref['name']})", '']
    L += [f'- {r}' for r in d['reasons']] + ['', '## Recommended actions'] + [f'- {a}' for a in res['actions']] + ['']
    L += ['## Micrographs', '', '| micrograph | tiles | status | ' + ' | '.join(v['short'] for v in KPIS.values()) + ' |',
          '|---|---|---|' + '---|' * len(KPIS)]
    for m in res['micrographs']:
        cells = []
        for k, v in KPIS.items():
            sc = m['score'][k]
            cells.append('n/m' if sc.get('t') is None else f"{sc['value'] * v['scale']:.3g} ({sc['t']:+.1f})")
        L.append(f"| {m['parent']} | {', '.join(m['fids'])} | {m['status']} | " + ' | '.join(cells) + ' |')
    L += ['', 'Cells: value (t vs approved). Approved means: ' + '; '.join(
        f"{v['short']} {ref['kpi'][k]['mean'] * v['scale']:.3g} {v['unit']}" for k, v in KPIS.items()), '']
    for t in res['explanations']:
        if t['status'] in ('deviant', 'out') or t['gate']:
            L += [f"### {t['headline']} - {t['status']}"] + [f'- {f}' for f in t['findings']]
            L += [f'- => {i}' for i in t['interpretation']] + [f'- exposure (hypothesis): {r}' for r in t['risks']]
            L += [f'- gate: {g}' for g in t['gate']] + ([f"- acquisition differs: {'; '.join(t['acquisition'])}"] if t['acquisition'] else []) + ['']
    return '\n'.join(L)
