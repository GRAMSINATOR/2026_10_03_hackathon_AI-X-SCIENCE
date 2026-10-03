p = 'qc/stats.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""        m['leverage'] = dict(verdict_without=sub['verdict'], p_without=sub['p_batch'], flips=sub['verdict'] != d['verdict'])""",
"""        why = 'batch would fall below 3 independent micrographs' if sub['n_independent'] < 3 else 'carries the decisive evidence'
        m['leverage'] = dict(verdict_without=sub['verdict'], p_without=sub['p_batch'], flips=sub['verdict'] != d['verdict'], why=why)""")
open(p, 'w', encoding='utf-8').write(s)
p = 'qc/field.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""                    (f"; verdict rests on {', '.join(pivotal)}" if pivotal else '') +""",
"""                    (f"; verdict rests on {', '.join(pivotal)} ({rows[[r['parent'] for r in rows].index(pivotal[0])]['leverage']['why']})" if pivotal else '') +""")
s = s.replace("""                trigger=[f"verdict flips without {pid} ({d['verdict']} → {lev['verdict_without']}, p = {lev['p_without']:.2f})",""",
"""                trigger=[f"verdict flips without {pid} ({d['verdict']} → {lev['verdict_without']}, p = {lev['p_without']:.2f}): it {lev['why']}",""")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
