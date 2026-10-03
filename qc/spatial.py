"""Capture geometry / spatial support.

Per field: window-mean variances (2-32 um squares), 25-um column profiles along the section, additive size histogram.
Reference level: how variance scales with window area (Var ~ A^beta), whether adjacent tiles of one micrograph
differ more than that short-range scaling predicts (excess E, chi-square CI), transect variograms along stitched
sections, and a spatial class per KPI (short-range / FOV-scale / long-range). Classical stereology / RVE statistics,
no geostatistical model fitting beyond these summaries.
"""
import numpy as np
from scipy import stats
from skimage import measure

SPATIAL_KPIS = ('additive_area_frac', 'additive_density', 'porosity')
WIN_UM = (2, 4, 8, 16, 32)
COL_UM = 25.0
PSD_BINS = [0.36, 0.5, 0.7, 1.0, 1.5, 2.5, 4.0, 12.0, 1e9]
BAND_COLS = 4   # 100-um window for the strip band


def field_maps(lab, px_nm):
    px_um = px_nm / 1000.0
    bri, pore = lab == 2, lab == 0
    rp = [p for p in measure.regionprops(measure.label(bri)) if p.area * px_um ** 2 >= 0.1]
    cnt = np.zeros(lab.shape, np.float32)
    if rp:
        c = np.array([p.centroid for p in rp]).astype(int)
        np.add.at(cnt, (c[:, 0], c[:, 1]), 1.0)
    ecd = np.array([2 * np.sqrt(p.area * px_um ** 2 / np.pi) for p in rp])
    maps = dict(additive_area_frac=(bri.astype(np.float32), 1.0), porosity=(pore.astype(np.float32), 1.0),
                additive_density=(cnt, 1000.0 / px_um ** 2))
    col = int(round(COL_UM / px_um))
    out = dict(col_um=COL_UM, width_um=lab.shape[1] * px_um, height_um=lab.shape[0] * px_um, win={}, cols={},
               psd=np.histogram(ecd, PSD_BINS)[0].tolist() if len(ecd) else [0] * (len(PSD_BINS) - 1),
               area_um2=float(lab.size * px_um ** 2))
    for k, (mp, scale) in maps.items():
        out['win'][k] = {}
        for w_um in WIN_UM:
            w = int(round(w_um / px_um))
            H, W = (mp.shape[0] // w) * w, (mp.shape[1] // w) * w
            if H < w or W < w:
                continue
            blk = mp[:H, :W].reshape(H // w, w, W // w, w).mean((1, 3)).ravel() * scale
            if blk.size > 2:
                out['win'][k][str(w_um)] = [float(blk.var(ddof=1)), int(blk.size)]
        nc = mp.shape[1] // col
        out['cols'][k] = (mp[:, :nc * col].reshape(mp.shape[0], nc, col).mean((0, 2)) * scale).tolist()
    return out


def _runs(order):
    runs, cur = [], []
    for k in order:
        if k is None:
            runs.append(cur)
            cur = []
        else:
            cur.append(k)
    runs.append(cur)
    return [r for r in runs if r]


def model(records, parent_of, chains, excluded_additive=()):
    """Reference-level spatial support model from all known fields (spread / correlation only, never means)."""
    by_key = {r['key']: r for r in records if 'spatial' in r}
    out = {}
    for k in SPATIAL_KPIS:
        ok = [r for r in by_key.values() if not (k.startswith('additive') and parent_of[r['key']] in excluded_additive)]
        A, V = [], []
        for w_um in WIN_UM:
            v = [r['spatial']['win'][k][str(w_um)][0] for r in ok if str(w_um) in r['spatial']['win'][k]]
            if v:
                A.append(w_um ** 2)
                V.append(float(np.mean(v)))
        A, V = np.array(A, float), np.array(V, float)
        beta, logc = np.polyfit(np.log(A[1:]), np.log(V[1:]), 1)
        groups = {}
        for r in ok:
            groups.setdefault(parent_of[r['key']], []).append(r['kpi'][k])
        ss = sum(float(((np.array(g) - np.mean(g)) ** 2).sum()) for g in groups.values() if len(g) > 1)
        df = sum(len(g) - 1 for g in groups.values() if len(g) > 1)
        A_tile = float(np.mean([r['spatial']['area_um2'] for r in ok]))
        pred = float(np.exp(logc) * A_tile ** beta)
        v_tile = ss / df if df else float('nan')
        E = v_tile / pred if df else float('nan')
        ci = [v_tile * df / stats.chi2.ppf(0.975, df) / pred, v_tile * df / stats.chi2.ppf(0.025, df) / pred] if df else [np.nan, np.nan]
        # transect variogram along stitched sections (contiguous runs only)
        num, cnt = {}, {}
        for pid, order in chains.items():
            if k.startswith('additive') and pid in excluded_additive:
                continue
            for run in _runs(order):
                z = np.concatenate([by_key[x]['spatial']['cols'][k] for x in run if x in by_key]) if run else np.array([])
                for h in range(1, len(z)):
                    d = z[h:] - z[:-h]
                    num[h] = num.get(h, 0.0) + float((d ** 2).sum())
                    cnt[h] = cnt.get(h, 0) + len(d)
        hs = [h for h in sorted(num) if cnt[h] >= 20]
        gam = [0.5 * num[h] / cnt[h] for h in hs]
        lag_um = [h * COL_UM for h in hs]
        cls, rng = 'short-range', None
        if np.isfinite(ci[0]) and ci[0] > 1 and gam:
            g = np.array(gam)
            early = g[np.array(lag_um) <= 250].max()
            if g[-1] > 1.2 * early:
                cls, rng = 'long-range', float(lag_um[-1])
            else:
                cls, rng = 'fov-scale', float(lag_um[int(np.argmax(g >= 0.9 * g.max()))])
        out[k] = dict(beta=float(beta), windows_um=[float(np.sqrt(a)) for a in A], window_var=V.tolist(), A_tile_um2=A_tile,
                      var_tile_obs=float(v_tile), var_tile_pred=pred, excess=float(E), excess_ci=[float(c) for c in ci], df=df,
                      variogram=dict(lag_um=lag_um, gamma=gam, n_pairs=[cnt[h] for h in hs]), cls=cls, range_um=rng,
                      max_coherent_um=float(max(sum(by_key[x]['spatial']['width_um'] for x in run if x in by_key)
                                                for o in chains.values() for run in _runs(o))))
    return out


def psd_density(records):
    """Additive count per size bin per 1000 um^2, pooled over records."""
    c = np.zeros(len(PSD_BINS) - 1)
    a = 0.0
    for r in records:
        c += np.array(r['spatial']['psd'], float)
        a += r['spatial']['area_um2']
    return (c / max(a, 1e-9) * 1000).tolist()


def band(records, k, excluded=()):
    """Approved 100-um window band for strip display (visual aid; decisions stay micrograph-level)."""
    w = []
    for r in records:
        if r.get('parent') in excluded:
            continue
        c = np.array(r['spatial']['cols'][k], float)
        w += [c[i:i + BAND_COLS].mean() for i in range(0, len(c) - BAND_COLS + 1)]
    w = np.array(w)
    return dict(mean=float(w.mean()), lo=float(w.mean() - 1.96 * w.std(ddof=1)), hi=float(w.mean() + 1.96 * w.std(ddof=1)), n=int(len(w)))
