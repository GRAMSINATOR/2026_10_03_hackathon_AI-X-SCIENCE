"""Instrument renderer host: injects the contract (epistemic-field/1) and image assets into the built React Three Fiber
renderer (renderer/dist/index.html). No scientific logic here or in the renderer; see renderer/src/model/*.js."""
import base64
import io
import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(__file__))
DIST = os.path.join(ROOT, 'renderer', 'dist', 'index.html')
PLACEHOLDER = '"__EVIDENCE_PAYLOAD__"'


def _uri(im, fmt):
    b = io.BytesIO()
    im.save(b, fmt, **({'quality': 78} if fmt == 'JPEG' else {'optimize': True}))
    return f"data:image/{'jpeg' if fmt == 'JPEG' else 'png'};base64," + base64.b64encode(b.getvalue()).decode()


def assets_for(field, asset_dir):
    """BSE image + registered segmentation per field, at ~0.2 µm/px. Accepts engine cache (×4, *_lab.png)
    or fixture assets (×8, *_seg.png)."""
    out = {}
    for f in field['provenance']['fields']:
        fid = f['id']
        bse, seg8, lab4 = (os.path.join(asset_dir, f'{fid}{s}') for s in ('_BSE.jpg', '_seg.png', '_lab.png'))
        if not os.path.exists(bse):
            continue
        im = Image.open(bse).convert('L')
        fixture_scale = os.path.exists(seg8)
        if not fixture_scale:
            im = im.resize((im.width // 2, im.height // 2))
        a = dict(bse=_uri(im, 'JPEG'), width_um=f['width_um'], height_um=f['height_um'],
                 image_px_um=f['width_um'] / im.width)
        if fixture_scale or os.path.exists(lab4):
            L = Image.open(seg8 if fixture_scale else lab4)
            if not fixture_scale:
                L = L.resize((L.width // 2, L.height // 2), Image.NEAREST)
            a['seg'] = _uri(L.convert('L'), 'PNG')
            a['seg_encoding'] = {'0': 'pore', '1': 'matrix', '2': 'high_z'}
        out[fid] = a
    return out


def render(field, asset_dir=None, dist=DIST, images=True, brief=None):
    """brief: the governed decision brief (decision-brief/1), built by the caller from the same field with the brief
    module; the host never derives it, so it stays free of scientific logic."""
    """images=False (public mode): no micrograph, segmentation or thumbnail is read or embedded. The payload carries
    the numerical field only (profiles, extents, rims, actions) and the renderer states that imagery is withheld."""
    if field.get('schema_version') != 'epistemic-field/1':
        raise ValueError('instrument renderer expects epistemic-field/1')
    if not os.path.exists(dist):
        raise FileNotFoundError(f'{dist} missing: run `npm run build` in renderer/')
    html = open(dist, encoding='utf-8').read()
    if PLACEHOLDER not in html:
        raise ValueError('renderer build has no payload placeholder')
    if images and asset_dir is None:   # same default as the engine cache, without importing scientific modules
        asset_dir = os.environ.get('QC_CACHE', os.path.join(ROOT, 'cache', 'fields'))
    assets = assets_for(field, asset_dir) if images else {}
    if brief is not None and brief['source']['batch'] != field['context']['batch']:
        raise ValueError('brief and field describe different batches')
    payload = json.dumps(dict(field=field, assets=assets, imagery=bool(images), brief=brief), separators=(',', ':')).replace('</', '<\\/')
    return html.replace(PLACEHOLDER, payload, 1)
