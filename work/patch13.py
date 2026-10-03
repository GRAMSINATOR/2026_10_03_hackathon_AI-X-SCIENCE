p = 'qc/stats.py'; s = open(p, encoding='utf-8').read()
s = s[:s.index('def decide(mgs, ref):')] + '''def _core(mgs, ref, R=100_000):
    """Batch decision from independent micrographs (reference-linked ones are shown but carry no independent weight)."""
    robust = [k for k, v in KPIS.items() if v['cls'] == 'robust']
    indep = [m for m in mgs if not m.get('ref_linked')]
    valid = [m for m in indep if m['gate']['additive']]
    d99 = sum(any(m['score'][k]['status'] == 'out' for k in robust) for m in valid)
    d95 = sum(any(m['score'][k]['status'] in ('out', 'deviant') for k in robust) for m in valid)
    sev = max([abs(m['score'][k]['t']) / m['score'][k]['q99'] for m in valid for k in robust if m['score'][k].get('q99')], default=0.0)
    p, null = null_pvalue([ref['kpi'][k] for k in robust], [m['n_tiles'] for m in valid], sev, d95, R=R)
    consistent_out = [m['parent'] for m in valid if any(m['score'][k]['status'] == 'out' and m['score'][k]['consistent'] for k in robust)]
    moderate_out = [m['parent'] for m in indep if any(m['score'][k]['status'] == 'out' for k, v in KPIS.items() if v['cls'] == 'moderate')]
    gate_fail = [m['parent'] for m in indep if not all(m['gate'].values())]
    linked = [m['parent'] for m in mgs if m.get('ref_linked')]
    reasons = []
    if p < ALPHA_REJECT and consistent_out:
        verdict = 'REJECT'
        reasons.append(f'{d99} of {len(valid)} independent micrographs fall outside the approved 99% envelope on a robust KPI '
                       f'(tile-consistent: {", ".join(consistent_out)}); an approved batch would look this deviant with p = {p:.3f}.')
    else:
        verdict = 'ACCEPT'
        if p < ALPHA_INVESTIGATE or d99 >= 1:
            verdict = 'INVESTIGATE'
            reasons.append(f'{d99} micrograph(s) outside the 99% envelope and {d95} outside the 95% envelope on robust KPIs '
                           f'(batch p = {p:.3f}; REJECT needs p < {ALPHA_REJECT} with tile-consistent evidence).')
        if moderate_out:
            verdict = 'INVESTIGATE'
            reasons.append(f'moderate-robustness KPI outside 99% envelope in {", ".join(moderate_out)} (acquisition-sensitive; confirm).')
    if gate_fail:
        verdict = 'INVESTIGATE' if verdict == 'ACCEPT' else verdict
        reasons.append(f'measurement-validity gate failed for {", ".join(gate_fail)}; affected KPIs not used.')
    if len(indep) < 3:
        verdict = 'INVESTIGATE' if verdict == 'ACCEPT' else verdict
        reasons.append(f'only {len(indep)} independent micrograph(s): too few to certify the batch.')
    if linked:
        reasons.append(f'{len(linked)} micrograph(s) ({", ".join(linked)}) are physical continuations of approved baseline '
                       'cross-sections: shown, but excluded from the batch test (not independent of the reference).')
    if verdict == 'ACCEPT':
        reasons.append(f'all {len(indep)} independent micrographs inside the approved envelope on every measurable KPI '
                       f'(batch p = {p:.3f}).')
    return dict(verdict=verdict, p_batch=p, d99=d99, d95=d95, severity=sev, n_micrographs=len(mgs), n_independent=len(indep),
                n_valid_additive=len(valid), ref_linked=linked, reasons=reasons, null=null, consistent_out=consistent_out,
                moderate_out=moderate_out, gate_fail=gate_fail)


def decide(mgs, ref, linked=()):
    """Score micrographs, decide, and measure decision leverage (verdict with each independent micrograph removed)."""
    for m in mgs:
        gate(m, ref['px_nm'])
        m['score'] = score(m, ref)
        m['status'] = worst(m['score'])
        m['ref_linked'] = m['parent'] in set(linked)
    d = _core(mgs, ref)
    for m in mgs:
        if m['ref_linked']:
            m['leverage'] = None
            continue
        sub = _core([x for x in mgs if x is not m], ref, R=40_000)
        m['leverage'] = dict(verdict_without=sub['verdict'], p_without=sub['p_batch'], flips=sub['verdict'] != d['verdict'])
    d['pivotal'] = [m['parent'] for m in mgs if m.get('leverage') and m['leverage']['flips']]
    return d
'''
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/pipeline.py'; s = open(p, encoding='utf-8').read()
s = s.replace("    decision = stats.decide(mgs, ref)\n    if is_ref:",
              "    linked = set() if is_ref else {m['parent'] for m in ref['micrographs']}\n    decision = stats.decide(mgs, ref, linked)\n    if is_ref:")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
