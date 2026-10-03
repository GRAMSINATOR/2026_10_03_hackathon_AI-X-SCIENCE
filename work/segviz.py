import numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, sys
sys.path.insert(0, 'work'); from seg import load, segment
S = pd.read_csv('work/sources.csv')
picks = [('S2316',0), ('S2060',0), ('S2088',0), ('S1880',0), ('S1904',0), ('S2068',0)]
fig, axes = plt.subplots(len(picks), 2, figsize=(20, 5.2*len(picks)))
for i, (s, k) in enumerate(picks):
    r = S[S.src==s].iloc[k]; bse = load(r.batch, r.fid, 'BSE'); lab, a = segment(bse)
    y0, x0 = bse.shape[0]//2 - 500, 2600; crop = bse[y0:y0+1000, x0:x0+1500]; L = lab[y0:y0+1000, x0:x0+1500]
    rgb = np.stack([crop]*3, -1)/255.; ov = rgb.copy(); ov[L==0] = [0.1, 0.3, 1.0]; ov[L==2] = [1.0, 0.5, 0.0]
    axes[i,0].imshow(crop, cmap='gray', vmin=0, vmax=200); axes[i,0].set_title(f'{s} {r.batch} {r.fid}  m={a["m"]:.0f} b={a["b"]:.0f} v={a["v"]:.0f} peak_ok={a["peak_ok"]}'); axes[i,0].axis('off')
    axes[i,1].imshow(0.55*rgb + 0.45*ov); axes[i,1].set_title(f'pore={np.mean(lab==0):.3f}  bright={np.mean(lab==2):.3f} (whole tile)'); axes[i,1].axis('off')
plt.tight_layout(); plt.savefig('work/viz/segcheck.png', dpi=50)
