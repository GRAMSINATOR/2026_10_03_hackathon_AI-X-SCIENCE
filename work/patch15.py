p = 'qc/robustness.py'; s = open(p, encoding='utf-8').read()
s = s.replace("from .features import KPI_CROP, kpis\n", "from .features import KPI_CROP, acquisition, kpis\n")
s = s.replace("""    x = raw[:, KPI_CROP:-KPI_CROP][:, 1500:5500]
    lab, _, _ = segment(PERTURB[name](x).astype(np.float32) if name != 'none' else x, px)
    return path, name, kpis(lab, px)""", """    x = raw[:, KPI_CROP:-KPI_CROP][:, 1500:5500]
    y = PERTURB[name](x).astype(np.float32) if name != 'none' else x
    lab, s, a = segment(y, px)
    return path, name, kpis(lab, px), acquisition(y, s, a, px)""")
s = s.replace("""    res = pool.map(_one, jobs)
    base = {p: k for p, n, k in res if n == 'none'}
    table = {k: {} for k in KPIS}
    for p, n, kp in res:""", """    res = pool.map(_one, jobs)
    base = {p: k for p, n, k, _ in res if n == 'none'}
    table = {k: {} for k in KPIS}
    tested = {}
    for _, _, _, aq in res:
        for m, v in aq.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                lo, hi = tested.get(m, (v, v))
                tested[m] = (min(lo, v), max(hi, v))
    for p, n, kp, _ in res:""")
s = s.replace("""        out[k] = dict(per_perturbation=means, worst=worst, max_abs=means[worst])
    return out""", """        out[k] = dict(per_perturbation=means, worst=worst, max_abs=means[worst])
    return out, {m: [float(lo), float(hi)] for m, (lo, hi) in tested.items()}""")
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/pipeline.py'; s = open(p, encoding='utf-8').read()
s = s.replace("        ref['robustness'] = robustness.card([paths[f] for f in pick], P)",
              "        ref['robustness'], tested = robustness.card([paths[f] for f in pick], P)")
s = s.replace("    ref['robustness_tiles'] = pick\n", """    ref['robustness_tiles'] = pick
    # acquisition range whose KPI effect was actually measured = approved micrographs U perturbed images
    ref['acq_tested'] = {a: [min(lo, tested.get(a, [lo, hi])[0]), max(hi, tested.get(a, [lo, hi])[1])]
                         for a, (lo, hi) in ref['acq_envelope'].items()}
""")
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/explain.py'; s = open(p, encoding='utf-8').read()
s = s.replace('''def acquisition_notes(m, ref):
    notes = []
    for a in ACQ:
        lo, hi = ref['acq_envelope'][a]
        v = m['acq'][a]
        span = max(hi - lo, 1e-9)
        if v < lo - 0.15 * span or v > hi + 0.15 * span:
            notes.append(f"{ACQ_LABEL[a]} {v:.3g} (baseline {lo:.3g}–{hi:.3g})")
    return notes''', '''# minimum differences that count as a different acquisition regime (instrument-level resolution of each metric)
ACQ_TOL = dict(px_nm=0.25, contrast_mb=3.0, black_level=1.0, clip_black=0.01, hist_gaps=0.05, noise_abs=1.0,
               cnr_additive=0.5, sharpness=0.03)


def acquisition_notes(m, ref, envelope='acq_envelope', label='baseline'):
    """Acquisition metrics of micrograph m outside an envelope (approved micrographs, or the range actually tested)."""
    notes = []
    for a in ACQ:
        if a not in ref.get(envelope, {}):
            continue
        lo, hi = ref[envelope][a]
        v = m['acq'][a]
        tol = max(ACQ_TOL.get(a, 0.0), 0.15 * (hi - lo))
        if v < lo - tol or v > hi + tol:
            notes.append(f"{ACQ_LABEL[a]} {v:.3g} ({label} {lo:.3g}–{hi:.3g})")
    return notes''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
