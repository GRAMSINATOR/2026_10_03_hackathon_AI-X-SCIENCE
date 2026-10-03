"""KPI robustness card: how much do synthetic acquisition changes move each KPI? (measured, not assumed)"""
import numpy as np
from scipy import ndimage as ndi

from .features import KPI_CROP, acquisition, kpis
from .io import read_gray
from .segment import segment
from .stats import KPIS

_rng = np.random.default_rng(0)
PERTURB = {
    'brightness +20': lambda x: np.clip(x + 20, 0, 255),
    'contrast x0.7': lambda x: np.clip((x - x.mean()) * 0.7 + x.mean(), 0, 255),
    'contrast x1.3': lambda x: np.clip((x - x.mean()) * 1.3 + x.mean(), 0, 255),
    'gamma 0.7': lambda x: 255 * (x / 255) ** 0.7,
    'gamma 1.4': lambda x: 255 * (x / 255) ** 1.4,
    'defocus blur 1.5 px': lambda x: ndi.gaussian_filter(x, 1.5),
    'noise sigma 8': lambda x: np.clip(x + _rng.normal(0, 8, x.shape), 0, 255),
    'histogram stretch (gaps)': lambda x: np.clip(np.round(x / 2) * 2, 0, 255),
    'raised black level': lambda x: np.clip(x * 0.85 + 22, 0, 255),
    'half resolution': lambda x: ndi.zoom(ndi.zoom(x, 0.5, order=1), 2, order=1)[: x.shape[0], : x.shape[1]],
}


def _one(args):
    path, name = args
    raw, px, _ = read_gray(path)
    x = raw[:, KPI_CROP:-KPI_CROP][:, 1500:5500]
    y = PERTURB[name](x).astype(np.float32) if name != 'none' else x
    lab, s, a = segment(y, px)
    return path, name, kpis(lab, px), acquisition(y, s, a, px)


def card(paths, pool):
    jobs = [(p, n) for p in paths for n in ['none'] + list(PERTURB)]
    res = pool.map(_one, jobs)
    base = {p: k for p, n, k, _ in res if n == 'none'}
    table = {k: {} for k in KPIS}
    tested = {}
    for _, _, _, aq in res:
        for m, v in aq.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                lo, hi = tested.get(m, (v, v))
                tested[m] = (min(lo, v), max(hi, v))
    for p, n, kp, _ in res:
        if n == 'none':
            continue
        for k in KPIS:
            table[k].setdefault(n, []).append(abs(kp[k] - base[p][k]))
    out = {}
    for k in KPIS:
        means = {n: float(np.nanmean(v)) for n, v in table[k].items()}
        worst = max(means, key=means.get)
        out[k] = dict(per_perturbation=means, worst=worst, max_abs=means[worst])
    return out, {m: [float(lo), float(hi)] for m, (lo, hi) in tested.items()}
