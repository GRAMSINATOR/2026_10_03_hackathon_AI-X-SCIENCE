"""One-off patch: two-level variance model in qc/stats.py + plumbing."""
p = 'qc/stats.py'
s = open(p, encoding='utf-8').read()
old_ref = s[s.index('def _kpi_ref(vals):'):s.index('def worst(sc):')]
new_ref = '''def within_sd(records, parent_of):
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


def _kpi_ref(vals, m_tiles, sw):
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
            ref['secondary'][k] = dict(mean=float(v.mean()), sd=float(v.std(ddof=1)), n=len(v))
    for a in ACQ:
        v = [m['acq'][a] for m in mgs if all(m['gate'].values())]
        ref['acq_envelope'][a] = [float(min(v)), float(max(v))]
    audit = []  # leave-one-micrograph-out self-audit of the baseline
    for m in mgs:
        rest = [x for x in mgs if x is not m]
        sub = {}
        for k, meta in KPIS.items():
            u = [x for x in rest if x['gate'][meta['family']] and np.isfinite(x['kpi'][k])]
            sub[k] = _kpi_ref([x['kpi'][k] for x in u], [x['n_tiles'] for x in u], sw[k]['sd'])
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
        tile_t = [(tk[k] - R['mean']) / den(R, 1) for tk in m['tile_kpi'].values() if np.isfinite(tk.get(k, np.nan))]
        same = sum(1 for z in tile_t if abs(z) > R['t95'] and np.sign(z) == np.sign(t))
        status = 'out' if abs(t) > R['t99'] else 'deviant' if abs(t) > R['t95'] else 'in'
        hw = R['t95'] * den(R, m['n_tiles'])
        res[k] = dict(value=x, t=float(t), status=status, pct=float(100 * (x / R['mean'] - 1)), pi95=[R['mean'] - hw, R['mean'] + hw],
                      p=float(2 * stats.t.sf(abs(t), R['n'] - 1)), tiles_beyond95=same, n_tiles=len(tile_t),
                      consistent=bool(len(tile_t) == 1 or same >= max(2, int(np.ceil(2 * len(tile_t) / 3)))))
    return res


'''
s = s.replace(old_ref, new_ref)
old_null = s[s.index('def null_pvalue('):s.index('def decide(')]
new_null = '''def null_pvalue(refs, m_test, d99, d95, R=100_000, seed=0):
    """P(a batch drawn from the approved population looks at least this deviant), lexicographic statistic (D99, D95):
    D = number of micrographs with any robust KPI outside the 99% / 95% envelope. Parametric bootstrap under the
    same two-level model, re-estimating the baseline in every draw (captures small-baseline uncertainty)."""
    M = len(m_test)
    if M == 0:
        return 1.0, dict(p_any99=0.0, p_any95=0.0)
    rng = np.random.default_rng(seed)
    mj = np.array(m_test, float)
    e99, e95 = np.zeros((R, M), bool), np.zeros((R, M), bool)
    for Rk in refs:
        sb, sw, mi = Rk['sd_between'], Rk['sd_within_tile'], np.array(Rk['m_tiles'], float)
        n = len(mi)
        xb = rng.normal(0, sb, (R, n)) + rng.normal(0, 1, (R, n)) * sw / np.sqrt(mi)
        mu, s2 = xb.mean(1), xb.var(1, ddof=1)
        sb2 = np.maximum(0, s2 - sw ** 2 * np.mean(1 / mi))
        xt = rng.normal(0, sb, (R, M)) + rng.normal(0, 1, (R, M)) * sw / np.sqrt(mj)
        z = (xt - mu[:, None]) / np.sqrt(sb2[:, None] + sw ** 2 / mj[None, :] + (s2 / n)[:, None])
        e99 |= np.abs(z) > stats.t.ppf(0.995, n - 1)
        e95 |= np.abs(z) > stats.t.ppf(0.975, n - 1)
    D99, D95 = e99.sum(1), e95.sum(1)
    p = float(np.mean((D99 > d99) | ((D99 == d99) & (D95 >= d95))))
    return p, dict(p_any99=float(np.mean(D99 >= 1)), p_any95=float(np.mean(D95 >= 1)))


'''
s = s.replace(old_null, new_null)
s = s.replace("p, null = null_pvalue([ref['kpi'][k]['n'] for k in robust], len(valid), d99, d95)",
              "p, null = null_pvalue([ref['kpi'][k] for k in robust], [m['n_tiles'] for m in valid], d99, d95)")
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/pipeline.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''def build_reference(baseline_dir, workers=None):
    recs = process_folder(baseline_dir, workers)
    allr = known_records()
    prov = provenance.build(allr)
    mgs = stats.micrographs(recs, prov['parent_of'])
    ref = stats.build_reference(mgs, os.path.basename(os.path.normpath(baseline_dir)))''', '''def build_reference(baseline_dir, noise_dirs=(), workers=None):
    """Reference = baseline micrographs (location, between-micrograph spread). Tile-sampling noise is pooled from
    replicate tiles of the same micrograph across baseline + noise_dirs (spread only, never their means)."""
    recs = process_folder(baseline_dir, workers)
    for d in noise_dirs:
        process_folder(d, workers)
    allr = known_records()
    prov = provenance.build(allr)
    mgs = stats.micrographs(recs, prov['parent_of'])
    sw = stats.within_sd(allr, prov['parent_of'])
    ref = stats.build_reference(mgs, os.path.basename(os.path.normpath(baseline_dir)), sw)''')
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/__main__.py'
s = open(p, encoding='utf-8').read()
s = s.replace("    a.add_argument('baseline')\n", "    a.add_argument('baseline')\n    a.add_argument('--noise-from', nargs='*', default=[])\n")
s = s.replace("ref = pipeline.build_reference(args.baseline, args.workers)",
              "ref = pipeline.build_reference(args.baseline, args.noise_from, args.workers)")
s = s.replace('''            print(f"  {k:22s} mean {v['mean']:.4g} sd {v['sd']:.3g} n {v['n']}  95% PI {v['pi95'][0]:.4g}–{v['pi95'][1]:.4g}  excluded {v['excluded']}")''',
              '''            print(f"  {k:20s} mean {v['mean']:.4g} sd_between {v['sd_between']:.3g} sd_tile {v['sd_within_tile']:.3g} n {v['n']} "
                  f"95% PI(3 tiles) {v['pi95_m3'][0]:.4g}-{v['pi95_m3'][1]:.4g} excl {v['excluded']}")''')
open(p, 'w', encoding='utf-8').write(s)
print('patched')
