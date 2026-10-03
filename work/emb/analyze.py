"""Latent-structure / pseudotime tests on DINOv2 crop embeddings. Usage: analyze.py [mp|cls]"""
import os, sys, json, warnings, itertools
import numpy as np, pandas as pd
from scipy.stats import spearmanr, pearsonr
from scipy.spatial.distance import pdist, squareform, cdist
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, roc_auc_score
warnings.filterwarnings('ignore')

FEAT = sys.argv[1] if len(sys.argv) > 1 else 'mp'
ROOT = r'C:\Code\2026_10_03_hackathon_AI-X-SCIENCE'
OUT = os.environ.get('EMB_DIR', os.path.join(ROOT, 'work', 'emb'))
meta = pd.read_csv(os.path.join(OUT, 'meta.csv'))
for _c in ['batch', 'fid', 'det', 'chan', 'src', 'norm', 'pert']: meta[_c] = np.array(meta[_c].tolist(), dtype=object)
ZZ = np.load(os.path.join(OUT, 'emb_crops.npz'))[FEAT].astype(np.float32)
ZZ /= np.linalg.norm(ZZ, axis=1, keepdims=True)
audit = pd.read_csv(os.path.join(ROOT, 'work', 'audit.csv'))
audit['chan'] = audit.det.map({'BSE': 'BSE', 'Inlens': 'Inlens', 'ETD': 'SEt', 'SE': 'SEt'})
CHANS, NORMS, STATS = ['BSE', 'SEt', 'Inlens'], ['raw', 'rz', 'heq'], ['mean', 'std', 'p1', 'p99', 'n_unique']
SRCS = sorted(meta.src.unique())
BASE = sorted(meta.loc[meta.batch == 'Batch_1', 'src'].unique())
isbase = np.array([s in BASE for s in SRCS])
rng = np.random.default_rng(0)
ar = lambda a, b: abs(spearmanr(a, b)[0])


def sub(chan, norm, scale=1, pert='none'):
    m = ((meta.chan == chan) & (meta.norm == norm) & (meta.scale == scale) & (meta.pert == pert)).values
    return ZZ[m], meta[m].reset_index(drop=True)


def r2(X, lab):
    lab = np.asarray(lab); sst = ((X - X.mean(0)) ** 2).sum()
    return 1 - sum(((X[lab == g] - X[lab == g].mean(0)) ** 2).sum() for g in np.unique(lab)) / sst


def cents(X, lab, keys):
    lab = np.asarray(lab); return np.stack([X[lab == k].mean(0) for k in keys])


def diffmap(X, knn=None):
    D = squareform(pdist(X))
    if knn is None:
        K = np.exp(-D ** 2 / np.median(D[np.triu_indices(len(D), 1)]) ** 2)
    else:
        s = np.sort(D, 1)[:, knn]; K = np.exp(-D ** 2 / np.outer(s, s))
    q = K.sum(1); K = K / np.outer(q, q)
    d = K.sum(1); A = K / np.sqrt(np.outer(d, d))
    w, u = np.linalg.eigh(A); o = np.argsort(w)[::-1]; w, u = w[o], u[:, o]
    psi = u / np.sqrt(d)[:, None]; psi = psi / psi[:, [0]]
    return psi[:, 1] * w[1]


def pc1(X):
    return PCA(3).fit(X).transform(X)[:, 0]


def mantel(D1, D2, nperm=4999):
    iu = np.triu_indices(len(D1), 1)
    a = pd.Series(D1[iu]).rank().values; a = (a - a.mean()) / a.std()
    R2 = np.zeros_like(D2); R2[iu] = pd.Series(D2[iu]).rank().values; R2 = R2 + R2.T
    def rr(M):
        b = M[iu]; b = (b - b.mean()) / b.std(); return (a * b).mean()
    r0 = rr(R2); null = np.array([rr(R2[p][:, p]) for p in (rng.permutation(len(D2)) for _ in range(nperm))])
    return r0, (1 + (null >= r0).sum()) / (nperm + 1)


def eta2(v, lab):
    return r2(v[:, None], lab)


R = {}          # per (chan,norm) results
SRCCOORD = {}   # (chan,norm) -> dict of src-level coordinates & dist matrix
for chan, norm in itertools.product(CHANS, NORMS):
    X, M = sub(chan, norm)
    tiles = sorted(M.fid.unique()); tsrc = M.groupby('fid').src.first()[tiles].to_numpy(dtype=object)
    tbat = M.groupby('fid').batch.first()[tiles].to_numpy(dtype=object)
    T = cents(X, M.fid, tiles); T /= np.linalg.norm(T, axis=1, keepdims=True)
    res = {}
    # 3. variance structure
    sb = (M.src + '|' + M.batch).values; tsb = np.array([f'{a}|{b}' for a, b in zip(tsrc, tbat)])
    res['crop_R2_src'], res['crop_R2_batch'] = r2(X, M.src), r2(X, M.batch)
    res['crop_R2_batch|src'] = r2(X, sb) - res['crop_R2_src']
    res['crop_R2_tile'] = r2(X, M.fid)
    res['tile_R2_src'], res['tile_R2_batch'] = r2(T, tsrc), r2(T, tbat)
    res['tile_R2_batch|src'] = r2(T, tsb) - res['tile_R2_src']
    nul = [r2(T, rng.permutation(tsrc)) for _ in range(999)]
    res['tile_R2_src_p'] = (1 + np.sum(np.array(nul) >= res['tile_R2_src'])) / 1000
    def perm_within(lab_b, lab_s):
        out = lab_b.copy()
        for s in np.unique(lab_s):
            ii = np.where(lab_s == s)[0]; out[ii] = rng.permutation(out[ii])
        return out
    nul = [r2(T, np.array([f'{a}|{b}' for a, b in zip(tsrc, perm_within(tbat, tsrc))])) - res['tile_R2_src'] for _ in range(999)]
    res['tile_R2_batch|src_p'] = (1 + np.sum(np.array(nul) >= res['tile_R2_batch|src'] - 1e-12)) / 1000
    res['sil_crop_src'] = silhouette_score(X, M.src, metric='cosine')
    res['sil_crop_batch'] = silhouette_score(X, M.batch, metric='cosine')
    res['sil_tile_src'] = silhouette_score(T, tsrc, metric='cosine')
    res['sil_tile_batch'] = silhouette_score(T, tbat, metric='cosine')
    # src-level coordinates
    C = cents(X, M.src, SRCS); D = squareform(pdist(C))
    p1, d1 = pc1(C), diffmap(C)
    res['src_pc1_evr'] = PCA(3).fit(C).explained_variance_ratio_[0]
    # 5a. LOO-src stability
    loo_p, loo_d = [], []
    for k in range(len(SRCS)):
        keep = np.arange(len(SRCS)) != k
        loo_p.append(ar(pc1(C[keep]), p1[keep])); loo_d.append(ar(diffmap(C[keep]), d1[keep]))
    res['loo_pc1_med'], res['loo_pc1_min'] = np.median(loo_p), np.min(loo_p)
    res['loo_dc1_med'], res['loo_dc1_min'] = np.median(loo_d), np.min(loo_d)
    # bootstrap over crops and over tiles (within src)
    bs_p, bs_d, bt_p = [], [], []
    srci = {s: np.where(M.src.to_numpy(dtype=object) == s)[0] for s in SRCS}
    tilei = {t: np.where(M.fid.to_numpy(dtype=object) == t)[0] for t in tiles}
    src_tiles = {s: [t for t, ss in zip(tiles, tsrc) if ss == s] for s in SRCS}
    for b in range(200):
        Cb = np.stack([X[rng.choice(srci[s], len(srci[s]))].mean(0) for s in SRCS])
        bs_p.append(ar(pc1(Cb), p1)); bs_d.append(ar(diffmap(Cb), d1))
        Ct = np.stack([np.concatenate([X[tilei[t]] for t in rng.choice(src_tiles[s], len(src_tiles[s]))]).mean(0) for s in SRCS])
        bt_p.append(ar(pc1(Ct), p1))
    res['boot_crop_pc1_med'], res['boot_crop_pc1_p5'] = np.median(bs_p), np.percentile(bs_p, 5)
    res['boot_crop_dc1_med'], res['boot_crop_dc1_p5'] = np.median(bs_d), np.percentile(bs_d, 5)
    res['boot_tile_pc1_med'], res['boot_tile_pc1_p5'] = np.median(bt_p), np.percentile(bt_p, 5)
    # 5d. baseline at one end
    auc = roc_auc_score(isbase, p1); res['auc_base_pc1'] = max(auc, 1 - auc)
    auc = roc_auc_score(isbase, d1); res['auc_base_dc1'] = max(auc, 1 - auc)
    # 5c. acquisition stats (src level and tile level)
    A = audit[audit.chan == chan].merge(meta[['batch', 'fid', 'src']].drop_duplicates(), on=['batch', 'fid'])
    As = A.groupby('src')[STATS].mean().loc[SRCS]
    rs = {st: spearmanr(p1, As[st])[0] for st in STATS}
    res['acq_src_pc1'] = rs
    At = A.set_index('fid').loc[tiles, STATS]
    tp1 = pc1(T); rt = {st: spearmanr(tp1, At[st])[0] for st in STATS}
    res['acq_tile_pc1'] = rt
    res['tile_pc1_evr'] = PCA(3).fit(T).explained_variance_ratio_[0]
    res['tile_pc1_eta2_src'] = eta2(tp1, tsrc)
    # crop-level PC1 / DC1 dominated by src?
    cp1 = pc1(X); cd1 = diffmap(X, knn=10)
    res['crop_pc1_eta2_src'], res['crop_dc1_eta2_src'] = eta2(cp1, M.src.to_numpy(dtype=object)), eta2(cd1, M.src.to_numpy(dtype=object))
    res['crop_pc1_eta2_tile'] = eta2(cp1, M.fid.to_numpy(dtype=object))
    Ac = A.set_index('fid').loc[M.fid, STATS].values
    res['acq_crop_pc1_maxabs'] = max(abs(spearmanr(cp1, Ac[:, j])[0]) for j in range(len(STATS)))
    # local crop stats (mean, std of crop) vs crop PC1 -> per-crop brightness axis?
    # 5e. continuum vs clusters: leave-tile-out kNN on crops
    Dc = cdist(X, X); same_tile = M.fid.to_numpy(dtype=object)[:, None] == M.fid.to_numpy(dtype=object)[None, :]; Dc[same_tile] = np.inf
    nn = np.argsort(Dc, 1)[:, :10]
    multi = M.src.map(M.groupby('src').fid.nunique()).values > 1
    nsrc = M.src.to_numpy(dtype=object)[nn]; own = M.src.to_numpy(dtype=object)[:, None]
    res['knn10_srcpurity'] = (nsrc[multi] == own[multi]).mean()
    res['nn1_srcpurity'] = (nsrc[multi, 0] == own[multi, 0]).mean()
    cnt_src = M.src.value_counts(); cnt_tile = M.fid.value_counts()
    chance = ((M.src.map(cnt_src) - M.fid.map(cnt_tile)) / (len(M) - M.fid.map(cnt_tile))).values
    res['knn_chance'] = chance[multi].mean()
    # tile-level vote
    ok = []
    for t in tiles:
        ii = tilei[t]
        if not multi[ii[0]]: continue
        v = pd.Series(nsrc[ii].ravel()).value_counts().index[0]; ok.append(v == M.src.to_numpy(dtype=object)[ii[0]])
    res['tile_vote_src_acc'] = np.mean(ok); res['n_tiles_vote'] = len(ok)
    # 6. novelty vs Batch_1 (leave-src-out, reference size matched)
    isB1 = (M.batch == 'Batch_1').values
    nov = {}
    for s in SRCS:
        q = X[M.src.to_numpy(dtype=object) == s]
        refs = [r for r in BASE if r != s] if s in BASE else None
        if s in BASE:
            sets = [refs]
        else:  # drop one baseline src at a time so reference has 5 srcs like baseline LOO
            sets = [[r for r in BASE if r != d] for d in BASE]
        sc = []
        for rs_ in sets:
            ref = X[isB1 & M.src.isin(rs_).values]
            dd = np.sort(cdist(q, ref), 1)[:, :5].mean(1); sc.append(np.median(dd))
        nov[s] = float(np.mean(sc))
    null = np.array([nov[s] for s in BASE])
    res['nov_raw'] = nov
    res['nov_z'] = {s: (nov[s] - null.mean()) / null.std(ddof=1) for s in SRCS}
    res['nov_ratio'] = {s: nov[s] / np.median(null) for s in SRCS}
    # perturbation reference distances
    res['d_between_src_cent_med'] = np.median(D[np.triu_indices(len(D), 1)])
    Ctile = cents(X, M.fid, tiles)
    wt = [np.linalg.norm(Ctile[i] - Ctile[j]) for i, j in itertools.combinations(range(len(tiles)), 2) if tsrc[i] == tsrc[j]]
    res['d_within_src_tilecent_med'] = np.median(wt)
    R[(chan, norm)] = res
    SRCCOORD[(chan, norm)] = dict(pc1=p1, dc1=d1, D=D, C=C)
    print(chan, norm, 'done', flush=True)

# 2. perturbation sensitivity
prow = []
for chan, norm in itertools.product(CHANS, NORMS):
    X, M = sub(chan, norm)
    key = M.fid + '_' + M.r.astype(str) + '_' + M.c.astype(str)
    lut = dict(zip(key, range(len(M))))
    tiles = sorted(M.fid.unique()); Ctile = cents(X, M.fid, tiles)
    C = SRCCOORD[(chan, norm)]['C']
    for pert in sorted(meta.pert.unique()):
        if pert == 'none': continue
        Xp, Mp = sub(chan, norm, pert=pert)
        for fid in Mp.fid.unique():
            ii = np.where(Mp.fid.to_numpy(dtype=object) == fid)[0]
            jj = [lut[f'{fid}_{r}_{c}'] for r, c in zip(Mp.r.values[ii], Mp.c.values[ii])]
            shift = np.linalg.norm(Xp[ii].mean(0) - X[jj].mean(0))
            cropshift = np.median(np.linalg.norm(Xp[ii] - X[jj], axis=1))
            s = Mp.src.to_numpy(dtype=object)[ii[0]]
            # nearest src centroid (own src centroid computed without this tile)
            Cl = C.copy(); k = SRCS.index(s)
            others = (M.src.to_numpy(dtype=object) == s) & (M.fid.to_numpy(dtype=object) != fid)
            Cl[k] = X[others].mean(0)
            nearest_orig = SRCS[np.argmin(np.linalg.norm(Cl - X[jj].mean(0), axis=1))]
            nearest_pert = SRCS[np.argmin(np.linalg.norm(Cl - Xp[ii].mean(0), axis=1))]
            prow.append(dict(chan=chan, norm=norm, pert=pert, fid=fid, src=s, cent_shift=shift, crop_shift=cropshift,
                             ratio_between=shift / R[(chan, norm)]['d_between_src_cent_med'],
                             ratio_within=shift / R[(chan, norm)]['d_within_src_tilecent_med'],
                             own_nearest_orig=nearest_orig == s, own_nearest_pert=nearest_pert == s))
P = pd.DataFrame(prow); P.to_csv(os.path.join(OUT, f'perturb_{FEAT}.csv'), index=False)

# 4/5b. cross-channel & cross-normalisation consistency
combos = list(itertools.product(CHANS, NORMS))
names = [f'{c}/{n}' for c, n in combos]
RHO_P = np.ones((9, 9)); RHO_D = np.ones((9, 9)); MAN = np.ones((9, 9)); MANP = np.zeros((9, 9))
for i, j in itertools.combinations(range(9), 2):
    a, b = SRCCOORD[combos[i]], SRCCOORD[combos[j]]
    RHO_P[i, j] = RHO_P[j, i] = ar(a['pc1'], b['pc1']); RHO_D[i, j] = RHO_D[j, i] = ar(a['dc1'], b['dc1'])
    MAN[i, j], MANP[i, j] = mantel(a['D'], b['D'], 1999); MAN[j, i], MANP[j, i] = MAN[i, j], MANP[i, j]

# ---------- print compact summary ----------
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
f3 = lambda v: f'{v:.2f}'
print(f'\n===== FEAT={FEAT}  n_crops per chan/norm ~{len(sub("BSE","raw")[1])}  baseline srcs={BASE}')
cols = ['crop_R2_src', 'crop_R2_batch', 'crop_R2_batch|src', 'crop_R2_tile', 'tile_R2_src', 'tile_R2_src_p', 'tile_R2_batch',
        'tile_R2_batch|src', 'tile_R2_batch|src_p', 'sil_crop_src', 'sil_crop_batch', 'sil_tile_src', 'sil_tile_batch',
        'knn10_srcpurity', 'nn1_srcpurity', 'knn_chance', 'tile_vote_src_acc']
T1 = pd.DataFrame({f'{c}/{n}': {k: R[(c, n)][k] for k in cols} for c, n in combos}).T
print(T1.round(3).to_string())
cols2 = ['src_pc1_evr', 'loo_pc1_med', 'loo_pc1_min', 'loo_dc1_med', 'loo_dc1_min', 'boot_crop_pc1_med', 'boot_crop_pc1_p5',
         'boot_crop_dc1_p5', 'boot_tile_pc1_med', 'boot_tile_pc1_p5', 'auc_base_pc1', 'auc_base_dc1', 'tile_pc1_evr',
         'tile_pc1_eta2_src', 'crop_pc1_eta2_src', 'crop_pc1_eta2_tile', 'crop_dc1_eta2_src', 'acq_crop_pc1_maxabs']
T2 = pd.DataFrame({f'{c}/{n}': {k: R[(c, n)][k] for k in cols2} for c, n in combos}).T
print(T2.round(3).to_string())
print('\nacq stats Spearman vs src-PC1 (13 srcs) | tile-PC1 (31 tiles):')
for c, n in combos:
    a, b = R[(c, n)]['acq_src_pc1'], R[(c, n)]['acq_tile_pc1']
    print(f'  {c}/{n}: src ' + ' '.join(f'{k}={a[k]:+.2f}' for k in STATS) + ' | tile ' + ' '.join(f'{k}={b[k]:+.2f}' for k in STATS))
print('\n|rho| PC1 src-orderings across chan/norm:'); print(pd.DataFrame(RHO_P, names, names).round(2).to_string())
print('\n|rho| DC1 src-orderings across chan/norm:'); print(pd.DataFrame(RHO_D, names, names).round(2).to_string())
print('\nMantel r (Spearman) src distance matrices:'); print(pd.DataFrame(MAN, names, names).round(2).to_string())
print('Mantel p:'); print(pd.DataFrame(MANP, names, names).round(4).to_string())
print('\nPerturbation: median centroid shift / median between-src centroid dist (ratio_between), / within-src tile dist (ratio_within)')
print(P.groupby(['norm', 'pert'])[['ratio_between', 'ratio_within']].median().unstack(0).round(2).to_string())
print('own-src nearest  orig:', P.groupby('norm').own_nearest_orig.mean().round(2).to_dict(),
      ' pert:', P.groupby('norm').own_nearest_pert.mean().round(2).to_dict())
print(P.groupby(['norm'])[['ratio_between']].agg(['median', 'max']).round(2).to_string())
print('\nNovelty z (vs 6 baseline-src LOO null); rows=src, cols=chan/norm')
NZ = pd.DataFrame({f'{c}/{n}': R[(c, n)]['nov_z'] for c, n in combos}).loc[SRCS]
NZ.insert(0, 'base', [s in BASE for s in SRCS])
print(NZ.round(1).to_string())
NR = pd.DataFrame({f'{c}/{n}': R[(c, n)]['nov_ratio'] for c, n in combos}).loc[SRCS]
print('Novelty ratio (score / median baseline LOO score)'); print(NR.round(2).to_string())
NZ.to_csv(os.path.join(OUT, f'novelty_z_{FEAT}.csv')); NR.to_csv(os.path.join(OUT, f'novelty_ratio_{FEAT}.csv'))
print('\nsrc PC1 orderings (raw / heq):')
for c in CHANS:
    for n in ['raw', 'heq']:
        p = SRCCOORD[(c, n)]['pc1']; o = np.argsort(p)
        print(f'  {c}/{n}: ' + ' < '.join(SRCS[k] + ('*' if SRCS[k] in BASE else '') for k in o))
T1.to_csv(os.path.join(OUT, f'variance_{FEAT}.csv')); T2.to_csv(os.path.join(OUT, f'pseudotime_{FEAT}.csv'))
np.savez(os.path.join(OUT, f'consistency_{FEAT}.npz'), names=names, rho_pc1=RHO_P, rho_dc1=RHO_D, mantel=MAN, mantel_p=MANP)

# scale-2 (context) quick summary
print('\nScale-2 (896px->448) context crops:')
for c, n in [(c, n) for c in CHANS for n in ['raw', 'heq']]:
    X, M = sub(c, n, scale=2)
    tiles = sorted(M.fid.unique()); T = cents(X, M.fid, tiles); T /= np.linalg.norm(T, axis=1, keepdims=True)
    tsrc = M.groupby('fid').src.first()[tiles].to_numpy(dtype=object)
    print(f'  {c}/{n}: crop R2 src={r2(X, M.src):.2f} batch={r2(X, M.batch):.2f}  tile R2 src={r2(T, tsrc):.2f}  sil_crop_src={silhouette_score(X, M.src, metric="cosine"):.2f}')
json.dump({f'{c}/{n}': {k: (v if not isinstance(v, (np.floating, np.integer)) else float(v)) for k, v in R[(c, n)].items()} for c, n in combos},
          open(os.path.join(OUT, f'results_{FEAT}.json'), 'w'), default=float, indent=1)
