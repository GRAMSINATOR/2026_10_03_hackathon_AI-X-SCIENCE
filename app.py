"""Polaron Track 4 – interpretable, uncertainty-aware SEM batch QC.   Run:  streamlit run app.py"""
import json
import os
import subprocess
import sys

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from qc import brief, frontier, instrument, provenance, viz
from qc.features import CACHE
from qc.pipeline import REF_PATH, REPORTS, known_records
from qc.stats import KPIS, SECONDARY

# Modes. QC_PUBLIC=1: derived results only (no data/, never runs the pipeline). QC_PUBLIC_IMAGES: micrograph-derived
# imagery (micrographs, segmentation, thumbnails, mosaics, embedded image payloads); off by default in public mode.
# Paths follow QC_REF / QC_REPORTS / QC_CACHE (and QC_DATA for raw folders). See docs/PUBLIC_MODE.md.
PUBLIC = os.environ.get('QC_PUBLIC') == '1'
IMAGES = os.environ.get('QC_PUBLIC_IMAGES', '0' if PUBLIC else '1') == '1'
DATA = os.environ.get('QC_DATA', 'data')
SENS = os.path.join(os.path.dirname(os.path.normpath(CACHE)), 'sens', 'summary.json')
PROV_MAP = os.path.join(REPORTS, 'provenance_map.json')
WITHHELD = 'Micrograph imagery withheld: this deployment shows derived numbers only.'

st.set_page_config(page_title='Electrode batch QC · Polaron Track 4', layout='wide', page_icon='🔬', initial_sidebar_state='collapsed')
# one surface with the instrument (theme in .streamlit/config.toml); no sidebar; a compact header row
st.markdown("""<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {display: none !important;}
.stApp, header[data-testid="stHeader"] {background: #e4e3df;}
header[data-testid="stHeader"] {height: 0; min-height: 0;}
[data-testid="stMainBlockContainer"], .block-container {padding: .55rem 1.1rem 1.2rem; max-width: 1940px;}
[data-testid="stMainBlockContainer"] > div > div > [data-testid="stHorizontalBlock"]:first-of-type {gap: .6rem; margin-bottom: -.4rem;}
[data-testid="stMainBlockContainer"] > div > div > [data-testid="stHorizontalBlock"]:first-of-type [data-baseweb="select"] > div
  {min-height: 30px; font-size: 12.5px; background: #dad9d4; border: 0; box-shadow: inset -1px 2px 4px rgba(40,36,30,.12);}
[data-testid="stMainBlockContainer"] > div > div > [data-testid="stHorizontalBlock"]:first-of-type p {font-size: 12px; color: #8b8880;}
iframe {border: 0;}
.verdict {border-radius: 10px; padding: 18px 22px; margin-bottom: 8px; color: #0b0b0b; background: #fcfcfb; border: 1px solid rgba(11,11,11,.10);}
.verdict h1 {margin: 0; font-size: 2.1rem;} .verdict p {margin: 4px 0 0 0; color: #52514e;}
.chip {display:inline-block; padding: 2px 8px; border-radius: 6px; font-size: .85rem; margin-right: 6px; border: 1px solid rgba(11,11,11,.12);}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load_json(path, mtime):
    return json.load(open(path))


@st.cache_data
def all_chains(mtime):
    """Every known parent micrograph as a tile chain. Prefers the exported map (derived numbers); recomputing needs the
    local engine cache (edge strips), which a public bundle does not contain."""
    if os.path.exists(PROV_MAP):
        parents = json.load(open(PROV_MAP))['parents']
        return {p: [k for run in v['runs'] for k in (run + [None])][:-1] for p, v in parents.items()}
    return provenance.build(known_records(), ref['name'])['chains']


def _runs(chain):
    """Split a tile chain (None = gap of unknown separation) into runs of abutting tiles."""
    runs = [[]]
    for k in chain:
        if k is None:
            runs.append([])
        else:
            runs[-1].append(k)
    return [r for r in runs if r]


@st.cache_data
def render_instrument(path, mtime, images, research=()):
    F = json.load(open(path, encoding='utf-8'))
    html = instrument.render(F, images=images, brief=brief.build(F))   # brief derived from the same contract
    return frontier.attach(html, REPORTS)   # + lab-level Marker Frontier (research/ bundles; `research` = cache key)


if not os.path.exists(REF_PATH):
    st.error('No approved reference found (QC_REF). ' + ('This derived bundle is incomplete.' if PUBLIC else
             'Run:  python -m qc reference data/Batch_1 --noise-from data/Batch_2 data/Batch_3'))
    st.stop()
ref = load_json(REF_PATH, os.path.getmtime(REF_PATH))

# ---------------- discreet control row (top left): batch, run, reference; dev-only controls behind a popover
# presentation mode by default; dev mode (QC_DEV=1 or ?dev=1) adds the renderer switch and the legacy colour key
DEV = os.environ.get('QC_DEV') == '1' or st.query_params.get('dev') == '1'
have_data = not PUBLIC and os.path.isdir(DATA)
reported = {b for b in (os.listdir(REPORTS) if os.path.isdir(REPORTS) else []) if os.path.exists(os.path.join(REPORTS, b, 'result.json'))}
raw = {b for b in os.listdir(DATA) if os.path.isdir(os.path.join(DATA, b))} if have_data else set()
batches = sorted(reported | raw)
if not batches:
    st.error('No assessed batches found (QC_REPORTS).')
    st.stop()
default = next((i for i, b in reversed(list(enumerate(batches))) if b != ref['name']), 0)
bar = st.columns([0.8, 0.62, 5.1, 0.4] if DEV else [0.8, 0.62, 5.5], vertical_alignment='center')
batch = bar[0].selectbox('Batch', batches, index=default, label_visibility='collapsed')
res_path = os.path.join(REPORTS, batch, 'result.json')
can_run = have_data and batch in raw
bar[2].caption(f"approved reference {ref['name']} · {len(ref['micrographs'])} micrographs · {ref['px_nm']:.1f} nm/px"
               + (' · public mode, derived results only' + ('' if IMAGES else ', no imagery') if PUBLIC else ''))
renderer = 'instrument'
if DEV:
    with bar[3].popover('dev'):
        # primary renderer (contract epistemic-field/1 -> renderer); legacy kept for parity checks
        renderer = st.radio('Renderer', ['instrument', 'legacy'] if IMAGES else ['instrument'], horizontal=True,
                            help='instrument = React Three Fiber Evidence Instrument; legacy = V1 exploratory HTML renderer '
                                 '(embeds imagery, so it is unavailable without imagery)')
        st.markdown('**Colour key (legacy)**  \n'
                    f"<span class='chip' style='border-color:{viz.ROLE['baseline']}'>■ approved baseline</span>"
                    f"<span class='chip' style='border-color:{viz.ROLE['batch']}'>■ this batch</span>"
                    f"<span class='chip' style='border-color:{viz.ROLE['other']}'>■ other batches</span>", unsafe_allow_html=True)
        st.markdown('Overlays: <span style="color:#2a78d6">■ pores</span> · <span style="color:#eb6834">■ high-Z additive</span>',
                    unsafe_allow_html=True)
# the pipeline runs only on an explicit click, never on page load
if can_run and bar[1].button('Run / refresh', type='tertiary', icon=':material/refresh:', help=f'Segment and measure {batch} again'):
    with st.spinner(f'Segmenting and measuring {batch} …'):
        out = subprocess.run([sys.executable, '-m', 'qc', 'assess', os.path.join(DATA, batch)], capture_output=True, text=True)
    if out.returncode != 0:
        st.error(out.stderr[-2000:])
        st.stop()
    st.cache_data.clear()
if not os.path.exists(res_path):
    st.info(f'No assessment for {batch} yet. ' + ('Click "Run / refresh" to measure it.' if can_run else
            'It is not part of this derived bundle.'))
    st.stop()
res = load_json(res_path, os.path.getmtime(res_path))
d = res['decision']
field_path = os.path.join(REPORTS, batch, 'field.json')
hero_path = os.path.join(REPORTS, batch, 'evidence_field.html')
view = None
if d['verdict'] != 'REFERENCE':
    if renderer == 'instrument' and os.path.exists(field_path) and os.path.exists(instrument.DIST):
        view = render_instrument(field_path, os.path.getmtime(field_path), IMAGES, frontier.signature(REPORTS))   # contract -> renderer, per mode
    elif renderer == 'legacy' and IMAGES and os.path.exists(hero_path):
        view = open(hero_path, encoding='utf-8').read()
if view:
    components.html(view, height=1900 if renderer == 'instrument' else 1130, scrolling=True)
    if DEV:
        st.caption('Renders only the uncertainty-field contract epistemic-field/1 (docs/REPRESENTATION_CONTRACT.md).')
    proof = st.expander('QC proof layer · primitive statistics', expanded=False)   # the instrument already carries the verdict
else:
    proof = st.container()
    # ---------------- verdict banner (only when no renderer view is available: the instrument carries the verdict itself)
    col, icon = viz.VERDICT[d['verdict']]
    st.markdown(f"""<div class='verdict' style='border-left: 10px solid {col}'>
<h1>{icon} {d['verdict']} <span style='font-size:1.1rem;color:#52514e;font-weight:400'>— {batch}</span></h1>
<p>{res['summary']}</p></div>""", unsafe_allow_html=True)
    for r in d['reasons']:
        st.markdown(f'- {r}')
c1, c2, c3, c4 = proof.columns(4)
c1.metric('Independent micrographs', d.get('n_independent', d['n_micrographs']), help='Fields are tiles of parent micrographs; the micrograph is the statistical unit. Micrographs continuous with approved baseline sections are not counted.')
c2.metric('Fields (tiles)', res['n_fields'])
c3.metric('Micrographs outside 99% envelope', d['d99'], help='on robust KPIs (additive phase)')
c4.metric('Batch p-value', f"{d['p_batch']:.3f}" if d['verdict'] != 'REFERENCE' else '—',
          help='Probability that a batch drawn from the approved population would look at least this deviant '
               '(parametric bootstrap with small-baseline uncertainty).')

tabs = proof.tabs(['Why: evidence', 'Material-state map', 'Provenance', 'Field explorer', 'Method & uncertainty'])

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
                if IMAGES:
                    st.image(viz.overlay(f"{res['batch']}__{fid}"), caption=f'{fid}: BSE with segmentation (most deviating tile)')
                else:
                    st.caption(f'Most deviating tile: {fid}. {WITHHELD}')

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
    stamps = [os.path.join(CACHE, f) for f in os.listdir(CACHE)] if os.path.isdir(CACHE) else []
    chains = all_chains(max([os.path.getmtime(p) for p in stamps + [PROV_MAP] if os.path.exists(p)], default=0)) if show_all else res['chains']
    statuses = {m['parent']: m['status'] for m in res['micrographs']}
    if IMAGES:
        st.image(viz.mosaic(chains, res['batch'], ref['name'], statuses), width='stretch')
    else:   # the same chains as numbers: parent, runs of abutting tiles (with their batch), status in this batch
        rows = []
        for pid, ch in chains.items():
            runs = ' | '.join(' → '.join(f"{k.split('__')[1]} ({k.split('__')[0].replace('Batch_', 'B')})" for k in run)
                              for run in _runs(ch))
            rows.append({'parent micrograph': pid, 'tiles (abutting runs; | = unknown separation)': runs,
                         'tiles': sum(k is not None for k in ch), 'status in this batch': statuses.get(pid, '—')})
        st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
        st.caption(WITHHELD + ' Full tile → parent map: provenance_map.csv / .json (python -m qc provenance).')
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
    size = f"{rec['W'] * rec['px_nm'] / 1000:.0f} × {rec['H'] * rec['px_nm'] / 1000:.0f} µm · {rec['px_nm']:.1f} nm/px"
    if IMAGES:
        dets = ['BSE'] + [x for x in ('SE2', 'InLens') if os.path.exists(os.path.join(CACHE, f'{key}_{x}.jpg'))]
        det = c.radio('Detector', dets, horizontal=True)
        ov = e.checkbox('Segmentation overlay', value=True)
        st.image(viz.overlay(key, det) if ov else viz.thumb(key, det), width='stretch',
                 caption=f"{fid} · {rec['detectors'].get(det, det)} · {size} (display downsampled 4×)")
    else:
        st.caption(f"{fid} · detectors {', '.join(rec['detectors'].values())} · {size}. {WITHHELD}")
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
    sens = SENS
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
