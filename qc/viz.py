"""Visual layer: provenance mosaic, segmentation overlays, material-state map, KPI deviation heatmap."""
import json
import os

import numpy as np
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont

from .features import CACHE
from .stats import KPIS, den, qz

# Reference palette (dataviz skill): categorical slots 1-3 validate all-pairs; status colours carry icon + label.
ROLE = {'baseline': '#2a78d6', 'batch': '#eb6834', 'other': '#1baf7a'}
STATUS = {'in': ('#0ca30c', '✓', 'in family'), 'deviant': ('#fab219', '!', 'outside 95%'),
          'out': ('#d03b3b', '✕', 'outside 99%'), 'not measurable': ('#898781', '?', 'not measurable')}
VERDICT = {'ACCEPT': ('#0ca30c', '✓'), 'INVESTIGATE': ('#fab219', '!'), 'REJECT': ('#d03b3b', '✕'), 'REFERENCE': ('#2a78d6', '◆')}
PHASE_RGB = {0: (42, 120, 214), 2: (235, 104, 52)}   # pore = blue, high-Z additive = orange
INK, INK2, MUTED, GRID, SURFACE = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#fcfcfb'


def record(key):
    return json.load(open(os.path.join(CACHE, key + '.json')))


def thumb(key, det='BSE'):
    p = os.path.join(CACHE, f'{key}_{det}.jpg')
    return Image.open(p).convert('L') if os.path.exists(p) else None


def overlay(key, det='BSE', alpha=0.45, phases=(0, 2)):
    g = thumb(key, det)
    lab = np.array(Image.open(os.path.join(CACHE, key + '_lab.png')))
    rgb = np.stack([np.array(g)] * 3, -1).astype(np.float32)
    h, w = min(rgb.shape[0], lab.shape[0]), min(rgb.shape[1], lab.shape[1])
    rgb, lab = rgb[:h, :w], lab[:h, :w]
    for ph in phases:
        m = lab == ph
        rgb[m] = (1 - alpha) * rgb[m] + alpha * np.array(PHASE_RGB[ph], np.float32)
    return Image.fromarray(rgb.clip(0, 255).astype(np.uint8))


def _font(size):
    for f in ('segoeui.ttf', 'arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def mosaic(chains, batch, ref_name, statuses=None, row_h=96, gap=26, label_w=150):
    """Stitched parent micrographs; tile border colour = which batch folder the tile came from."""
    statuses = statuses or {}
    f, fs = _font(15), _font(12)
    rows = []
    for pid, order in chains.items():
        tiles = []
        for k in order:
            if k is None:
                tiles.append(None)
                continue
            im = thumb(k)
            s = row_h / im.height
            tiles.append((k, im.resize((max(1, int(im.width * s)), row_h))))
        rows.append((pid, tiles))
    W = label_w + max(sum((t[1].width if t else gap) for t in tiles) + 4 * len(tiles) for _, tiles in rows) + 10
    H = len(rows) * (row_h + 40) + 10
    canvas = Image.new('RGB', (W, H), SURFACE)
    d = ImageDraw.Draw(canvas)
    for i, (pid, tiles) in enumerate(rows):
        y = 8 + i * (row_h + 40)
        st = statuses.get(pid)
        d.text((8, y + row_h / 2 - 18), pid, fill=INK, font=f)
        if st:
            c, _, lab = STATUS[st]
            d.ellipse([8, y + row_h / 2 + 5, 18, y + row_h / 2 + 15], fill=c)
            d.text((23, y + row_h / 2 + 2), lab, fill=INK2, font=fs)
        x = label_w
        for t in tiles:
            if t is None:
                d.line([(x + 4, y + row_h / 2), (x + gap - 4, y + row_h / 2)], fill=MUTED, width=2)
                d.text((x + 2, y + row_h / 2 + 4), 'gap', fill=MUTED, font=fs)
                x += gap
                continue
            k, im = t
            b = k.split('__')[0]
            col = ROLE['baseline'] if b == ref_name else ROLE['batch'] if b == batch else ROLE['other']
            canvas.paste(im, (x + 2, y + 2))
            d.rectangle([x, y, x + im.width + 3, y + row_h + 3], outline=col, width=3)
            d.text((x + 4, y + row_h + 6), f"{k.split('__')[1]} · {b.replace('Batch_', 'B')}", fill=INK2, font=fs)
            x += im.width + 4
    return canvas


def _hover_kpis(kp):
    return '<br>'.join(f"{v['label']}: {kp[k] * v['scale']:.3g} {v['unit']}" for k, v in KPIS.items() if kp.get(k) is not None)


def state_map(ref, res, kx='additive_density', ky='additive_d50_um', m_band=3):
    fig = go.Figure()
    Rx, Ry = ref['kpi'][kx], ref['kpi'][ky]
    sx, sy = KPIS[kx]['scale'], KPIS[ky]['scale']
    hx, hy = qz(Rx, m_band)[0] * den(Rx, m_band), qz(Ry, m_band)[0] * den(Ry, m_band)
    fig.add_shape(type='rect', x0=(Rx['mean'] - hx) * sx, x1=(Rx['mean'] + hx) * sx, y0=(Ry['mean'] - hy) * sy,
                  y1=(Ry['mean'] + hy) * sy, fillcolor='rgba(42,120,214,0.10)', line=dict(color='rgba(42,120,214,0.6)', width=1, dash='dot'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name=f'approved 95% envelope ({m_band}-tile micrograph)',
                             marker=dict(symbol='square', size=12, color='rgba(42,120,214,0.18)', line=dict(color='rgba(42,120,214,0.6)', width=1))))
    groups = [('baseline', ref['micrographs'], ref['name'])]
    if res['batch'] != ref['name']:
        groups.append(('batch', res['micrographs'], res['batch']))
    fam = {KPIS[kx]['family'], KPIS[ky]['family']}
    for role, mgs, name in groups:
        col = ROLE[role]
        mgs = [m for m in mgs if all(m.get('gate', {}).get(f, True) for f in fam)]  # skip axes a micrograph can't be measured on
        for m in mgs:
            tx = [t.get(kx) for t in m['tile_kpi'].values()]
            ty = [t.get(ky) for t in m['tile_kpi'].values()]
            for a, b in zip(tx, ty):
                if a is None or b is None:
                    continue
                fig.add_trace(go.Scatter(x=[m['kpi'][kx] * sx, a * sx], y=[m['kpi'][ky] * sy, b * sy], mode='lines',
                                         line=dict(color=col, width=1), opacity=0.35, hoverinfo='skip', showlegend=False))
            fig.add_trace(go.Scatter(x=[a * sx for a in tx if a is not None], y=[b * sy for b in ty if b is not None], mode='markers',
                                     marker=dict(color=col, size=6, opacity=0.45), showlegend=False,
                                     text=[f"tile {f}" for f in m['tile_kpi']], hovertemplate='%{text}<extra></extra>'))
        xs = [m['kpi'][kx] * sx if m['kpi'].get(kx) is not None else None for m in mgs]
        ys = [m['kpi'][ky] * sy if m['kpi'].get(ky) is not None else None for m in mgs]
        lab = []
        for m in mgs:
            st = m.get('status')
            lab.append(f"{m['parent']} {STATUS[st][1]}" if role == 'batch' and st in ('deviant', 'out') else '')
        hov = [f"<b>{m['parent']}</b> ({name}, {m['n_tiles']} tiles)<br>{_hover_kpis(m['kpi'])}" for m in mgs]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode='markers+text', name=f"{name} micrographs", text=lab, textposition='top center',
                                 textfont=dict(color=INK, size=12), marker=dict(color=col, size=13, line=dict(color=SURFACE, width=2)),
                                 hovertext=hov, hoverinfo='text'))
    fig.update_layout(template='plotly_white', height=520, margin=dict(l=60, r=20, t=30, b=60), legend=dict(orientation='h', y=1.08),
                      xaxis_title=f"{KPIS[kx]['label']} ({KPIS[kx]['unit']})", yaxis_title=f"{KPIS[ky]['label']} ({KPIS[ky]['unit']})",
                      plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, font=dict(color=INK2))
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def deviation_heatmap(res):
    mgs = res['micrographs']
    keys = list(KPIS)
    z, txt, hov = [], [], []
    for m in mgs:
        row, trow, hrow = [], [], []
        for k in keys:
            s = m['score'][k]
            t = s.get('t')
            row.append(None if t is None else float(np.clip(t, -8, 8)))
            icon = STATUS[s['status']][1]
            val = s.get('value')
            trow.append(f"{icon} {val * KPIS[k]['scale']:.3g}" if val is not None else icon)
            hrow.append(f"<b>{m['parent']}</b> – {KPIS[k]['label']}<br>value {val * KPIS[k]['scale']:.3g} {KPIS[k]['unit']}"
                        f"<br>t = {t:+.1f} ({STATUS[s['status']][2]})<br>tiles beyond 95%: {s.get('tiles_beyond95')}/{s.get('n_tiles')}"
                        if t is not None else f"<b>{m['parent']}</b> – {KPIS[k]['label']}: not measurable (validity gate)")
        z.append(row)
        txt.append(trow)
        hov.append(hrow)
    fig = go.Figure(go.Heatmap(z=z, x=[KPIS[k]['short'] for k in keys], y=[f"{m['parent']} ({m['n_tiles']}t)" for m in mgs],
                               text=txt, texttemplate='%{text}', hovertext=hov, hoverinfo='text', zmin=-8, zmax=8, xgap=2, ygap=2,
                               colorscale=[[0, '#2a78d6'], [0.5, '#f0efec'], [1, '#e34948']],
                               colorbar=dict(title='t vs approved', tickvals=[-8, -4, 0, 4, 8])))
    fig.update_layout(template='plotly_white', height=90 + 46 * len(mgs), margin=dict(l=10, r=10, t=10, b=10),
                      plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, font=dict(color=INK2))
    fig.update_xaxes(side='top')
    fig.update_yaxes(autorange='reversed')
    return fig
