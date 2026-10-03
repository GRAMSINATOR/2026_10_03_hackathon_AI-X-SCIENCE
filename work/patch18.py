p = 'qc/hero.py'; s = open(p, encoding='utf-8').read()
s = s.replace("const totalX=Math.max(...pr.tiles.map(t=>t.x0+t.width),1)+(pr.runs.length-1)*60;", "const totalX=Math.max(...pr.tiles.map(t=>t.x0+t.width),1);")
s = s.replace("""  off+=60; });""", """ });""")
s = s.replace("let off=0; pr.runs.forEach((run,i)=>{const pts=run.sx.map((x,j)=>`${sx(x+off)},${sy(run.smooth[j])}`).join(' ');",
              "const off=0; pr.runs.forEach((run,i)=>{const pts=run.sx.map((x,j)=>`${sx(x)},${sy(run.smooth[j])}`).join(' ');")
s = s.replace("let gx=0, last=null; pr.tiles.forEach(t=>{ if(last!==null && t.x0 < last-1){} const im=D.thumbs[t.key]; const xx=sx(t.x0+gx), ww=sx(t.x0+gx+t.width)-xx;",
              "pr.tiles.forEach(t=>{ const im=D.thumbs[t.key]; const xx=sx(t.x0), ww=sx(t.x0+t.width)-xx;")
s = s.replace("""  last=t.x0+t.width; });""", """ });""")
s = s.replace("const show=cols.filter(c=>c.measured||step>=3||true);", "const show=cols.filter(c=>c.measured||step>=3);")
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/pipeline.py'; s = open(p, encoding='utf-8').read()
s = s.replace("from . import explain, field, provenance, spatial, stats\n", "from . import explain, field, hero, provenance, spatial, stats\n")
s = s.replace("""    open(os.path.join(REPORTS, batch, 'report.md'), 'w', encoding='utf-8').write(explain.markdown_report(_clean(res), ref))""",
"""    open(os.path.join(REPORTS, batch, 'report.md'), 'w', encoding='utf-8').write(explain.markdown_report(_clean(res), ref))
    open(os.path.join(REPORTS, batch, 'evidence_field.html'), 'w', encoding='utf-8').write(hero.render(_clean(res['field']), ref['name']))""")
open(p, 'w', encoding='utf-8').write(s)
print('ok', s.count('evidence_field'))
