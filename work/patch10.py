"""Batch statistic = two complementary simulated tests (max-severity and count), Bonferroni-combined."""
p = 'qc/stats.py'
s = open(p, encoding='utf-8').read()
old_null = s[s.index('def null_pvalue('):s.index('def decide(')]
new_null = '''def null_pvalue(refs, m_test, sev_obs, d95_obs, R=100_000, seed=0):
    """Batch-level p-value: probability that a batch drawn from the approved population looks at least this deviant.
    Two complementary statistics, each calibrated by simulation under the two-level model (re-estimating the small
    baseline in every draw and integrating over plausible between-micrograph spread), Bonferroni-combined:
      * severity  = max over micrographs and robust KPIs of |z| / (99% threshold)  -> one micrograph far outside
      * D95       = number of micrographs with any robust KPI outside its 95% envelope -> many mildly outside"""
    M = len(m_test)
    if M == 0:
        return 1.0, dict(p_any99=0.0, p_any95=0.0, p_severity=1.0, p_count=1.0)
    rng = np.random.default_rng(seed)
    mj = np.array(m_test, float)
    sev, e95, e99 = np.zeros(R), np.zeros((R, M), bool), np.zeros((R, M), bool)
    for Rk in refs:
        mi = np.array(Rk['m_tiles'], float)
        sb = _draw_sb(Rk['sd'] ** 2, Rk['sd_within_tile'], mi, R, rng)
        z = np.abs(_sim_z(sb, Rk['sd_within_tile'], mi, mj, rng))
        thr = np.array([qz(Rk, m) for m in mj])
        sev = np.maximum(sev, (z / thr[None, :, 1]).max(1))
        e95 |= z > thr[None, :, 0]
        e99 |= z > thr[None, :, 1]
    D95 = e95.sum(1)
    p_sev = float(np.mean(sev >= sev_obs))
    p_cnt = float(np.mean(D95 >= d95_obs)) if d95_obs > 0 else 1.0
    p = min(1.0, 2 * min(p_sev, p_cnt))
    return p, dict(p_any99=float(np.mean(e99.any(1))), p_any95=float(np.mean(D95 >= 1)), p_severity=p_sev, p_count=p_cnt)


'''
s = s.replace(old_null, new_null)
s = s.replace('''    p, null = null_pvalue([ref['kpi'][k] for k in robust], [m['n_tiles'] for m in valid], d99, d95)''',
'''    sev = max([abs(m['score'][k]['t']) / m['score'][k]['q99'] for m in valid for k in robust if m['score'][k].get('q99')], default=0.0)
    p, null = null_pvalue([ref['kpi'][k] for k in robust], [m['n_tiles'] for m in valid], sev, d95)''')
s = s.replace('''    return dict(verdict=verdict, p_batch=p, d99=d99, d95=d95, n_micrographs=len(mgs), n_valid_additive=len(valid),''',
'''    return dict(verdict=verdict, p_batch=p, d99=d99, d95=d95, severity=sev, n_micrographs=len(mgs), n_valid_additive=len(valid),''')
open(p, 'w', encoding='utf-8').write(s)

p = 'app.py'
s = open(p, encoding='utf-8').read()
s = s.replace("""D99/D95 = number of micrographs with
any *robust* KPI outside the 99%/95% envelope (thresholds calibrated by simulation so the coverage is real); the batch p-value is the probability that an
approved-population batch of the same size looks at least as deviant (parametric bootstrap re-estimating the small baseline each draw).""",
"""Envelope thresholds are calibrated by
simulation so their coverage is real. The batch p-value is the probability that an approved-population batch of the same size
looks at least as deviant, combining two simulated tests (Bonferroni): *severity* (the most extreme micrograph, |z| relative to
its 99% threshold) and *count* (number of micrographs outside 95%), re-estimating the small baseline in every draw.""")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
