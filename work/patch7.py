p = 'qc/viz.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""    for role, mgs, name in groups:
        col = ROLE[role]
        for m in mgs:""", """    fam = {KPIS[kx]['family'], KPIS[ky]['family']}
    for role, mgs, name in groups:
        col = ROLE[role]
        mgs = [m for m in mgs if all(m.get('gate', {}).get(f, True) for f in fam)]  # skip axes a micrograph can't be measured on
        for m in mgs:""")
open(p, 'w', encoding='utf-8').write(s)
p = 'app.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""    st.caption('Large dots = micrograph means; small dots = individual tiles (spatial sampling spread). The dotted box is the '""",
"""    gated = [m['parent'] for m in ref['micrographs'] + res['micrographs'] if not all(m['gate'].get(f, True) for f in (KPIS[kx]['family'], KPIS[ky]['family']))]
    if gated:
        st.caption(f"Not plotted (validity gate failed for these KPIs): {', '.join(sorted(set(gated)))}")
    st.caption('Large dots = micrograph means; small dots = individual tiles (spatial sampling spread). The dotted box is the '""")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
