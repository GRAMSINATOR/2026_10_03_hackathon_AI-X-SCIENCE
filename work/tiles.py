import numpy as np, pandas as pd, itertools, tifffile, glob, os
from skimage.registration import phase_cross_correlation
df = pd.read_csv('work/audit.csv')
# exact rationals
rat = {}
for f in sorted(glob.glob('data/Batch_*/*_BSE.tif')):
    with tifffile.TiffFile(f) as t: rat[os.path.basename(f).split('_')[1]] = t.pages[0].tags['XResolution'].value
F = df[df.det=='BSE'][['batch','fid','H','W']].copy(); F['xres'] = F.fid.map(rat)
F['grp'] = F.groupby(['H','xres']).ngroup()
print(F.sort_values(['grp','batch']).to_string())
load = lambda r: np.load(f'cache/{r.batch}_{r.fid}_BSE.npy').astype(np.float32)[:, 4:-4]
def ncc(a, b):
    a = a - a.mean(); b = b - b.mean(); return float((a*b).sum() / np.sqrt((a*a).sum()*(b*b).sum()) + 1e-9)
print('\n--- edge continuity & overlap for same-H pairs (BSE) ---')
for (h), g in F.groupby('H'):
    if len(g) < 2: continue
    rows = list(g.itertuples())
    ims = {r.fid: load(r) for r in rows}
    for A, B in itertools.permutations(rows, 2):
        a, b = ims[A.fid], ims[B.fid]
        edge = ncc(a[:, -1], b[:, 0])
        # overlap search: A right strip vs B left strip
        sa, sb = a[:, -2000:], b[:, :2000]
        shift, err, _ = phase_cross_correlation(sa[::2, ::2], sb[::2, ::2], normalization=None)
        dy, dx = (shift*2).astype(int)
        # compute ncc at shift on overlap
        if dx > 0: oa, ob = sa[:, dx:], sb[:, :2000-dx]
        else: oa, ob = sa[:, :2000+dx], sb[:, -dx:]
        if dy > 0: oa, ob = oa[dy:], ob[:oa.shape[0]-dy] if False else ob[:-dy]
        elif dy < 0: oa, ob = oa[:dy], ob[-dy:]
        ov = ncc(oa, ob) if oa.size > 1000 else float('nan')
        print(f'H={h} {A.batch}:{A.fid} -> {B.batch}:{B.fid}  edgeNCC={edge:+.3f}  overlap shift=({dy},{dx}) NCC={ov:+.3f}')
