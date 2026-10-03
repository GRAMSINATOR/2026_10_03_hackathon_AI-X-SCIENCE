import sys, numpy as np, pandas as pd
from scipy import ndimage as ndi
from multiprocessing import Pool
sys.path.insert(0, 'work'); from seg import load, segment; from kpi import kpis
KEY = ['phi_pore_macro','solid_macro_chord_x','solid_macro_chord_y','pore_macro_chord_x','interface_density_macro','phi_pore','phi_bright','bright_ecd_d50','bright_n_per_1000um2','pore_ecd_areaw','solid_chord_x','solid_chord_y','interface_density','orient_order','pore_horiz_frac','crack_len_density']
rng = np.random.default_rng(0)
P = {'none': lambda x: x, 'bright+20': lambda x: np.clip(x + 20, 0, 255), 'contrast0.7': lambda x: np.clip((x - x.mean())*0.7 + x.mean(), 0, 255),
     'contrast1.3': lambda x: np.clip((x - x.mean())*1.3 + x.mean(), 0, 255), 'gamma0.7': lambda x: 255*(x/255)**0.7, 'gamma1.4': lambda x: 255*(x/255)**1.4,
     'blur1.5': lambda x: ndi.gaussian_filter(x, 1.5), 'noise8': lambda x: np.clip(x + rng.normal(0, 8, x.shape), 0, 255),
     'stretch_comb': lambda x: np.clip(np.round(x/2)*2*1.0, 0, 255), 'floor20': lambda x: np.clip(x*0.85 + 22, 0, 255),
     'halfres': lambda x: ndi.zoom(ndi.zoom(x, 0.5, order=1), 2, order=1)[:x.shape[0], :x.shape[1]]}
def run(a):
    b, f, pn = a; x = load(b, f, 'BSE')[:, 1500:5500]; y = P[pn](x).astype(np.float32)
    lab, s, an = segment(y); k = kpis(lab, s, an); return dict(fid=f, pert=pn, **{kk: k[kk] for kk in KEY})
if __name__ == '__main__':
    tiles = [('Batch_1','ffwubibz'), ('Batch_1','f1vzngrs'), ('Batch_1','iv6g2oq0')]
    with Pool(12) as pool: R = pd.DataFrame(pool.map(run, [(b, f, p) for b, f in tiles for p in P]))
    T = pd.read_csv('work/kpi_tiles.csv'); T = T[T.win == 'all']
    sd_between = T[T.batch == 'Batch_1'].groupby('src')[KEY].mean().drop(index='S2316').std()
    print(sd_between.round(4).to_string())
    base = R[R.pert == 'none'].set_index('fid')[KEY]
    out = {}
    for pn in P:
        if pn == 'none': continue
        d = (R[R.pert == pn].set_index('fid')[KEY] - base).abs().mean() / sd_between; out[pn] = d
    print('mean |KPI shift| / baseline between-micrograph SD (excl. S2316):')
    print(pd.DataFrame(out).T.round(2).to_string())
