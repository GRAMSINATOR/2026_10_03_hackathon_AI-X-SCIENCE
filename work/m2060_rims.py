"""Two decision-relevant checks for M2060: (1) spatial extent of the density excess along its 700 um section,
(2) where in the size distribution the excess lives (near the 0.36 um detection floor?)."""
import json
import os
import sys

import numpy as np
from scipy import stats
from skimage import measure

sys.path.insert(0, '.')
from qc.features import KPI_CROP
from qc.io import read_gray
from qc.segment import segment

D = json.load(open('work/spatial_raw.json'))
R, parent_of, chains = D['R'], D['parent_of'], D['chains']
base_keys = [k for k in R if k.startswith('Batch_1') and parent_of[k] != 'M2316']
# baseline envelope for a 100-um window (4 columns x full height)
bw = []
for k in base_keys:
    c = np.array(R[k]['cols']['additive_density'])
    bw += [c[i:i + 4].mean() for i in range(0, len(c) - 3, 4)]
bw = np.array(bw)
lo, hi = np.percentile(bw, [2.5, 97.5])
print(f'baseline 100-um window density: mean {bw.mean():.1f}, 95% range {lo:.1f}-{hi:.1f}, max {bw.max():.1f} (n={len(bw)})')
for pid in ('M2060', 'M2068', 'M2080'):
    z = np.concatenate([R[k]['cols']['additive_density'] for k in chains[pid] if k])
    prof = np.convolve(z, np.ones(4) / 4, mode='valid')
    print(pid, 'chain', [k.split('__')[1] for k in chains[pid] if k], f'length {len(z) * 25} um')
    print('   100-um moving mean every 100 um:', ' '.join(f'{v:.0f}' for v in prof[::4]))
    print(f'   fraction of section above baseline 97.5%: {np.mean(prof > hi):.2f}; first/last window {prof[0]:.0f}/{prof[-1]:.0f}')

# PSD excess by size bin: M2060 vs baseline (counts per 1000 um^2)
bins = np.array([0.36, 0.5, 0.7, 1.0, 1.5, 2.5, 4, 12])
def psd(keys):
    cnt, area = np.zeros(len(bins) - 1), 0.0
    for key in keys:
        b, f = key.split('__')
        raw, px, _ = read_gray(f'data/{b}/img_{f}_BSE.tif')
        lab, _, _ = segment(raw[:, KPI_CROP:-KPI_CROP], px)
        a = np.bincount(measure.label(lab == 2).ravel())[1:] * (px / 1000) ** 2
        e = 2 * np.sqrt(a[a >= 0.1] / np.pi)
        cnt += np.histogram(e, bins)[0]
        area += lab.size * (px / 1000) ** 2
    return cnt / area * 1000, cnt
pb, cb = psd(base_keys)
pm, cm = psd([k for k in R if parent_of[k] == 'M2060'])
print('\nECD bin (um)    baseline   M2060   ratio   (counts base/M2060)')
for i in range(len(bins) - 1):
    print(f'{bins[i]:.2f}-{bins[i + 1]:.2f}   {pb[i]:7.2f}  {pm[i]:7.2f}  {pm[i] / max(pb[i], 1e-9):5.2f}   ({int(cb[i])}/{int(cm[i])})')
exc = pm - pb
print(f'share of M2060 excess count below 1.0 um ECD: {exc[:3].sum() / exc.sum():.2f}; below 0.7 um: {exc[:2].sum() / exc.sum():.2f}')
# prevalence: 1 of 7 Batch-3 micrographs anomalous
for k_, n_ in ((1, 7), (2, 14), (3, 21), (4, 28)):
    ci = stats.beta.ppf([0.025, 0.975], [k_, k_ + 1], [n_ - k_ + 1, n_ - k_])
    print(f'prevalence {k_}/{n_}: 95% CI {ci[0] * 100:.1f}-{ci[1] * 100:.1f}%  (width {100 * (ci[1] - ci[0]):.0f} pts)')
