"""Derived public bundle (issues #3, #4): everything the dashboard needs in public mode, nothing image-bearing.

    python -m qc bundle public_bundle
    QC_PUBLIC=1 QC_REF=public_bundle/reference.json QC_REPORTS=public_bundle/reports \
        QC_CACHE=public_bundle/cache/fields streamlit run app.py

Contents: approved reference, per-batch result/field/report (numbers and text), the tile -> parent map, numerical
field records (KPIs, per-strip KPIs, histogram anchors, window variances, acquisition fingerprints) and the verdict
sensitivity summary. Excluded: raw TIFFs, thumbnails, segmentation labels, edge strips (*.npy), mosaics and any
instrument page with embedded imagery. `check()` enforces this and fails the export otherwise.
"""
import glob
import json
import os
import shutil

from . import brief, instrument, provmap
from .features import CACHE
from .pipeline import REF_PATH, REPORTS

IMAGE_EXT = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.gif', '.webp', '.bmp', '.npy', '.npz')
BATCH_FILES = ('result.json', 'field.json', 'brief.json', 'report.md')


def check(root):
    """Raise if anything image-bearing is present under root (by extension or as an embedded data: URI)."""
    bad = []
    for dp, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(dp, f)
            if f.lower().endswith(IMAGE_EXT):
                bad.append(p)
            elif f.lower().endswith(('.html', '.json', '.md', '.txt', '.csv', '.js')):
                if 'data:image' in open(p, encoding='utf-8', errors='ignore').read():
                    bad.append(p + ' (embedded image)')
    if bad:
        raise RuntimeError('public bundle contains image-bearing content:\n  ' + '\n  '.join(bad))
    return True


def export(out, batches=None):
    if os.path.exists(out) and os.listdir(out):
        raise FileExistsError(f'{out} exists and is not empty')
    rep_out, cache_out = os.path.join(out, 'reports'), os.path.join(out, 'cache', 'fields')
    os.makedirs(rep_out, exist_ok=True)
    os.makedirs(cache_out, exist_ok=True)
    shutil.copy(REF_PATH, os.path.join(out, 'reference.json'))
    batches = batches or sorted(d for d in os.listdir(REPORTS) if os.path.exists(os.path.join(REPORTS, d, 'result.json')))
    for b in batches:
        os.makedirs(os.path.join(rep_out, b), exist_ok=True)
        for f in BATCH_FILES:
            src = os.path.join(REPORTS, b, f)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(rep_out, b, f))
        fpath = os.path.join(REPORTS, b, 'field.json')
        if os.path.exists(fpath) and os.path.exists(instrument.DIST):
            F = json.load(open(fpath, encoding='utf-8'))
            html = instrument.render(F, images=False, brief=brief.build(F))
            open(os.path.join(rep_out, b, 'instrument_public.html'), 'w', encoding='utf-8').write(html)
    provmap.export(rep_out)
    for p in glob.glob(os.path.join(CACHE, '*.json')):
        shutil.copy(p, cache_out)
    sens = os.path.join(os.path.dirname(os.path.normpath(CACHE)), 'sens', 'summary.json')
    if os.path.exists(sens):
        os.makedirs(os.path.join(out, 'cache', 'sens'), exist_ok=True)
        shutil.copy(sens, os.path.join(out, 'cache', 'sens', 'summary.json'))
    check(out)
    return dict(out=out, batches=batches)
