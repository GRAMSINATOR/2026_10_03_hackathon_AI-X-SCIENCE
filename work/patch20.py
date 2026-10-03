p = 'qc/hero.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""g+=`<rect x="${x0-60}" y="${sy(pr.band.hi)}" width="60" height="${sy(pr.band.lo)-sy(pr.band.hi)}" fill="url(#fl)"/><rect x="${x1}" y="${sy(pr.band.hi)}" width="60" height="${sy(pr.band.lo)-sy(pr.band.hi)}" fill="url(#fr)"/>`;""",
"""if(step>=3) g+=`<rect x="${x0-60}" y="${sy(pr.band.hi)}" width="60" height="${sy(pr.band.lo)-sy(pr.band.hi)}" fill="url(#fl)"/><rect x="${x1}" y="${sy(pr.band.hi)}" width="60" height="${sy(pr.band.lo)-sy(pr.band.hi)}" fill="url(#fr)"/>`;""")
s = s.replace("""g+=`<text x="${x0-58}" y="${sy(pr.band.lo)+12}" fill="#898781" font-size="10">unobserved</text>""",
"""if(step>=3) g+=`<text x="${x0-58}" y="${sy(pr.band.lo)+12}" fill="#898781" font-size="10">unobserved</text>""")
s = s.replace("""  if(run.open_left) g+=""", """  if(step>=3&&run.open_left) g+=""")
s = s.replace("""  if(run.open_right) g+=""", """  if(step>=3&&run.open_right) g+=""")
open(p, 'w', encoding='utf-8').write(s)
print(s.count('step>=3&&run.open'))
