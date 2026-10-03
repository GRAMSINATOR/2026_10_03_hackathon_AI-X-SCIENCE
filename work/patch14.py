p = 'qc/pipeline.py'; s = open(p, encoding='utf-8').read()
s = s.replace("from . import explain, provenance, stats\n", "from . import explain, field, provenance, spatial, stats\n")
s = s.replace("""    ref['robustness_tiles'] = pick
    os.makedirs(""", """    ref['robustness_tiles'] = pick
    # capture-geometry / spatial support model (spread and correlation only)
    gated = [m['parent'] for m in ref['micrographs'] if not m['gate']['additive']]
    ref['spatial'] = spatial.model(allr, prov['parent_of'], prov['chains'], gated)
    ok_add = [r for r in recs if prov['parent_of'][r['key']] not in gated]
    ref['psd_ref'] = spatial.psd_density(ok_add)
    tagged = [dict(r, parent=prov['parent_of'][r['key']]) for r in recs]
    ref['band'] = {k: spatial.band(tagged, k, gated if k.startswith('additive') else ()) for k in spatial.SPATIAL_KPIS}
    ref['tile_range'] = {}
    for k, meta in stats.KPIS.items():
        v = [t[k] for m in ref['micrographs'] if m['gate'][meta['family']] for t in m['tile_kpi'].values() if t.get(k) is not None]
        ref['tile_range'][k] = [float(min(v)), float(max(v))]
    os.makedirs(""")
s = s.replace("""    res['actions'] = explain.actions(decision, mtexts, mgs)""", """    res['field'] = field.build(_clean(res), ref, recs, prov['chains'], allr)
    res['actions'] = [f"[{a['verb']}] {a['title']}" for a in res['field']['actions']]""")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
