"""Calibrate envelope thresholds by simulation under the two-level model (posterior-predictive over sigma_between)."""
p = 'qc/stats.py'
s = open(p, encoding='utf-8').read()

s = s.replace('''def _kpi_ref(vals, m_tiles, sw):
    """Two-level model: micrograph mean = material level + tile-sampling noise / sqrt(m)."""
    v, m = np.array(vals, float), np.array(m_tiles, float)
    n = len(v)
    mu, s2 = float(v.mean()), float(v.var(ddof=1))
    sw2 = sw ** 2 if np.isfinite(sw) else 0.0
    sb2 = max(0.0, s2 - sw2 * float(np.mean(1 / m)))
    t95, t99 = float(stats.t.ppf(0.975, n - 1)), float(stats.t.ppf(0.995, n - 1))
    r = dict(mean=mu, sd=float(np.sqrt(s2)), sd_between=float(np.sqrt(sb2)), sd_within_tile=float(np.sqrt(sw2)),
             var_mu=s2 / n, n=n, m_tiles=[int(x) for x in m], t95=t95, t99=t99)
    for mm in (1, 3):
        hw = np.sqrt(sb2 + sw2 / mm + s2 / n)
        r[f'pi95_m{mm}'] = [mu - t95 * hw, mu + t95 * hw]
    r['mdc95'] = float(t95 * np.sqrt(sb2 + sw2 / 3 + s2 / n))
    return r
''', '''M_MAX = 8  # thresholds tabulated for micrographs with 1..8 tiles


def _draw_sb(s2_obs, sw, mi, R, rng):
    """Plausible between-micrograph SDs given the observed baseline spread (chi-square posterior on total variance)."""
    n = len(mi)
    tot = s2_obs * (n - 1) / rng.chisquare(n - 1, R)
    return np.sqrt(np.maximum(0.0, tot - sw ** 2 * np.mean(1 / mi)))


def _sim_z(sb, sw, mi, mj, rng):
    """z-scores of new micrographs (tile counts mj) against a freshly simulated baseline (tile counts mi)."""
    R, n, M = len(sb), len(mi), len(mj)
    xb = rng.standard_normal((R, n)) * sb[:, None] + rng.standard_normal((R, n)) * sw / np.sqrt(mi)
    mu, s2 = xb.mean(1), xb.var(1, ddof=1)
    sb2 = np.maximum(0, s2 - sw ** 2 * np.mean(1 / mi))
    xt = rng.standard_normal((R, M)) * sb[:, None] + rng.standard_normal((R, M)) * sw / np.sqrt(mj)
    return (xt - mu[:, None]) / np.sqrt(sb2[:, None] + sw ** 2 / mj[None, :] + (s2 / n)[:, None] + 1e-30)


def _calibrate(s2_obs, sw, mi, R=100_000, seed=1):
    """|z| quantiles giving true 95% / 99% coverage for an approved micrograph with m tiles (m = 1..M_MAX)."""
    rng = np.random.default_rng(seed)
    mi = np.array(mi, float)
    if s2_obs <= 0 and sw <= 0:
        n = len(mi)
        return {str(m): [float(stats.t.ppf(0.975, n - 1)), float(stats.t.ppf(0.995, n - 1))] for m in range(1, M_MAX + 1)}
    sb = _draw_sb(s2_obs, sw, mi, R, rng)
    q = {}
    for m in range(1, M_MAX + 1):
        z = np.abs(_sim_z(sb, sw, mi, np.array([m], float), rng)[:, 0])
        q[str(m)] = [float(np.quantile(z, 0.95)), float(np.quantile(z, 0.99))]
    return q


def qz(R, m):
    return R['q'][str(int(min(max(m, 1), M_MAX)))]


def _kpi_ref(vals, m_tiles, sw, R_sim=100_000):
    """Two-level model: micrograph mean = material level + tile-sampling noise / sqrt(m); thresholds calibrated by simulation."""
    v, m = np.array(vals, float), np.array(m_tiles, float)
    n = len(v)
    mu, s2 = float(v.mean()), float(v.var(ddof=1))
    sw = float(sw) if np.isfinite(sw) else 0.0
    sb2 = max(0.0, s2 - sw ** 2 * float(np.mean(1 / m)))
    r = dict(mean=mu, sd=float(np.sqrt(s2)), sd_between=float(np.sqrt(sb2)), sd_within_tile=sw,
             var_mu=s2 / n, n=n, m_tiles=[int(x) for x in m], q=_calibrate(s2, sw, m, R_sim))
    for mm in (1, 3):
        hw = qz(r, mm)[0] * np.sqrt(sb2 + sw ** 2 / mm + s2 / n)
        r[f'pi95_m{mm}'] = [mu - hw, mu + hw]
    r['mdc95'] = float(qz(r, 3)[0] * np.sqrt(sb2 + sw ** 2 / 3 + s2 / n))
    return r
''')

s = s.replace('''            sub[k] = _kpi_ref([x['kpi'][k] for x in u], [x['n_tiles'] for x in u], sw[k]['sd'])''',
              '''            sub[k] = _kpi_ref([x['kpi'][k] for x in u], [x['n_tiles'] for x in u], sw[k]['sd'], R_sim=20_000)''')

s = s.replace('''        t = (x - R['mean']) / den(R, m['n_tiles'])
        tile_t = [(tk[k] - R['mean']) / den(R, 1) for tk in m['tile_kpi'].values() if np.isfinite(tk.get(k, np.nan))]
        same = sum(1 for z in tile_t if abs(z) > R['t95'] and np.sign(z) == np.sign(t))
        status = 'out' if abs(t) > R['t99'] else 'deviant' if abs(t) > R['t95'] else 'in'
        hw = R['t95'] * den(R, m['n_tiles'])
        res[k] = dict(value=x, t=float(t), status=status, pct=float(100 * (x / R['mean'] - 1)), pi95=[R['mean'] - hw, R['mean'] + hw],
                      p=float(2 * stats.t.sf(abs(t), R['n'] - 1)), tiles_beyond95=same, n_tiles=len(tile_t),''',
              '''        t = (x - R['mean']) / den(R, m['n_tiles'])
        q95, q99 = qz(R, m['n_tiles'])
        tile_t = [(tk[k] - R['mean']) / den(R, 1) for tk in m['tile_kpi'].values() if np.isfinite(tk.get(k, np.nan))]
        same = sum(1 for z in tile_t if abs(z) > qz(R, 1)[0] and np.sign(z) == np.sign(t))
        status = 'out' if abs(t) > q99 else 'deviant' if abs(t) > q95 else 'in'
        hw = q95 * den(R, m['n_tiles'])
        res[k] = dict(value=x, t=float(t), status=status, pct=float(100 * (x / R['mean'] - 1)), pi95=[R['mean'] - hw, R['mean'] + hw],
                      q95=q95, q99=q99, tiles_beyond95=same, n_tiles=len(tile_t),''')

old_null = s[s.index('def null_pvalue('):s.index('def decide(')]
new_null = '''def null_pvalue(refs, m_test, d99, d95, R=100_000, seed=0):
    """P(a batch drawn from the approved population looks at least this deviant), lexicographic statistic (D99, D95):
    D = number of micrographs with any robust KPI outside the 99% / 95% envelope. Simulated under the same two-level
    model, re-estimating the small baseline in every draw and integrating over plausible between-micrograph spread."""
    M = len(m_test)
    if M == 0:
        return 1.0, dict(p_any99=0.0, p_any95=0.0)
    rng = np.random.default_rng(seed)
    mj = np.array(m_test, float)
    e99, e95 = np.zeros((R, M), bool), np.zeros((R, M), bool)
    for Rk in refs:
        mi = np.array(Rk['m_tiles'], float)
        sb = _draw_sb(Rk['sd'] ** 2, Rk['sd_within_tile'], mi, R, rng)
        z = np.abs(_sim_z(sb, Rk['sd_within_tile'], mi, mj, rng))
        thr = np.array([qz(Rk, m) for m in mj])
        e99 |= z > thr[None, :, 1]
        e95 |= z > thr[None, :, 0]
    D99, D95 = e99.sum(1), e95.sum(1)
    p = float(np.mean((D99 > d99) | ((D99 == d99) & (D95 >= d95))))
    return p, dict(p_any99=float(np.mean(D99 >= 1)), p_any95=float(np.mean(D95 >= 1)))


'''
s = s.replace(old_null, new_null)
open(p, 'w', encoding='utf-8').write(s)

p = 'app.py'
s = open(p, encoding='utf-8').read()
s = s.replace("compared with the approved\nmicrographs via a t-based prediction interval with two variance levels",
              "compared with the approved\nmicrographs via a prediction interval with two variance levels")
s = s.replace("any *robust* KPI outside the 99%/95% envelope; the batch p-value",
              "any *robust* KPI outside the 99%/95% envelope (thresholds calibrated by simulation so the coverage is real); the batch p-value")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
