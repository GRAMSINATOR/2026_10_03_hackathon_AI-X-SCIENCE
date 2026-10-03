"""Acquisition-robust 3-phase segmentation of BSE cross-sections: pore / matrix (graphite-like) / high-Z additive.

Phase boundaries are placed at 50% of the local intensity step, using per-image anchors (matrix mode, dominant
high-Z mode, pore floor). This makes phase fractions invariant to affine brightness/contrast changes between
micrographs. Spatial parameters are in physical units and converted with the pixel size.
"""
import os

import numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from skimage import morphology

SMOOTH_NM = 25.0       # Gaussian denoising sigma
OPEN_NM = 50.0         # opening radius that removes bright rims/edges thinner than ~100 nm
MIN_OBJ_UM2 = 0.01     # minimum object area kept


def anchors(s):
    """Matrix mode m, dominant high-Z mode b, pore floor p of a smoothed 0..255 image."""
    h, _ = np.histogram(s, bins=256, range=(0, 256))
    h = ndi.gaussian_filter1d(h.astype(float), 2) / s.size
    lh = np.log10(h + 1e-7)
    m = int(np.argmax(h[5:250]) + 5)
    pk, _ = find_peaks(lh, prominence=0.05)
    pk = [p for p in pk if m + 15 < p < 250 and h[p] > 3e-4]
    if pk:
        b, ok = float(max(pk, key=lambda p: h[p])), True
    else:  # no separate high-Z peak: use the strongest shoulder above the matrix peak
        d2 = np.gradient(np.gradient(lh))
        seg = np.arange(m + 15, 200)
        b, ok = float(seg[np.argmin(d2[seg])]), False
    return float(m), b, float(np.percentile(s, 0.5)), ok


F_PORE = float(os.environ.get('QC_FPORE', 0.5))
F_BRIGHT = float(os.environ.get('QC_FBRIGHT', 0.5))


def segment(bse, px_nm, f_pore=F_PORE, f_bright=F_BRIGHT):
    """Return (labels uint8 {0 pore, 1 matrix, 2 high-Z}, smoothed image, anchor dict)."""
    s = ndi.gaussian_filter(bse, SMOOTH_NM / px_nm)
    m, b, p, ok = anchors(s)
    t_pore, t_bright = p + f_pore * (m - p), m + f_bright * (b - m)
    min_px = max(4, int(round(MIN_OBJ_UM2 / (px_nm / 1000) ** 2)))
    pore = morphology.remove_small_objects(s < t_pore, max_size=min_px)
    bright = morphology.binary_opening(s > t_bright, morphology.disk(max(1, int(round(OPEN_NM / px_nm)))))
    bright = morphology.remove_small_objects(bright, max_size=min_px)
    lab = np.ones(bse.shape, np.uint8)
    lab[pore] = 0
    lab[bright & ~pore] = 2
    return lab, s, dict(m=m, b=b, floor=p, t_pore=t_pore, t_bright=t_bright, peak_ok=ok)


def pore_mask_se(img, px_nm, f=0.5):
    """Independent pore segmentation of a secondary-electron image (cross-detector check)."""
    s = ndi.gaussian_filter(img, 1.5 * SMOOTH_NM / px_nm)
    h, _ = np.histogram(s, bins=256, range=(0, 256))
    h = ndi.gaussian_filter1d(h.astype(float), 2)
    m = int(np.argmax(h[5:250]) + 5)
    p = np.percentile(s, 0.5)
    min_px = max(4, int(round(MIN_OBJ_UM2 / (px_nm / 1000) ** 2)))
    return morphology.remove_small_objects(s < p + f * (m - p), max_size=min_px)
