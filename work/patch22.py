p = 'qc/field.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""        a['triggered_by'] = [r for r in a.pop('rims', []) if r in rim_ids]""",
"""        a['triggered_by'] = [r for r in a.pop('rims', []) if r in rim_ids]
        a['trigger_facts'] = [dict(collection=c, id=i, path=p) for c, i, p in a.pop('facts', [])]""")
rep = {
 "rims=[pop['id'], f'acquisition:{pid}'], title=f'Repeat {pid}": "rims=[pop['id'], f'acquisition:{pid}'], facts=[('entities', pid, 'leverage'), ('entities', pid, 'acquisition.differs_from_approved')], title=f'Repeat {pid}",
 "ents=[pid], rims=[f'scale:{pid}'],": "ents=[pid], rims=[f'scale:{pid}'], facts=[('entities', pid, 'size_distribution')],",
 "obs=mr['basis']['dependent_observations'], rims=[f'composition:{pid}'],": "obs=mr['basis']['dependent_observations'], rims=[f'composition:{pid}'], facts=[('missing_dimensions', pid, 'basis')],",
 "obs=[_oid(pid, k)], ents=[pid], rims=[rid],": "obs=[_oid(pid, k)], ents=[pid], rims=[rid], facts=[('spatial_profiles', _oid(pid, k), 'runs')],",
 "ents=[e['id'] for e in piv], rims=[pop['id']] + [f'spatial-dimension:{k}' for k in redundant],": "ents=[e['id'] for e in piv], rims=[pop['id']] + [f'spatial-dimension:{k}' for k in redundant], facts=[('decision', 'batch', 'pivotal')] + [('entities', e['id'], 'leverage') for e in piv],",
 "dims=[k], rims=[f'spatial-dimension:{k}'] + [f'spatial:{p}:{k}' for p in incons],": "dims=[k], rims=[f'spatial-dimension:{k}'] + [f'spatial:{p}:{k}' for p in incons], facts=[('dimensions', k, 'spatial_support')] + [('observations', _oid(p, k), 'scrutiny') for p in incons],",
 "ents=[e['id']], rims=[f\"validity:{e['id']}\"],": "ents=[e['id']], rims=[f\"validity:{e['id']}\"], facts=[('entities', e['id'], 'validity')],",
 "rims=[pop['id']], dims=[x['id'] for x in pick],": "rims=[pop['id']], dims=[x['id'] for x in pick], facts=[('dimensions', x['id'], 'reference') for x in pick],",
}
for a, b in rep.items():
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
