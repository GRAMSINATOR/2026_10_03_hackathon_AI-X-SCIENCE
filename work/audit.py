import tifffile, glob, os, json, numpy as np, pandas as pd
rows = []
for f in sorted(glob.glob('data/Batch_*/*.tif')):
    b = os.path.basename(os.path.dirname(f)); name = os.path.basename(f)[:-4]
    _, fid, det = name.split('_')
    with tifffile.TiffFile(f) as t:
        p = t.pages[0]
        xr = p.tags['XResolution'].value; yr = p.tags['YResolution'].value
        desc = p.tags['ImageDescription'].value if 'ImageDescription' in p.tags else ''
        a = p.asarray()
    same_rg = bool(np.array_equal(a[...,0], a[...,1])); same_rb = bool(np.array_equal(a[...,0], a[...,2]))
    g = a[...,0] if (same_rg and same_rb) else a.mean(-1).astype(np.uint8)
    np.save(f'cache/{b}_{fid}_{det}.npy', g)
    px_nm = 25.4e7 / (xr[0]/xr[1])
    h = np.bincount(g.ravel(), minlength=256)
    rows.append(dict(batch=b, fid=fid, det=det, H=a.shape[0], W=a.shape[1], px_nm=round(px_nm,4), py_nm=round(25.4e7/(yr[0]/yr[1]),4),
        rgb_identical=same_rg and same_rb, maxdiff=int(np.abs(a.astype(int)[...,0]-a[...,1]).max()), desc=desc,
        mean=float(g.mean()), std=float(g.std()), p1=int(np.searchsorted(np.cumsum(h), 0.01*g.size)), p99=int(np.searchsorted(np.cumsum(h), 0.99*g.size)),
        n_unique=int((h>0).sum()), frac0=float(h[0]/g.size), frac255=float(h[255]/g.size), size_mb=round(os.path.getsize(f)/1e6,1)))
df = pd.DataFrame(rows); df.to_csv('work/audit.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 200)
print(df.drop(columns=['desc']).to_string())
print(df.desc.unique()[:10])
