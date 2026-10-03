p = 'qc/hero.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""  if(step>=2){const w=1+3*cell.reducible_share; st+=`box-shadow:inset 0 0 0 ${w.toFixed(1)}px ${cell.dominant=='spatial'?'var(--spatial)':'var(--base)'}${cell.deviating&&cell.survives?','+'0 0 16px 2px '+rgba(cell.dir,.55):''};`}""",
"""  if(step>=2){const strong=cell.deviating; const w=strong?1.5+3*cell.reducible_share:1+1.5*cell.reducible_share; const hue=cell.dominant=='spatial'?'25,158,112':'144,133,233';
   st+=`box-shadow:inset 0 0 0 ${w.toFixed(1)}px rgba(${hue},${strong?1:.45})${cell.deviating&&cell.survives?','+'0 0 16px 2px '+rgba(cell.dir,.55):''};`}""")
s = s.replace("""g+=`<text x="${x0-64}" y="${sy(pr.band.hi)-3}" fill="#898781" font-size="10">unobserved</text><text x="${x1+6}" y="${sy(pr.band.hi)-3}" fill="#898781" font-size="10">unobserved</text>`;""",
"""g+=`<text x="${x0-58}" y="${sy(pr.band.lo)+12}" fill="#898781" font-size="10">unobserved</text><text x="${x1+4}" y="${sy(pr.band.lo)+12}" fill="#898781" font-size="10">unobserved</text>`;
 g+=`<text x="4" y="11" fill="#898781" font-size="10">${c.short} (${c.unit})</text>`;""")
open(p, 'w', encoding='utf-8').write(s)

p = 'app.py'; s = open(p, encoding='utf-8').read()
s = s.replace("import streamlit as st\n", "import streamlit as st\nimport streamlit.components.v1 as components\n")
s = s.replace("""# ---------------- verdict banner""", """# ---------------- hero: Evidence Field (the uncertainty field as a control surface)
hero_path = os.path.join('reports', batch, 'evidence_field.html')
if os.path.exists(hero_path) and d['verdict'] != 'REFERENCE':
    components.html(open(hero_path, encoding='utf-8').read(), height=1290, scrolling=True)
    st.caption('Evidence Field: every visual state is a rule over the uncertainty field (docs/FIELD_MODEL.md). '
               'The QC proof layer below holds the primitive statistics.')
    st.markdown('---')
    st.markdown('### QC proof layer')

# ---------------- verdict banner""")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
