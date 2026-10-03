p = 'qc/contract.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""        for r in o['rims']:
            if r not in R:
                bad.append(f"observation {o['id']}: unknown rim {r}")""", """        for r in o['rims']:
            if r not in R:
                bad.append(f"observation {o['id']}: unknown rim {r}")
        if o['entity'] in E and not set(o['per_field']) <= set(E[o['entity']]['fields']):
            bad.append(f"observation {o['id']}: per_field keys are not fields of its entity")""")
open(p, 'w', encoding='utf-8').write(s)
