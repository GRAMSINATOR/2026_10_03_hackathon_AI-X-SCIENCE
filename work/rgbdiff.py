import tifffile, glob, os, numpy as np
for f in sorted(glob.glob('data/Batch_*/*_BSE.tif')):
    a = tifffile.imread(f).astype(int)
    d = (a[...,0]!=a[...,1]) | (a[...,0]!=a[...,2])
    if d.any():
        ys, xs = np.nonzero(d)
        cols = a[d]; u, c = np.unique(cols, axis=0, return_counts=True)
        top = u[np.argsort(-c)[:4]].tolist()
        print(os.path.basename(f), 'ndiff', d.sum(), 'bbox y', ys.min(), ys.max(), 'x', xs.min(), xs.max(), 'topcolors', top)
