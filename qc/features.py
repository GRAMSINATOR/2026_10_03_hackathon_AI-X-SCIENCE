"""Per-field processing: segmentation, physical KPIs, acquisition fingerprint, cross-detector check, cached artifacts."""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure, morphology

from .io import read_gray
from .segment import pore_mask_se, segment
from .spatial import field_maps

CACHE = os.environ.get('QC_CACHE', 'cache/fields')
EDGE_CROP = 4      # px; removes the 1-4 px green stitching column (provenance edges use this)
KPI_CROP = 8       # px; margin for KPI computation
N_STRIPS = 4       # spatial sub-windows for within-field uncertainty
THUMB = 4          # display downsampling
FEATURE_VERSION = 2  # bump to invalidate cached field records


def _chords_mean(mask, axis, px_um):
    m = mask if axis == 1 else mask.T
    d = np.diff(np.pad(m.astype(np.int8), ((0, 0), (1, 1))), axis=1)
    st, en = np.argwhere(d == 1), np.argwhere(d == -1)
    L = en[:, 1] - st[:, 1]
    inner = (st[:, 1] > 0) & (en[:, 1] < m.shape[1])
    return float(L[inner].mean() * px_um) if inner.any() else np.nan


def kpis(lab, px_nm):
    px_um = px_nm / 1000.0
    a_px = px_um ** 2
    A_um2 = lab.size * a_px
    pore, bri = lab == 0, lab == 2
    k = dict(additive_area_frac=float(bri.mean()), porosity=float(pore.mean()))
    # high-Z additive particles (objects >= 0.1 um^2, i.e. ECD >= 0.36 um)
    ar = np.bincount(measure.label(bri).ravel())[1:] * a_px
    ar = ar[ar >= 0.1]
    ecd = 2 * np.sqrt(ar / np.pi)
    k.update(additive_density=float(len(ar) / A_um2 * 1000),
             additive_d50_um=float(np.median(ecd)) if len(ecd) else np.nan,
             additive_d90_um=float(np.percentile(ecd, 90)) if len(ecd) else np.nan,
             additive_max_um=float(ecd.max()) if len(ecd) else np.nan)
    # pores
    rp = measure.regionprops_table(measure.label(pore), properties=('area', 'axis_major_length', 'axis_minor_length', 'orientation'))
    pa = rp['area'] * a_px
    keep = pa >= 0.05
    pe = 2 * np.sqrt(pa[keep] / np.pi)
    L = rp['axis_major_length'] * px_um
    W = rp['axis_minor_length'] * px_um
    horiz = np.abs(np.abs(rp['orientation']) - np.pi / 2) < np.pi / 9
    crack = (L > 15) & horiz & (L / np.maximum(W, 1e-3) > 6)
    k.update(pore_size_um=float((pe * pa[keep]).sum() / max(pa[keep].sum(), 1e-9)),
             horiz_pore_frac=float(pa[keep & horiz].sum() / max(pa[keep].sum(), 1e-9)),
             long_crack_len_per_mm2=float(L[crack].sum() / A_um2 * 1e6),
             pore_len_max_um=float(L.max()) if len(L) else np.nan)
    # coarse-grained solid chords (ignore pores < 0.25 um^2 -> robust to blur/noise)
    macro = morphology.remove_small_objects(pore, max_size=int(0.25 / a_px))
    k.update(solid_chord_x_um=_chords_mean(~macro, 1, px_um), solid_chord_y_um=_chords_mean(~macro, 0, px_um))
    return k


def additive_brightness(lab, s, a, px_nm):
    # median normalised core intensity u = (I - m) / (b - m) of additive particles by size class (1 = high-Z mode)
    px_um = px_nm / 1000.0
    bri = lab == 2
    L = measure.label(bri)
    area = np.bincount(L.ravel())[1:] * px_um ** 2
    ecd = 2 * np.sqrt(area / np.pi)
    core = L * ndi.binary_erosion(bri, iterations=2)
    out = {}
    for name, lo, hi in (('additive_fines_u', 0.6, 1.0), ('additive_coarse_u', 2.0, 1e9)):
        idx = np.nonzero((ecd >= lo) & (ecd < hi))[0] + 1
        med = np.array(ndi.median(s, core, idx)) if len(idx) else np.array([])
        med = med[np.isfinite(med)] if med.size else med
        out[name] = float(np.median((med - a['m']) / (a['b'] - a['m']))) if med.size else float('nan')
    return out


def acquisition(raw, s, a, px_nm):
    contrast = a['b'] - a['m']
    lo, hi = np.percentile(raw, [1, 99])
    hh = np.bincount(np.clip(raw, 0, 255).astype(np.uint8).ravel(), minlength=256)
    hp = raw - ndi.gaussian_filter(raw, 2)
    matrix = np.abs(s - a['m']) < 0.15 * contrast
    noise = 1.4826 * np.median(np.abs(hp[matrix]))
    g = ndi.gaussian_gradient_magnitude(s, 1.0)
    return dict(px_nm=px_nm, contrast_mb=float(contrast), matrix_level=a['m'], additive_level=a['b'], black_level=a['floor'],
                clip_black=float(np.mean(raw <= 0.5)), clip_white=float(np.mean(raw >= 254.5)),
                hist_gaps=float(np.mean(hh[int(lo):int(hi) + 1] == 0)), noise_abs=float(noise),
                cnr_additive=float(contrast / max(noise, 1e-6)), sharpness=float(np.percentile(g, 99) / contrast),
                additive_peak_found=bool(a['peak_ok']))


def _thumb(img, path, factor=THUMB, mode='L'):
    h, w = (img.shape[0] // factor) * factor, (img.shape[1] // factor) * factor
    if mode == 'P':
        t = img[:h:factor, :w:factor]
    else:
        t = np.clip(img[:h, :w].reshape(h // factor, factor, w // factor, factor).mean((1, 3)), 0, 255)
    Image.fromarray(t.astype(np.uint8)).save(path, quality=88) if path.endswith('.jpg') else Image.fromarray(t.astype(np.uint8)).save(path)


def process_field(field, force=False):
    """Compute (or load cached) record for one field. Returns a JSON-serialisable dict."""
    key = f"{field['batch']}__{field['fid']}"
    out_json = os.path.join(CACHE, key + '.json')
    src = field['channels']['BSE']
    stamp = [os.path.getsize(src), int(os.path.getmtime(src))]
    if not force and os.path.exists(out_json):
        rec = json.load(open(out_json))
        if rec.get('stamp') == stamp and rec.get('v') == FEATURE_VERSION:
            return rec
    os.makedirs(CACHE, exist_ok=True)
    raw_full, px_nm, sig = read_gray(src)
    H, W = raw_full.shape
    # provenance edges (BSE, after removing the edge artifact column)
    np.save(os.path.join(CACHE, key + '_edges.npy'), np.stack([raw_full[:, EDGE_CROP], raw_full[:, W - 1 - EDGE_CROP]]))
    raw = raw_full[:, KPI_CROP:-KPI_CROP]
    lab, s, a = segment(raw, px_nm)
    rec = dict(key=key, v=FEATURE_VERSION, batch=field['batch'], fid=field['fid'], H=H, W=W, px_nm=px_nm, xres_sig=sig, stamp=stamp,
               detectors=field['detectors'], anchors=a)
    rec['kpi'] = kpis(lab, px_nm)
    rec['kpi'].update(additive_brightness(lab, s, a, px_nm))
    rec['strips'] = [kpis(l, px_nm) for l in np.array_split(lab, N_STRIPS, axis=1)]
    rec['acq'] = acquisition(raw, s, a, px_nm)
    rec['spatial'] = field_maps(lab, px_nm)
    # cross-detector porosity check with the secondary-electron image
    if 'SE2' in field['channels']:
        se, _, _ = read_gray(field['channels']['SE2'])
        pm = pore_mask_se(se[:, KPI_CROP:-KPI_CROP], px_nm)
        bp = lab == 0
        rec['kpi']['porosity_SE2'] = float(pm.mean())
        rec['kpi']['pore_dice_SE2'] = float(2 * (pm & bp).sum() / max(pm.sum() + bp.sum(), 1))
    # display artifacts
    _thumb(raw, os.path.join(CACHE, key + '_BSE.jpg'))
    for det in ('SE2', 'InLens'):
        if det in field['channels']:
            im, _, _ = read_gray(field['channels'][det])
            _thumb(im[:, KPI_CROP:-KPI_CROP], os.path.join(CACHE, key + f'_{det}.jpg'))
    _thumb(lab, os.path.join(CACHE, key + '_lab.png'), mode='P')
    json.dump(rec, open(out_json, 'w'), indent=1, default=float)
    return rec
