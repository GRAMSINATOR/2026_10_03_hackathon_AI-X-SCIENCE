"""Polaron Track 4 – interpretable, uncertainty-aware SEM batch QC.   Run:  streamlit run app.py"""
import json
import os
import subprocess
import sys

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from qc import provenance, viz
from qc.pipeline import REF_PATH, known_records
from qc.stats import KPIS, SECONDARY

st.set_page_config(page_title='Electrode batch QC · Polaron Track 4', layout='wide', page_icon='🔬')
st.markdown("""<style>
.verdict {border-radius: 10px; padding: 18px 22px; margin-bottom: 8px; color: #0b0b0b; background: #fcfcfb; border: 1px solid rgba(11,11,11,.10);}
.verdict h1 {margin: 0; font-size: 2.1rem;} .verdict p {margin: 4px 0 0 0; color: #52514e;}
.chip {display:inline-block; padding: 2px 8px; border-radius: 6px; font-size: .85rem; margin-right: 6px; border: 1px solid rgba(11,11,11,.12);}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load_json(path, mtime):
    return json.load(open(path))


@st.cache_data
def all_chains(mtime):
    return provenance.build(known_records(), ref['name'])


if not os.path.exists(REF_PATH):
    st.error('No reference yet. Run:  python -m qc reference data/Batch_1 --noise-from data/Batch_2 data/Batch_3')
    st.stop()
ref = load_json(REF_PATH, os.path.getmtime(REF_PATH))

# ---------------- sidebar
st.sidebar.title('Electrode batch QC')
st.sidebar.caption(f"Approved reference: **{ref['name']}** · {len(ref['micrographs'])} micrographs · {ref['px_nm']:.1f} nm/px")
batches = sorted(d for d in os.listdir('data') if os.path.isdir(os.path.join('data', d)))
default = next((i for i, b in reversed(list(enumerate(batches))) if b != ref['name']), 0)
batch = st.sidebar.selectbox('Batch to assess', batches, index=default)
res_path = os.path.join('reports', batch, 'result.json')
if st.sidebar.button('Run / refresh assessment', type='primary') or not os.path.exists(res_path):
    with st.spinner(f'Segmenting and measuring {batch} …'):
        out = subprocess.run([sys.executable, '-m', 'qc', 'assess', os.path.join('data', batch)], capture_output=True, text=True)
    if out.returncode != 0:
        st.sidebar.error(out.stderr[-2000:])
        st.stop()
    st.cache_data.clear()
res = load_json(res_path, os.path.getmtime(res_path))
d = res['decision']
st.sidebar.markdown('---')
st.sidebar.markdown('**Colour key**  \n'
                    f"<span class='chip' style='border-color:{viz.ROLE['baseline']}'>■ approved baseline</span>"
                    f"<span class='chip' style='border-color:{viz.ROLE['batch']}'>■ this batch</span>"
                    f"<span class='chip' style='border-color:{viz.ROLE['other']}'>■ other batches</span>", unsafe_allow_html=True)
st.sidebar.markdown('Overlays: <span style="color:#2a78d6">■ pores</span> · <span style="color:#eb6834">■ high-Z additive</span>',
                    unsafe_allow_html=True)

# ---------------- hero: Evidence Field (the uncertainty field as a control surface)
hero_path = os.path.join('reports', batch, 'evidence_field.html')
if os.path.exists(hero_path) and d['verdict'] != 'REFERENCE':
    components.html(open(hero_path, encoding='utf-8').read(), height=1130, scrolling=True)
    st.caption('V1 exploratory renderer of the uncertainty-field contract epistemic-field/1 (docs/REPRESENTATION_CONTRACT.md). '
               'The QC proof layer below holds the primitive statistics.')
    st.markdown('---')
    st.markdown('### QC proof layer')

# ---------------- verdict banner
col, icon = viz.VERDICT[d['verdict']]
st.markdown(f"""<div class='verdict' style='border-left: 10px solid {col}'>
<h1>{icon} {d['verdict']} <span style='font-size:1.1rem;color:#52514e;font-weight:400'>— {batch}</span></h1>
<p>{res['summary']}</p></div>""", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric('Independent micrographs', d.get('n_independent', d['n_micrographs']), help='Fields are tiles of parent micrographs; the micrograph is the statistical unit. Micrographs continuous with approved baseline sections are not counted.')
c2.metric('Fields (tiles)', res['n_fields'])
c3.metric('Micrographs outside 99% envelope', d['d99'], help='on robust KPIs (additive phase)')
c4.metric('Batch p-value', f"{d['p_batch']:.3f}" if d['verdict'] != 'REFERENCE' else '—',
          help='Probability that a batch drawn from the approved population would look at least this deviant '
               '(parametric bootstrap with small-baseline uncertainty).')
for r in d['reasons']:
    st.markdown(f'- {r}')
if res.get('actions'):
    with st.expander('Recommended actions', expanded=d['verdict'] != 'ACCEPT'):
        for a in res['actions']:
            st.markdown(f'- {a}')

tabs = st.tabs(['Why: evidence', 'Material-state map', 'Provenance', 'Field explorer', 'Method & uncertainty'])

# ---------------- evidence
with tabs[0]:
    st.subheader('KPI deviation by micrograph')
    st.caption('Cell = KPI value with status icon; colour = t versus the approved envelope (blue below, red above). '
               '✓ in family · ! outside 95% · ✕ outside 99% · ? not measurable (validity gate). Hover for details.')
    st.plotly_chart(viz.deviation_heatmap(res), width='stretch')
    flagged = [t for t in res['explanations'] if t['status'] in ('deviant', 'out') or t['gate']]
    st.subheader('Flagged micrographs' if flagged else 'No micrograph flagged')
    mg_by = {m['parent']: m for m in res['micrographs']}
    for t in flagged:
        stc, sti, stl = viz.STATUS[t['status']]
        with st.expander(f"{sti} {t['headline']} — {stl}", expanded=True):
            a, b = st.columns([3, 2])
            with a:
                for f in t['findings']:
                    st.markdown(f'- {f}')
                if t['interpretation']:
                    st.markdown('**Interpretation**')
                    for i in t['interpretation']:
                        st.markdown(f'- {i}')
                if t['risks']:
                    st.markdown('**Downstream exposure** *(literature-grounded hypothesis, not a measured prediction)*')
                    for r in t['risks']:
                        st.markdown(f'- {r}')
                if t['acquisition']:
                    st.markdown('**Acquisition differs from baseline:** ' + '; '.join(t['acquisition']))
                for g in t['gate']:
                    st.warning(g)
                if t['links']:
                    st.info(f"Same parent micrograph also appears in: {', '.join(t['links'])}")
            with b:
                m = mg_by[t['parent']]
                worst = max(KPIS, key=lambda k: abs(m['score'][k]['t'] or 0))
                fid = max(m['tile_kpi'], key=lambda f: abs((m['tile_kpi'][f].get(worst) or 0) - ref['kpi'][worst]['mean']))
                st.image(viz.overlay(f"{res['batch']}__{fid}"), caption=f'{fid}: BSE with segmentation (most deviating tile)')

# ---------------- state map
with tabs[1]:
    keys = list(KPIS)
    a, b = st.columns(2)
    kx = a.selectbox('x axis', keys, index=keys.index('additive_density'), format_func=lambda k: KPIS[k]['label'])
    ky = b.selectbox('y axis', keys, index=keys.index('additive_d50_um'), format_func=lambda k: KPIS[k]['label'])
    st.plotly_chart(viz.state_map(ref, res, kx, ky), width='stretch')
    gated = [m['parent'] for m in ref['micrographs'] + res['micrographs'] if not all(m['gate'].get(f, True) for f in (KPIS[kx]['family'], KPIS[ky]['family']))]
    if gated:
        st.caption(f"Not plotted (validity gate failed for these KPIs): {', '.join(sorted(set(gated)))}")
    st.caption('Large dots = micrograph means; small dots = individual tiles (spatial sampling spread). The dotted box is the '
               'approved 95% prediction envelope for a 3-tile micrograph (between-micrograph + tile-sampling + baseline-'
               'estimation uncertainty). Pseudotime/trajectory structure was tested and is not supported by the data, so '
               'none is drawn.')

# ---------------- provenance
with tabs[2]:
    st.subheader('Fields are tiles of larger micrographs')
    st.markdown('Each row is one parent micrograph rebuilt from abutting tiles (edge continuity of BSE pixels). '
                'Border colour = batch folder the tile came from. Several micrographs span **multiple batch folders**, so '
                'tiles are not independent samples: all statistics are computed per micrograph.')
    show_all = st.checkbox('Show every known micrograph', value=False)
    prov = all_chains(max(os.path.getmtime(os.path.join('cache', 'fields', f)) for f in os.listdir('cache/fields')))
    chains = prov['chains'] if show_all else res['chains']
    statuses = {m['parent']: m['status'] for m in res['micrographs']}
    st.image(viz.mosaic(chains, res['batch'], ref['name'], statuses), width='stretch')
    if res['links']:
        st.caption('Edge links (normalised cross-correlation of abutting edges; non-neighbours score ≈0 ± 0.15): ' +
                   ', '.join(f"{l['left'].split('__')[1]}→{l['right'].split('__')[1]} ({l['ncc']:.2f})" for l in res['links']))

# ---------------- field explorer
with tabs[3]:
    mg = {m['parent']: m for m in res['micrographs']}
    a, b, c, e = st.columns([1, 1, 1, 1])
    pid = a.selectbox('Micrograph', list(mg), format_func=lambda p: f"{viz.STATUS[mg[p]['status']][1]} {p}")
    fid = b.selectbox('Field', mg[pid]['fids'])
    key = f"{res['batch']}__{fid}"
    rec = viz.record(key)
    dets = ['BSE'] + [x for x in ('SE2', 'InLens') if os.path.exists(os.path.join('cache', 'fields', f'{key}_{x}.jpg'))]
    det = c.radio('Detector', dets, horizontal=True)
    ov = e.checkbox('Segmentation overlay', value=True)
    st.image(viz.overlay(key, det) if ov else viz.thumb(key, det), width='stretch',
             caption=f"{fid} · {rec['detectors'].get(det, det)} · {rec['W'] * rec['px_nm'] / 1000:.0f} × {rec['H'] * rec['px_nm'] / 1000:.0f} µm · "
                     f"{rec['px_nm']:.1f} nm/px (display downsampled 4×)")
    rows = []
    for k, meta in KPIS.items():
        R = ref['kpi'][k]
        lo, hi = R['pi95_m1']
        v = rec['kpi'].get(k)
        rows.append({'KPI': meta['label'], 'value': None if v is None else round(v * meta['scale'], 3), 'unit': meta['unit'],
                     'approved 95% (single field)': f"{lo * meta['scale']:.3g} – {hi * meta['scale']:.3g}",
                     'robustness': meta['cls']})
    for k, meta in SECONDARY.items():
        v = rec['kpi'].get(k)
        if v is not None:
            rows.append({'KPI': meta['label'], 'value': round(v * meta['scale'], 3), 'unit': meta['unit'],
                         'approved 95% (single field)': '', 'robustness': 'advisory'})
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
    st.caption('Acquisition fingerprint: ' + ', '.join(f"{k} {v:.3g}" for k, v in rec['acq'].items() if isinstance(v, (int, float))))

# ---------------- method
with tabs[4]:
    st.subheader('Approved reference (micrograph-level)')
    rows = []
    for k, meta in KPIS.items():
        R = ref['kpi'][k]
        rb = ref.get('robustness', {}).get(k, {})
        s = meta['scale']
        rows.append({'KPI': meta['label'], 'robustness class': meta['cls'], 'approved mean': round(R['mean'] * s, 4),
                     'between-micrograph SD': round(R['sd_between'] * s, 4), 'tile-sampling SD': round(R['sd_within_tile'] * s, 4),
                     'n micrographs': R['n'], 'min. detectable change (95%, 3 tiles)': round(R['mdc95'] * s, 4),
                     'worst acquisition effect': f"{rb.get('worst', '')}: {rb.get('max_abs', 0) * s:.3g}" if rb else '',
                     'excluded (gate)': ', '.join(R['excluded'])})
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
    st.markdown("""
**Decision rule (fixed before seeing the unseen batch).** Unit = parent micrograph. For each KPI the micrograph mean is
compared with the approved micrographs via a prediction interval with two variance levels (between-micrograph
material spread from the baseline; tile-sampling noise pooled from replicate tiles). Envelope thresholds are calibrated
by simulation so their coverage is real. The batch p-value is the probability that an approved-population batch of the
same size looks at least as deviant, combining two simulated tests (Bonferroni): *severity* (the most extreme micrograph,
|z| relative to its 99% threshold) and *count* (micrographs outside 95%), re-estimating the small baseline in every draw.
**REJECT**: p < 0.05 and ≥1 tile-consistent out-of-envelope micrograph. **INVESTIGATE**: p < 0.20, any micrograph outside
99%, a moderate-robustness KPI outside 99%, a failed validity gate, or < 3 micrographs. **ACCEPT**: otherwise.

**Validity gate.** The high-Z phase is only measured where its contrast-to-noise against the matrix is ≥ 4; a different pixel
size disables size KPIs. Robust KPIs moved ≤ 0.5 tile-sampling SD under synthetic brightness/contrast/gamma/blur/noise/
stretch/black-level/resolution changes; porosity and chord lengths are acquisition-sensitive and can only trigger INVESTIGATE.

**What is not claimed.** Chemistry of the bright phase (no EDS), 3-D sizes or absolute porosity (2-D sections of
non-infiltrated pores), process origin of cracks (may be sample preparation), any tool-wear prediction, any material
"trajectory" (pseudotime was tested: the leading latent axis changed with detector/normalisation and tracked black level).""")
    sens = 'cache/sens/summary.json'
    if os.path.exists(sens):
        st.subheader('Verdict sensitivity to analysis choices')
        S = json.load(open(sens))
        st.dataframe(pd.DataFrame([{'variant': v, **{f'{b} verdict': f"{x['verdict']} (p={x['p']:.3f})" for b, x in r.items()},
                                    **{f'{b} flagged': ', '.join(f'{k}:{s}' for k, s in x['flagged'].items()) for b, x in r.items()}}
                                   for v, r in S.items()]), width='stretch', hide_index=True)
    st.subheader('Baseline self-audit (leave-one-micrograph-out)')
    st.dataframe(pd.DataFrame(ref['self_audit']), width='stretch', hide_index=True)
    st.caption(f"False-alarm calibration for this batch size: P(any micrograph outside 99% | approved) = {d['null'].get('p_any99', 0):.2f}, "
               f"P(any outside 95%) = {d['null'].get('p_any95', 0):.2f} — why a single excursion only triggers INVESTIGATE.")
