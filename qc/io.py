"""Discovery and loading of SEM fields (one field = one field of view, several co-registered detector images)."""
import glob
import os
import re

import numpy as np
import tifffile

# Canonical detector names. ETD and SE are both secondary-electron (Everhart-Thornley-type) detectors.
DET_CANON = {'BSE': 'BSE', 'BSD': 'BSE', 'BSED': 'BSE', 'CBS': 'BSE', 'ABS': 'BSE', 'ASB': 'BSE', 'ESB': 'BSE', 'VCD': 'BSE',
             'ETD': 'SE2', 'SE': 'SE2', 'SE2': 'SE2', 'SESI': 'SE2', 'EVERHART': 'SE2',
             'INLENS': 'InLens', 'TLD': 'InLens', 'SE1': 'InLens', 'INBEAM': 'InLens', 'ILENS': 'InLens'}
DEFAULT_PX_NM = 25.0
_NAME = re.compile(r'^(?:img_)?(?P<fid>.+?)_(?P<det>[A-Za-z0-9]+)$')


def discover(folder):
    """Group the TIFFs of a batch folder into fields: {fid, batch, channels{canon: path}, detectors{canon: raw}}."""
    batch = os.path.basename(os.path.normpath(folder))
    fields = {}
    for p in sorted(glob.glob(os.path.join(folder, '*.tif')) + glob.glob(os.path.join(folder, '*.tiff'))):
        stem = os.path.splitext(os.path.basename(p))[0]
        m = _NAME.match(stem)
        fid, det = (m['fid'], m['det']) if m and m['det'].upper() in DET_CANON else (stem, 'BSE')
        canon = DET_CANON.get(det.upper(), det)
        f = fields.setdefault(fid, dict(fid=fid, batch=batch, channels={}, detectors={}))
        f['channels'][canon] = p
        f['detectors'][canon] = det
    return [f for f in fields.values() if 'BSE' in f['channels']]


def pixel_size_nm(tif):
    """Pixel size from TIFF X/YResolution + ResolutionUnit (the only acquisition metadata that survives)."""
    p = tif.pages[0]
    try:
        num, den = p.tags['XResolution'].value
        unit = int(p.tags['ResolutionUnit'].value) if 'ResolutionUnit' in p.tags else 2
        per_unit = num / den
        if per_unit <= 1 or unit == 1:
            return DEFAULT_PX_NM, None
        nm = (25.4e6 if unit == 2 else 1e7) / per_unit
        return nm, f'{num}/{den}'
    except (KeyError, ZeroDivisionError, TypeError):
        return DEFAULT_PX_NM, None


def read_gray(path):
    """Return (gray float32 image on a 0..255 scale, pixel size nm, xres signature string)."""
    with tifffile.TiffFile(path) as t:
        a = t.pages[0].asarray()
        px, sig = pixel_size_nm(t)
    if a.ndim == 3:
        a = a[..., 0] if a.shape[-1] >= 3 and np.array_equal(a[..., 0], a[..., 2]) else a[..., :3].mean(-1)
    a = a.astype(np.float32)
    if a.max() > 255.5:  # 16-bit data -> 8-bit scale so histogram anchors are comparable
        a = a / 257.0
    return a, px, sig
