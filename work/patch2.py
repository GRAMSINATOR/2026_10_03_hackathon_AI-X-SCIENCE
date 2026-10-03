p = 'qc/features.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""def acquisition(raw, s, a, px_nm):""", """def additive_brightness(lab, s, a, px_nm):
    # median normalised core intensity u = (I - m) / (b - m) of additive particles by size class (1 = high-Z mode)
    px_um = px_nm / 1000.0
    bri = lab == 2
    L = measure.label(bri)
    area = np.bincount(L.ravel())[1:] * px_um ** 2
    ecd = 2 * np.sqrt(area / np.pi)
    core = L * ndi.binary_erosion(bri, iterations=2)
    out = {}
    for name, lo, hi in (('additive_fines_u', 0.6, 1.0), ('additive_coarse_u', 2.0, 1e9)):
        idx = np.nonzero((ecd >= lo) & (ecd < hi))[0] + 1
        med = np.array(ndi.median(s, core, idx)) if len(idx) else np.array([])
        med = med[np.isfinite(med)] if med.size else med
        out[name] = float(np.median((med - a['m']) / (a['b'] - a['m']))) if med.size else float('nan')
    return out


def acquisition(raw, s, a, px_nm):""")
s = s.replace("""    rec['kpi'] = kpis(lab, px_nm)""", """    rec['kpi'] = kpis(lab, px_nm)
    rec['kpi'].update(additive_brightness(lab, s, a, px_nm))""")
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/stats.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""    'additive_max_um': dict(label='Largest additive particle (ECD)', unit='µm', scale=1, family='additive'),""",
"""    'additive_max_um': dict(label='Largest additive particle (ECD)', unit='µm', scale=1, family='additive'),
    'additive_fines_u': dict(label='Brightness of fine (0.6-1 µm) additive particles (1 = additive mode)', unit='', scale=1, family='additive'),""")
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/explain.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""        interp.append('additive particle-size distribution shifted toward fines' +
                      (' at unchanged additive loading' if sc['additive_area_frac']['status'] == 'in' else ''))
        risks.append(RISK[('additive', 'finer')])""", """        interp.append('additive particle-size distribution shifted toward fines' +
                      (' at unchanged additive loading' if sc['additive_area_frac']['status'] == 'in' else ''))
        risks.append(RISK[('additive', 'finer')])
        fu, rf = m['kpi'].get('additive_fines_u'), ref['secondary'].get('additive_fines_u')
        if fu is not None and rf and np.isfinite(fu) and fu < rf['mean'] - 2 * rf['sd']:
            interp.append(f"caveat: the fine objects are BSE-dimmer than approved additive fines (u = {fu:.2f} vs "
                          f"{rf['mean']:.2f} ± {rf['sd']:.2f}); they may be partly sub-surface particles or a lower-Z fine phase "
                          "- confirm identity with EDS before attributing to the additive supplier")""")
s = s.replace("""    acq = acquisition_notes(m, ref)""", """    acq = acquisition_notes(m, ref)
    rob = ref.get('robustness', {})
    if acq and bad and rob:
        worst_k = bad[0][0]
        r = rob.get(worst_k)
        if r:
            obs = abs(m['score'][worst_k]['value'] - ref['kpi'][worst_k]['mean'])
            interp.append(f"acquisition check: the largest synthetic acquisition change tested ({r['worst']}) moves "
                          f"{KPIS[worst_k]['label'].lower()} by {fmt(worst_k, r['max_abs'])} = "
                          f"{100 * r['max_abs'] / max(obs, 1e-12):.0f}% of the observed deviation")""")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
