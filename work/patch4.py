p = 'qc/pipeline.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""    fields = [f for f in discover(baseline_dir) if 'BSE' in f['channels']][:3]
    with Pool(min(12, (os.cpu_count() or 4) - 2)) as P:
        ref['robustness'] = robustness.card([f['channels']['BSE'] for f in fields], P)""", """    paths = {f['fid']: f['channels']['BSE'] for f in discover(baseline_dir)}
    pick = [m['fids'][0] for m in ref['micrographs'] if all(m['gate'].values())][:4]  # one valid tile per micrograph
    with Pool(min(12, (os.cpu_count() or 4) - 2)) as P:
        ref['robustness'] = robustness.card([paths[f] for f in pick], P)
    ref['robustness_tiles'] = pick""")
open(p, 'w', encoding='utf-8').write(s)
