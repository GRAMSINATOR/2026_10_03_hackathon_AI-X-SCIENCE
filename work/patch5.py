p = 'qc/stats.py'; s = open(p, encoding='utf-8').read()
s = s.replace("ref['secondary'][k] = dict(mean=float(v.mean()), sd=float(v.std(ddof=1)), n=len(v))",
              "ref['secondary'][k] = dict(mean=float(v.mean()), sd=float(v.std(ddof=1)), n=len(v), min=float(v.min()), max=float(v.max()))")
open(p, 'w', encoding='utf-8').write(s)
p = 'qc/explain.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""        if fu is not None and rf and np.isfinite(fu) and fu < rf['mean'] - 2 * rf['sd']:
            interp.append(f"caveat: the fine objects are BSE-dimmer than approved additive fines (u = {fu:.2f} vs "
                          f"{rf['mean']:.2f} ± {rf['sd']:.2f}); they may be partly sub-surface particles or a lower-Z fine phase "
                          "- confirm identity with EDS before attributing to the additive supplier")""",
"""        if fu is not None and rf and np.isfinite(fu) and fu <= rf['min']:
            interp.append(f"caveat: these fine objects sit at the dim end of the approved range (BSE brightness u = {fu:.2f} vs "
                          f"approved {rf['min']:.2f}-{rf['max']:.2f}); part of the excess may be sub-surface particles or a "
                          "lower-Z fine phase - EDS spot-check recommended before attributing it to the additive supplier")""")
open(p, 'w', encoding='utf-8').write(s)
