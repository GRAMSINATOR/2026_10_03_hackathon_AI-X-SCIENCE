"""Acquisition-robust 3-phase segmentation of BSE cross-sections: pore / matrix (graphite-like) / bright (high-Z).

Boundaries are placed at 50% of the local intensity step (matrix<->bright, matrix<->pore floor) using per-image
anchors, so phase fractions are invariant to affine brightness/contrast changes between micrographs.
"""
import numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from skimage import morphology

PX_UM = 0.025  # 25 nm / px, from TIFF XResolution


def load(batch, fid, det, crop=8):
    return np.load(f'cache/{batch}_{fid}_{det}.npy')[:, crop:-crop].astype(np.float32)


def anchors(s):
    h, _ = np.histogram(s, bins=256, range=(0, 256))
    h = ndi.gaussian_filter1d(h.astype(float), 2) / s.size
    lh = np.log10(h + 1e-7)
    m = int(np.argmax(h[5:250]) + 5)
    pk, _ = find_peaks(lh, prominence=0.05)
    pk = [p for p in pk if m + 15 < p < 250 and h[p] > 3e-4]
    if pk:  # dominant secondary (high-Z) population = tallest peak above the matrix peak
        b, ok = float(max(pk, key=lambda p: h[p])), True
    else:  # shoulder fallback: strongest negative curvature above the matrix peak
        d2 = np.gradient(np.gradient(lh))
        seg = np.arange(m + 15, 200)
        b, ok = float(seg[np.argmin(d2[seg])]), False
    floor = float(np.percentile(s, 0.5))
    return float(m), b, floor, ok


def segment(bse, sigma=1.0, f_pore=0.5, f_bright=0.5, open_r=2, min_px=16):
    s = ndi.gaussian_filter(bse, sigma)
    m, b, p, ok = anchors(s)
    t_pore = p + f_pore * (m - p)
    t_bright = m + f_bright * (b - m)
    pore = morphology.remove_small_objects(s < t_pore, max_size=min_px)
    bright = s > t_bright
    if open_r:
        bright = morphology.binary_opening(bright, morphology.disk(open_r))
    bright = morphology.remove_small_objects(bright, max_size=min_px)
    lab = np.ones(bse.shape, np.uint8)
    lab[pore] = 0
    lab[bright & ~pore] = 2
    return lab, s, dict(m=m, b=b, floor=p, t_pore=t_pore, t_bright=t_bright,
                        contrast_mb=b - m, contrast_pm=m - p, peak_ok=ok)
