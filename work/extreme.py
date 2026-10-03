import numpy as np, pandas as pd
from skimage import measure, morphology
from multiprocessing import Pool
PX = 0.025
S = pd.read_csv('work/sources.csv')
def run(r):
    b, f, s = r; lab = np.load(f'cache/lab_{b}_{f}.npy'); A_mm2 = lab.size * PX**2 / 1e6
    out = dict(src=s, batch=b, fid=f)
    pore = lab == 0; rp = measure.regionprops(measure.label(pore))
    L = np.array([p.axis_major_length * PX for p in rp]); O = np.array([abs(abs(p.orientation) - np.pi/2) < np.pi/9 for p in rp])
    W = np.array([p.axis_minor_length * PX for p in rp])
    crack = (L > 15) & O & (L / np.maximum(W, 1e-3) > 6)
    out.update(pore_len_max=L.max(), n_long_hcrack_per_mm2=crack.sum() / A_mm2, long_hcrack_len_sum_per_mm2=L[crack].sum() / A_mm2)
    br = measure.regionprops(measure.label(lab == 2)); E = np.array([2*np.sqrt(p.area/np.pi)*PX for p in br])
    out.update(bright_ecd_max=E.max(), n_bright_gt5um_per_mm2=(E > 5).sum() / A_mm2)
    solid = morphology.binary_opening(lab != 0, morphology.disk(3))
    sp = measure.regionprops(measure.label(lab == 1)); Es = np.sort([2*np.sqrt(p.area/np.pi)*PX for p in sp])[::-1]
    out.update(matrix_region_ecd_top3=np.mean(Es[:3]))
    return out
if __name__ == '__main__':
    with Pool(10) as P: X = pd.DataFrame(P.map(run, [tuple(x) for x in S[['batch','fid','src']].values]))
    X.to_csv('work/extreme.csv', index=False)
    pd.set_option('display.width', 200)
    print(X.sort_values(['src','batch']).round(2).to_string(index=False))
