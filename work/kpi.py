"""Per-tile physical KPIs (BSE) + acquisition-quality metrics; also per 4 vertical strips for spatial uncertainty."""
import os
import sys

import numpy as np
import pandas as pd
from multiprocessing import Pool
from scipy import ndimage as ndi
from skimage import feature, measure, morphology

sys.path.insert(0, 'work')
from seg import PX_UM, load, segment


def chords(mask, axis):
    m = mask if axis == 1 else mask.T
    pad = np.pad(m.astype(np.int8), ((0, 0), (1, 1)))
    d = np.diff(pad, axis=1)
    st, en = np.argwhere(d == 1), np.argwhere(d == -1)
    L = en[:, 1] - st[:, 1]
    inner = (st[:, 1] > 0) & (en[:, 1] < m.shape[1])
    L = L[inner]
    return L * PX_UM if len(L) else np.array([np.nan])


def corr_len(mask):
    out = []
    for ax in (1, 0):
        a = mask.astype(np.float32)
        a = a - a.mean()
        f = np.fft.rfft(a, axis=ax, n=2 * a.shape[ax])
        ac = np.fft.irfft(f * np.conj(f), axis=ax)
        ac = ac.mean(axis=1 - ax)[: a.shape[ax] // 2]
        ac = ac / ac[0]
        i = int(np.argmax(ac < np.exp(-1)))
        out.append(i * PX_UM if i > 0 else np.nan)
    return out  # [x, y]


def multiscale_cv(mask, sizes=(40, 80, 160, 320, 640)):
    cv = []
    for w in sizes:
        H, W = (mask.shape[0] // w) * w, (mask.shape[1] // w) * w
        if H < w or W < w:
            cv.append(np.nan)
            continue
        blk = mask[:H, :W].reshape(H // w, w, W // w, w).mean((1, 3))
        cv.append(blk.std() / (blk.mean() + 1e-9))
    cv = np.array(cv)
    ok = np.isfinite(cv) & (cv > 0)
    slope = np.polyfit(np.log(np.array(sizes)[ok]), np.log(cv[ok]), 1)[0] if ok.sum() >= 3 else np.nan
    return cv, slope


def kpis(lab, s, a):
    pore, bri = lab == 0, lab == 2
    solid = ~pore
    A_um2 = lab.size * PX_UM ** 2
    k = dict(phi_pore=pore.mean(), phi_bright=bri.mean(), bright_in_solid=bri.sum() / max(solid.sum(), 1))
    # bright (high-Z) particles
    lb = measure.label(bri)
    rp = measure.regionprops_table(lb, properties=('area', 'axis_major_length', 'axis_minor_length', 'solidity'))
    ar = rp['area'] * PX_UM ** 2
    keep = ar >= 0.1
    ecd = 2 * np.sqrt(ar[keep] / np.pi)
    has = len(ecd) > 0
    k.update(bright_n_per_1000um2=keep.sum() / A_um2 * 1000,
             bright_ecd_d10=np.percentile(ecd, 10) if has else np.nan,
             bright_ecd_d50=np.median(ecd) if has else np.nan,
             bright_ecd_d90=np.percentile(ecd, 90) if has else np.nan,
             bright_ecd_areaw=(ecd * ar[keep]).sum() / ar[keep].sum() if has else np.nan,
             bright_aspect=np.median(rp['axis_major_length'][keep] / np.maximum(rp['axis_minor_length'][keep], 1)) if has else np.nan,
             bright_solidity=np.median(rp['solidity'][keep]) if has else np.nan)
    # pores
    lp = measure.label(pore)
    rpp = measure.regionprops_table(lp, properties=('area', 'axis_major_length', 'axis_minor_length', 'orientation'))
    pa = rpp['area'] * PX_UM ** 2
    pk = pa >= 0.05
    pecd = 2 * np.sqrt(pa[pk] / np.pi)
    horiz = np.abs(np.abs(rpp['orientation'][pk]) - np.pi / 2) < np.pi / 9  # skimage: orientation wrt rows axis
    k.update(pore_n_per_1000um2=pk.sum() / A_um2 * 1000,
             pore_ecd_areaw=(pecd * pa[pk]).sum() / max(pa[pk].sum(), 1e-9),
             pore_largest_frac=pa.max() / pa.sum() if len(pa) else np.nan,
             pore_aspect=np.average(rpp['axis_major_length'][pk] / np.maximum(rpp['axis_minor_length'][pk], 1), weights=pa[pk]) if pk.any() else np.nan,
             pore_horiz_frac=np.sum(pa[pk] * horiz) / max(pa[pk].sum(), 1e-9))
    # stereological chords
    for nm, msk in (('pore', pore), ('solid', solid)):
        cx, cy = chords(msk, 1), chords(msk, 0)
        k[f'{nm}_chord_x'] = np.nanmean(cx)
        k[f'{nm}_chord_y'] = np.nanmean(cy)
        k[f'{nm}_chord_ratio'] = k[f'{nm}_chord_x'] / k[f'{nm}_chord_y']
    # coarse-grained (resolution/noise-robust) variants: ignore pores < 0.25 um^2
    macro = morphology.remove_small_objects(pore, max_size=400)
    k['phi_pore_macro'] = macro.mean()
    for nm, msk in (('pore_macro', macro), ('solid_macro', ~macro)):
        k[f'{nm}_chord_x'] = np.nanmean(chords(msk, 1))
        k[f'{nm}_chord_y'] = np.nanmean(chords(msk, 0))
    em = macro ^ ndi.binary_erosion(macro)
    k['interface_density_macro'] = em.sum() * PX_UM / A_um2 * (np.pi / 4)
    edge = pore ^ ndi.binary_erosion(pore)
    k['interface_density'] = edge.sum() * PX_UM / A_um2 * (np.pi / 4)
    k['pore_corr_x'], k['pore_corr_y'] = corr_len(pore)
    cvp, slp = multiscale_cv(pore.astype(np.float32))
    cvb, slb = multiscale_cv(bri.astype(np.float32))
    k.update(pore_cv_4um=cvp[2], pore_cv_16um=cvp[4], pore_cv_slope=slp,
             bright_cv_4um=cvb[2], bright_cv_16um=cvb[4], bright_cv_slope=slb)
    # interface orientation order (structure tensor; angle 0 = gradients along x, 90 = along y)
    ss = ndi.gaussian_filter(solid[::2, ::2].astype(np.float32), 1.0)  # phase-boundary orientation (acquisition-robust)
    Arr, Arc, Acc = feature.structure_tensor(ss, sigma=3, order='rc')
    th2 = np.arctan2(2 * Arc, Acc - Arr)
    w = np.sqrt((Acc - Arr) ** 2 + 4 * Arc ** 2)
    z = np.sum(w * np.exp(1j * th2)) / w.sum()
    k['orient_order'] = np.abs(z)
    k['orient_angle_deg'] = np.degrees(np.angle(z) / 2)
    # intra-particle cracks: thin dark lines inside solid (closing residue)
    th = ndi.grey_closing(s, size=(7, 7)) - s
    inner = ndi.binary_erosion(solid, iterations=4)
    crk = morphology.remove_small_objects((th > 0.6 * a['contrast_mb']) & inner, max_size=30)
    sk = morphology.skeletonize(crk); lk = measure.label(sk, connectivity=2)
    lens = np.bincount(lk.ravel())[1:] * PX_UM
    k['crack_len_density'] = lens[lens >= 0.5].sum() / A_um2  # crack-like dark lines >= 0.5 um inside solid
    prof = np.array([b.mean() for b in np.array_split(pore, 10, axis=0)])
    k['pore_profile_cv'] = prof.std() / (prof.mean() + 1e-9)
    k['pore_profile_slope'] = np.polyfit(np.linspace(0, 1, 10), prof, 1)[0]
    return k


def acq_qc(raw, s, a):
    lo, hi = np.percentile(raw, [1, 99])
    hh = np.bincount(raw.astype(np.uint8).ravel(), minlength=256)
    comb = np.mean(hh[int(lo):int(hi) + 1] == 0)
    hp = raw - ndi.gaussian_filter(raw, 2)
    matmask = np.abs(s - a['m']) < 0.15 * a['contrast_mb']
    noise = 1.4826 * np.median(np.abs(hp[matmask])) / a['contrast_mb']
    g = ndi.gaussian_gradient_magnitude(raw, 1.0)
    return dict(acq_contrast_mb=a['contrast_mb'], acq_matrix_level=a['m'], acq_bright_level=a['b'], acq_floor=a['floor'],
                acq_clip0=np.mean(raw <= 0.5), acq_comb=comb, acq_noise_rel=noise,
                acq_sharp_rel=np.percentile(g, 99) / a['contrast_mb'], acq_peak_ok=a['peak_ok'])


def run(args):
    batch, fid, src = args
    raw = load(batch, fid, 'BSE')
    lab, s, a = segment(raw)
    np.save(f'cache/lab_{batch}_{fid}.npy', lab)
    rows = [dict(batch=batch, fid=fid, src=src, win='all', **kpis(lab, s, a), **acq_qc(raw, s, a))]
    for i, (l, ss) in enumerate(zip(np.array_split(lab, 4, 1), np.array_split(s, 4, 1))):
        rows.append(dict(batch=batch, fid=fid, src=src, win=f'w{i}', **kpis(l, ss, a)))
    return rows


if __name__ == '__main__':
    S = pd.read_csv('work/sources.csv')
    with Pool(min(10, os.cpu_count() - 2)) as P:
        res = P.map(run, [tuple(x) for x in S[['batch', 'fid', 'src']].values])
    df = pd.DataFrame([r for rr in res for r in rr])
    df.to_csv('work/kpi_tiles.csv', index=False)
    print(df[df.win == 'all'].shape, 'cpus', os.cpu_count())
