"""Micrograph-level aggregation, the approved-baseline reference model, and the ACCEPT/INVESTIGATE/REJECT decision.

Statistical unit = parent micrograph (tiles of one micrograph are spatially contiguous pseudo-replicates).
Per KPI, a new micrograph is compared with the baseline micrographs through a t-based prediction interval,
which honestly reflects how few independent baseline micrographs exist. The batch-level p-value is calibrated by
simulating batches drawn from the approved population (including the uncertainty of the small baseline).
"""
import numpy as np
from scipy import stats

# Decision-driving KPIs. Robustness class from synthetic acquisition perturbations (brightness, contrast, gamma,
# blur, noise, histogram stretch, black level, resolution): robust <= 0.6 baseline SD, moderate <= ~1 SD.
KPIS = {
    'additive_area_frac': dict(short='Additive area', label='High-Z additive area fraction', unit='%', scale=100, cls='robust', family='additive'),
    'additive_d50_um': dict(short='Additive D50', label='Additive median particle size (ECD)', unit='µm', scale=1, cls='robust', family='additive'),
    'additive_density': dict(short='Additive density', label='Additive particle number density', unit='/1000 µm²', scale=1, cls='robust', family='additive'),
    'porosity': dict(short='Porosity', label='Porosity (BSE-dark area fraction)', unit='%', scale=100, cls='moderate', family='pore'),
    'pore_size_um': dict(short='Pore size', label='Area-weighted pore size (ECD)', unit='µm', scale=1, cls='moderate', family='pore'),
    'solid_chord_x_um': dict(short='Solid chord (x)', label='In-plane solid chord length', unit='µm', scale=1, cls='moderate', family='structure'),
}
SECONDARY = {
    'additive_d90_um': dict(label='Additive D90 (ECD)', unit='µm', scale=1, family='additive'),
    'additive_max_um': dict(label='Largest additive particle (ECD)', unit='µm', scale=1, family='additive'),
    'additive_fines_u': dict(label='Brightness of fine (0.6-1 µm) additive particles (1 = additive mode)', unit='', scale=1, family='additive'),
    'porosity_SE2': dict(label='Porosity from SE detector (cross-check)', unit='%', scale=100, family='pore'),
    'pore_dice_SE2': dict(label='BSE vs SE pore-mask agreement (Dice)', unit='', scale=1, family='pore'),
    'solid_chord_y_um': dict(label='Through-thickness solid chord length', unit='µm', scale=1, family='structure'),
    'horiz_pore_frac': dict(label='Pore area in-plane oriented (±20°)', unit='%', scale=100, family='pore'),
    'long_crack_len_per_mm2': dict(label='Long in-plane crack length (>15 µm)', unit='µm/mm²', scale=1, family='pore'),
    'pore_len_max_um': dict(label='Longest pore/crack', unit='µm', scale=1, family='pore'),
}
ACQ = ['px_nm', 'contrast_mb', 'black_level', 'clip_black', 'hist_gaps', 'noise_abs', 'cnr_additive', 'sharpness']
CNR_MIN = 4.0          # additive-vs-matrix contrast-to-noise needed to segment the high-Z phase
ALPHA_REJECT, ALPHA_INVESTIGATE = 0.05, 0.20


def micrographs(records, parent_of):
    groups = {}
    for r in records:
        groups.setdefault(parent_of[r['key']], []).append(r)
    out = []
    for pid, rs in sorted(groups.items()):
        w = np.array([r['H'] * r['W'] for r in rs], float)
        kp = {}
        for k in list(KPIS) + list(SECONDARY):
            v = np.array([r['kpi'].get(k, np.nan) for r in rs], float)
            ok = np.isfinite(v)
            kp[k] = float(np.average(v[ok], weights=w[ok])) if ok.any() else float('nan')
        strips = {k: np.array([s[k] for r in rs for s in r['strips']], float) for k in KPIS}
        se = {k: float(np.nanstd(v, ddof=1) / np.sqrt(np.isfinite(v).sum())) if np.isfinite(v).sum() > 1 else float('nan')
              for k, v in strips.items()}
        acq = {a: float(np.mean([r['acq'][a] for r in rs])) for a in ACQ}
        out.append(dict(parent=pid, batch=rs[0]['batch'], keys=[r['key'] for r in rs], fids=[r['fid'] for r in rs],
                        n_tiles=len(rs), area_um2=float(w.sum() * (rs[0]['px_nm'] / 1000) ** 2), kpi=kp, se=se, acq=acq,
                        tile_kpi={r['fid']: r['kpi'] for r in rs}, detectors=sorted({d for r in rs for d in r['detectors'].values()})))
    return out


def gate(m, ref_px=None):
    """Measurement-validity gate per KPI family."""
    g = dict(additive=True, pore=True, structure=True)
    reasons = []
    if m['acq']['cnr_additive'] < CNR_MIN:
        g['additive'] = False
        reasons.append(f"additive-vs-matrix contrast-to-noise {m['acq']['cnr_additive']:.1f} < {CNR_MIN}: "
                       "high-Z phase cannot be segmented reliably (different additive chemistry or beam/detector settings)")
    if ref_px and abs(m['acq']['px_nm'] / ref_px - 1) > 0.05:
        g['structure'] = g['additive'] = False
        reasons.append(f"pixel size {m['acq']['px_nm']:.1f} nm differs from baseline {ref_px:.1f} nm: size KPIs not comparable")
    m['gate'], m['gate_reasons'] = g, reasons
    return m


def within_sd(records, parent_of):
    """Pooled within-micrograph, tile-level SD per KPI (spatial sampling noise of one field), from all micrographs
    with >= 2 tiles. Only the spread between replicate tiles is used, never their means."""
    groups = {}
    for r in records:
        groups.setdefault(parent_of[r['key']], []).append(r)
    out = {}
    for k, meta in KPIS.items():
        ss, df = 0.0, 0
        for rs in groups.values():
            v = np.array([r['kpi'][k] for r in rs if np.isfinite(r['kpi'].get(k, np.nan))
                          and (meta['family'] != 'additive' or r['acq']['cnr_additive'] >= CNR_MIN)])
            if len(v) >= 2:
                ss += float(((v - v.mean()) ** 2).sum())
                df += len(v) - 1
        out[k] = dict(sd=float(np.sqrt(ss / df)) if df else float('nan'), df=df)
    return out


M_MAX = 8  # thresholds tabulated for micrographs with 1..8 tiles


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


def den(R, m):
    return float(np.sqrt(R['sd_between'] ** 2 + R['sd_within_tile'] ** 2 / m + R['var_mu']))


def build_reference(mgs, name, sw):
    px = float(np.median([m['acq']['px_nm'] for m in mgs]))
    for m in mgs:
        gate(m, px)
    ref = dict(name=name, px_nm=px, micrographs=mgs, kpi={}, secondary={}, acq_envelope={}, within=sw)
    for k, meta in KPIS.items():
        used = [m for m in mgs if m['gate'][meta['family']] and np.isfinite(m['kpi'][k])]
        ref['kpi'][k] = dict(_kpi_ref([m['kpi'][k] for m in used], [m['n_tiles'] for m in used], sw[k]['sd']),
                             used=[m['parent'] for m in used], excluded=[m['parent'] for m in mgs if m not in used])
    for k, meta in SECONDARY.items():
        used = [m for m in mgs if m['gate'][meta['family']] and np.isfinite(m['kpi'][k])]
        if len(used) >= 2:
            v = np.array([m['kpi'][k] for m in used])
            ref['secondary'][k] = dict(mean=float(v.mean()), sd=float(v.std(ddof=1)), n=len(v), min=float(v.min()), max=float(v.max()))
    for a in ACQ:
        v = [m['acq'][a] for m in mgs if all(m['gate'].values())]
        ref['acq_envelope'][a] = [float(min(v)), float(max(v))]
    audit = []  # leave-one-micrograph-out self-audit of the baseline
    for m in mgs:
        rest = [x for x in mgs if x is not m]
        sub = {}
        for k, meta in KPIS.items():
            u = [x for x in rest if x['gate'][meta['family']] and np.isfinite(x['kpi'][k])]
            sub[k] = _kpi_ref([x['kpi'][k] for x in u], [x['n_tiles'] for x in u], sw[k]['sd'], R_sim=20_000)
        sc = score(m, dict(kpi=sub))
        audit.append(dict(parent=m['parent'], status=worst(sc), gate_reasons=m['gate_reasons'],
                          max_t=max((abs(v['t']) for v in sc.values() if np.isfinite(v['t'])), default=float('nan'))))
    ref['self_audit'] = audit
    return ref


def score(m, ref):
    res = {}
    for k, meta in KPIS.items():
        R = ref['kpi'].get(k)
        x = m['kpi'][k]
        if R is None or not m['gate'][meta['family']] or not np.isfinite(x):
            res[k] = dict(value=x, t=float('nan'), status='not measurable')
            continue
        t = (x - R['mean']) / den(R, m['n_tiles'])
        q95, q99 = qz(R, m['n_tiles'])
        tile_t = [(tk[k] - R['mean']) / den(R, 1) for tk in m['tile_kpi'].values() if np.isfinite(tk.get(k, np.nan))]
        same = sum(1 for z in tile_t if abs(z) > qz(R, 1)[0] and np.sign(z) == np.sign(t))
        status = 'out' if abs(t) > q99 else 'deviant' if abs(t) > q95 else 'in'
        hw = q95 * den(R, m['n_tiles'])
        res[k] = dict(value=x, t=float(t), status=status, pct=float(100 * (x / R['mean'] - 1)), pi95=[R['mean'] - hw, R['mean'] + hw],
                      q95=q95, q99=q99, tiles_beyond95=same, n_tiles=len(tile_t),
                      consistent=bool(len(tile_t) == 1 or same >= max(2, int(np.ceil(2 * len(tile_t) / 3)))))
    return res


def worst(sc):
    order = ['in', 'not measurable', 'deviant', 'out']
    return max((s['status'] for s in sc.values()), key=order.index)


def null_pvalue(refs, m_test, sev_obs, d95_obs, R=100_000, seed=0):
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


def _core(mgs, ref, R=100_000):
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
        why = 'batch would fall below 3 independent micrographs' if sub['n_independent'] < 3 else 'carries the decisive evidence'
        m['leverage'] = dict(verdict_without=sub['verdict'], p_without=sub['p_batch'], flips=sub['verdict'] != d['verdict'], why=why)
    d['pivotal'] = [m['parent'] for m in mgs if m.get('leverage') and m['leverage']['flips']]
    return d
