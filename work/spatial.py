"""Spatial support audit: variance vs window area (integral range), tile/micrograph-scale excess variance,
and 1-D variograms along stitched cross-sections. Output: work/spatial.json + printed summary."""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np
from skimage import measure

sys.path.insert(0, '.')
from qc.features import KPI_CROP
from qc.io import discover, read_gray
from qc.pipeline import known_records
from qc import provenance
from qc.segment import segment

WIN = [80, 160, 320, 640, 1280]   # px: 2, 4, 8, 16, 32 um squares
COL = 1000                        # px: 25 um transect columns (full height)


def fields_maps(args):
    key, path = args
    raw, px, _ = read_gray(path)
    raw = raw[:, KPI_CROP:-KPI_CROP]
    lab, _, _ = segment(raw, px)
    bri, pore = lab == 2, lab == 0
    L = measure.label(bri)
    rp = measure.regionprops(L)
    pxa = (px / 1000) ** 2
    cent = np.array([p.centroid for p in rp if p.area * pxa >= 0.1]).reshape(-1, 2)
    cnt = np.zeros(lab.shape, np.float32)
    if len(cent):
        np.add.at(cnt, (cent[:, 0].astype(int), cent[:, 1].astype(int)), 1.0)
    out = dict(key=key, H=lab.shape[0], W=lab.shape[1], px=px, win={}, cols={})
    maps = dict(additive_area_frac=bri.astype(np.float32), porosity=pore.astype(np.float32), additive_density=cnt)
    for name, mp in maps.items():
        scale = 1000 / ((px / 1000) ** 2) if name == 'additive_density' else 1.0   # density per 1000 um^2
        out['win'][name] = {}
        for w in WIN:
            H, W = (mp.shape[0] // w) * w, (mp.shape[1] // w) * w
            if H < w:
                continue
            blk = mp[:H, :W].reshape(H // w, w, W // w, w).mean((1, 3)) * scale
            out['win'][name][w] = blk.ravel().tolist()
        nc = mp.shape[1] // COL
        out['cols'][name] = (mp[:, :nc * COL].reshape(mp.shape[0], nc, COL).mean((0, 2)) * scale).tolist()
        out[name] = float(mp.mean() * scale)
    return out


if __name__ == '__main__':
    recs = known_records()
    paths = {}
    for b in sorted(os.listdir('data')):
        for f in discover(os.path.join('data', b)):
            paths[f"{b}__{f['fid']}"] = f['channels']['BSE']
    with Pool(10) as P:
        R = {r['key']: r for r in P.map(fields_maps, list(paths.items()))}
    prov = provenance.build(recs, 'Batch_1')
    json.dump(dict(R=R, parent_of=prov['parent_of'], chains=prov['chains']), open('work/spatial_raw.json', 'w'))
    print('saved', len(R))
