import numpy as np, pandas as pd
from scipy import stats
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40); pd.set_option('display.max_rows', 100)
D = pd.read_csv('work/kpi_tiles.csv')
T = D[D.win == 'all'].copy(); W = D[D.win != 'all'].copy()
K = [c for c in T.columns if c not in ('batch', 'fid', 'src', 'win') and not c.startswith('acq_')]
ACQ = ['acq_contrast_mb', 'acq_matrix_level', 'acq_floor', 'acq_clip0', 'acq_comb', 'acq_noise_rel', 'acq_sharp_rel']
BASE = set(T[T.batch == 'Batch_1'].src)

# 1) variance structure: strips within tile, tiles within source, between sources
rows = []
for k in K:
    x = T[k]; tot = np.nanvar(x)
    src_means = T.groupby('src')[k].mean(); within_src = T.groupby('src')[k].var().dropna().mean()
    strip_var = W.groupby('fid')[k].var().mean()
    icc = np.nanvar(src_means) / (np.nanvar(src_means) + np.nan_to_num(within_src))
    # acquisition confounding at source level
    S = T.groupby('src')[[k] + ACQ].mean()
    rho = {a: stats.spearmanr(S[k], S[a]).correlation for a in ACQ}
    amax = max(rho, key=lambda a: abs(rho[a]) if np.isfinite(rho[a]) else 0)
    rows.append(dict(kpi=k, mean=np.nanmean(x), cv_between_src=np.nanstd(src_means) / abs(np.nanmean(x)),
                     sd_strip_rel=np.sqrt(strip_var) / abs(np.nanmean(x)), icc_src=icc, acq_max=amax.replace('acq_', ''), rho_acq=rho[amax]))
V = pd.DataFrame(rows).sort_values('icc_src', ascending=False)
print(V.round(3).to_string(index=False))

# 2) source-level table (key KPIs) + acquisition
key = ['phi_pore', 'phi_bright', 'bright_ecd_d50', 'bright_n_per_1000um2', 'pore_ecd_areaw', 'solid_chord_x', 'solid_chord_y',
       'solid_chord_ratio', 'interface_density', 'orient_order', 'crack_len_density', 'pore_cv_16um', 'bright_cv_16um', 'pore_horiz_frac']
S = T.groupby('src').agg(batches=('batch', lambda s: ''.join(sorted(set(b[-1] for b in s)))), n=('fid', 'size'),
                         **{k: (k, 'mean') for k in key}, contrast=('acq_contrast_mb', 'mean'), floor=('acq_floor', 'mean'),
                         comb=('acq_comb', 'mean'), noise=('acq_noise_rel', 'mean'), sharp=('acq_sharp_rel', 'mean'))
print('\n', S.round(3).to_string())
# 3) baseline prediction-interval z (t-based, n_base sources)
B = S.loc[sorted(BASE)]
nb = len(B)
Z = pd.DataFrame(index=S.index)
for k in key:
    mu, sd = B[k].mean(), B[k].std(ddof=1)
    Z[k] = (S[k] - mu) / (sd * np.sqrt(1 + 1 / nb))
Z['max|t|'] = Z[key].abs().max(1); Z['driver'] = Z[key].abs().idxmax(1)
tcrit95, tcrit99 = stats.t.ppf(0.975, nb - 1), stats.t.ppf(0.995, nb - 1)
print(f'\nbaseline srcs={sorted(BASE)} n={nb}; t95={tcrit95:.2f} t99={tcrit99:.2f}')
print(Z.round(2).to_string())
