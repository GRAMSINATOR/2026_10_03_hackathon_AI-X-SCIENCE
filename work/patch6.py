import re
p = 'qc/stats.py'; s = open(p, encoding='utf-8').read()
for k, short in [('additive_area_frac', 'Additive area'), ('additive_d50_um', 'Additive D50'), ('additive_density', 'Additive density'),
                 ('porosity', 'Porosity'), ('pore_size_um', 'Pore size'), ('solid_chord_x_um', 'Solid chord (x)')]:
    s = s.replace(f"    '{k}': dict(label=", f"    '{k}': dict(short='{short}', label=", 1)
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/explain.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""        s += ' Deviating: ' + '; '.join(f"{t['parent']} – {', '.join(t['interpretation']) or 'see KPIs'}" for t in flagged) + '.'""",
"""        main = lambda t: next((i for i in t['interpretation'] if not i.startswith(('caveat', 'acquisition check'))), 'see KPIs')
        s += ' Deviating: ' + '; '.join(f"{t['parent']} ({t['status']}) – {main(t)}" for t in flagged) + '.'""")
open(p, 'w', encoding='utf-8').write(s)

p = 'qc/viz.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""    fig.add_annotation(x=(Rx['mean'] + hx) * sx, y=(Ry['mean'] + hy) * sy, text=f'approved 95% envelope ({m_band} tiles)',
                       showarrow=False, xanchor='right', yanchor='bottom', font=dict(color=INK2, size=11))""",
"""    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name=f'approved 95% envelope ({m_band}-tile micrograph)',
                             marker=dict(symbol='square', size=12, color='rgba(42,120,214,0.18)', line=dict(color='rgba(42,120,214,0.6)', width=1))))""")
s = s.replace("""            lab.append(f"{m['parent']} {STATUS[st][1]}" if role == 'batch' and st in ('deviant', 'out') else m['parent'] if role == 'batch' else '')""",
"""            lab.append(f"{m['parent']} {STATUS[st][1]}" if role == 'batch' and st in ('deviant', 'out') else '')""")
s = s.replace("""    fig = go.Figure(go.Heatmap(z=z, x=[KPIS[k]['label'] for k in keys],""", """    fig = go.Figure(go.Heatmap(z=z, x=[KPIS[k]['short'] for k in keys],""")
open(p, 'w', encoding='utf-8').write(s)

p = 'app.py'; s = open(p, encoding='utf-8').read()
s = s.replace('use_container_width=True', "width='stretch'")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
