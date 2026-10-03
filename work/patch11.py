"""Stable parent naming, recommended actions, markdown report."""
p = 'qc/provenance.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''def build(records):
    """records: field records (any batches). Returns dict with parent of each key, chains and adjacency scores."""''',
'''def build(records, primary_batch='Batch_1'):
    """records: field records (any batches). Returns dict with parent of each key, chains and adjacency scores.
    Parents sharing a height get letter suffixes; signatures seen in `primary_batch` (the reference) keep the plain name."""''')
s = s.replace('''    by_h = {}
    for (h, sig) in groups:
        by_h.setdefault(h, []).append(sig)''', '''    by_h = {}
    for (h, sig), rs in groups.items():
        by_h.setdefault(h, []).append((0 if any(r['batch'] == primary_batch for r in rs) else 1, min(r['batch'] for r in rs), str(sig)))
    for h in by_h:
        by_h[h] = [x[2] for x in sorted(by_h[h])]''')
s = s.replace('''        pid = f'M{h}' if len(by_h[h]) == 1 else f'M{h}{"abcdefgh"[sorted(map(str, by_h[h])).index(str(sig))]}\'''', 'XX')
s = s.replace('''        pid = f'M{h}' if len(by_h[h]) == 1 else f'M{h}{"abcdefgh"[sorted(map(str, by_h[h])).index(str(sig))]}'
''', '''        i = by_h[h].index(str(sig))
        pid = f'M{h}' if i == 0 else f'M{h}{"bcdefghij"[i - 1]}'
''')
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/explain.py'
s = open(p, encoding='utf-8').read()
s += '''

def actions(decision, mtexts, mgs):
    """Concrete next steps for a QC engineer."""
    out = []
    v = decision['verdict']
    if v == 'REJECT':
        out.append('Quarantine the lot and send the supplier the evidence pack (KPI deviations, overlays, micrograph IDs).')
    elif v == 'INVESTIGATE':
        out.append('Hold the lot pending the checks below; do not release to coating.')
    elif v == 'ACCEPT':
        out.append('Release; append these micrographs to the trend log (they can extend the approved reference after sign-off).')
    for t in mtexts:
        if any(i.startswith('caveat') for i in t['interpretation']):
            out.append(f"EDS spot-check of the fine BSE-bright objects in {t['parent']} (confirm they are the specified additive).")
        if t['status'] in ('deviant', 'out') and any('spatially inconsistent' in f for f in t['findings']):
            out.append(f"Image 2-3 more fields of {t['parent']}: the deviation is not consistent across its tiles.")
    for m in mgs:
        if m.get('gate_reasons'):
            out.append(f"Re-image {m['parent']} under the standard BSE settings (additive contrast-to-noise >= 4) before judging its additive.")
    acq = [t['parent'] for t in mtexts if t['acquisition'] and t['status'] in ('deviant', 'out')]
    if acq:
        out.append('Standardise acquisition (black level, contrast stretching, detector set) for ' + ', '.join(acq) +
                   ' - robust KPIs were checked against such changes, moderate ones were not immune.')
    if decision['n_micrographs'] < 3:
        out.append('Acquire >= 3 independent cross-sections (separate micrographs, not adjacent tiles) to certify a batch.')
    return list(dict.fromkeys(out))


def markdown_report(res, ref):
    d = res['decision']
    L = [f"# QC report - {res['batch']}", '', f"**Verdict: {d['verdict']}**  (batch p = {d['p_batch']:.3f}; "
         f"{d['n_micrographs']} independent micrographs from {res['n_fields']} fields; reference {ref['name']})", '']
    L += [f'- {r}' for r in d['reasons']] + ['', '## Recommended actions'] + [f'- {a}' for a in res['actions']] + ['']
    L += ['## Micrographs', '', '| micrograph | tiles | status | ' + ' | '.join(v['short'] for v in KPIS.values()) + ' |',
          '|---|---|---|' + '---|' * len(KPIS)]
    for m in res['micrographs']:
        cells = []
        for k, v in KPIS.items():
            sc = m['score'][k]
            cells.append('n/m' if sc.get('t') is None else f"{sc['value'] * v['scale']:.3g} ({sc['t']:+.1f})")
        L.append(f"| {m['parent']} | {', '.join(m['fids'])} | {m['status']} | " + ' | '.join(cells) + ' |')
    L += ['', 'Cells: value (t vs approved). Approved means: ' + '; '.join(
        f"{v['short']} {ref['kpi'][k]['mean'] * v['scale']:.3g} {v['unit']}" for k, v in KPIS.items()), '']
    for t in res['explanations']:
        if t['status'] in ('deviant', 'out') or t['gate']:
            L += [f"### {t['headline']} - {t['status']}"] + [f'- {f}' for f in t['findings']]
            L += [f'- => {i}' for i in t['interpretation']] + [f'- exposure (hypothesis): {r}' for r in t['risks']]
            L += [f'- gate: {g}' for g in t['gate']] + ([f"- acquisition differs: {'; '.join(t['acquisition'])}"] if t['acquisition'] else []) + ['']
    return '\\n'.join(L)
'''
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/pipeline.py'
s = open(p, encoding='utf-8').read()
s = s.replace("    prov = provenance.build(allr)\n    mgs = stats.micrographs(recs, prov['parent_of'])\n    sw = ",
              "    prov = provenance.build(allr, os.path.basename(os.path.normpath(baseline_dir)))\n    mgs = stats.micrographs(recs, prov['parent_of'])\n    sw = ")
s = s.replace("""    allr = known_records()
    prov = provenance.build(allr)
    mgs = stats.micrographs(recs, prov['parent_of'])
    decision = stats.decide(mgs, ref)""", """    allr = known_records()
    prov = provenance.build(allr, ref['name'])
    mgs = stats.micrographs(recs, prov['parent_of'])
    decision = stats.decide(mgs, ref)""")
s = s.replace("""               mdc95={k: ref['kpi'][k]['mdc95'] for k in stats.KPIS})""", """               mdc95={k: ref['kpi'][k]['mdc95'] for k in stats.KPIS})
    res['actions'] = explain.actions(decision, mtexts, mgs)""")
s = s.replace("""    json.dump(_clean(res), open(os.path.join(REPORTS, batch, 'result.json'), 'w'), indent=1)""",
"""    json.dump(_clean(res), open(os.path.join(REPORTS, batch, 'result.json'), 'w'), indent=1)
    open(os.path.join(REPORTS, batch, 'report.md'), 'w', encoding='utf-8').write(explain.markdown_report(_clean(res), ref))""")
open(p, 'w', encoding='utf-8').write(s)

p = 'app.py'
s = open(p, encoding='utf-8').read()
s = s.replace("""for r in d['reasons']:
    st.markdown(f'- {r}')
""", """for r in d['reasons']:
    st.markdown(f'- {r}')
if res.get('actions'):
    with st.expander('Recommended actions', expanded=d['verdict'] != 'ACCEPT'):
        for a in res['actions']:
            st.markdown(f'- {a}')
""")
s = s.replace("    prov = all_chains(", "    prov = all_chains(")
s = s.replace("def all_chains(mtime):\n    return provenance.build(known_records())", "def all_chains(mtime):\n    return provenance.build(known_records(), ref['name'])")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
