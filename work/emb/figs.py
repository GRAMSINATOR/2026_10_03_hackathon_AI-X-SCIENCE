import os, json
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from sklearn.decomposition import PCA
import matplotlib.patheffects as pe

ROOT = r'C:\Code\2026_10_03_hackathon_AI-X-SCIENCE'; OUT = os.path.join(ROOT, 'work', 'emb'); FEAT = 'mp'
INK, INK2, SURF, GRID = '#0b0b0b', '#52514e', '#fcfcfb', '#e4e3df'
C1, C2, C3 = '#2a78d6', '#eb6834', '#1baf7a'
SEQ = LinearSegmentedColormap.from_list('seq', ['#cde2fb', '#86b6ef', '#3987e5', '#256abf', '#184f95', '#0d366b'])
plt.rcParams.update({'figure.facecolor': SURF, 'axes.facecolor': SURF, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'text.color': INK, 'font.size': 8, 'axes.titlesize': 9})
meta = pd.read_csv(os.path.join(OUT, 'meta.csv'))
Z = np.load(os.path.join(OUT, 'emb_crops.npz'))[FEAT].astype(np.float32); Z /= np.linalg.norm(Z, axis=1, keepdims=True)
R = json.load(open(os.path.join(OUT, f'results_{FEAT}.json')))
BASE = sorted(meta.loc[meta.batch == 'Batch_1', 'src'].unique()); SRCS = sorted(meta.src.unique())
MK = {'Batch_1': 'o', 'Batch_2': 's', 'Batch_3': '^'}

# fig 1: crop-level PCA per channel x normalisation
fig, axs = plt.subplots(2, 3, figsize=(13, 7.5))
for r, norm in enumerate(['raw', 'heq']):
    for c, chan in enumerate(['BSE', 'SEt', 'Inlens']):
        ax = axs[r, c]
        m = ((meta.chan == chan) & (meta.norm == norm) & (meta.scale == 1) & (meta.pert == 'none')).values
        X, M = Z[m], meta[m]
        pca = PCA(2).fit(X); Y = pca.transform(X)
        for b, mk in MK.items():
            for isb, col in [(True, C1), (False, C2)]:
                k = ((M.batch == b) & (M.src.isin(BASE) == isb)).values
                ax.scatter(Y[k, 0], Y[k, 1], s=5, marker=mk, c=col, alpha=0.45, linewidths=0)
        for s in SRCS:
            k = (M.src == s).values
            ax.text(*np.median(Y[k], 0), s, fontsize=7.5, ha='center', va='center', color=INK, fontweight='bold',
                    path_effects=[pe.withStroke(linewidth=2.5, foreground=SURF)])
        res = R[f'{chan}/{norm}']
        ax.set_title(f'{chan} / {norm}:  R²(src) crop={res["crop_R2_src"]:.2f}, tile={res["tile_R2_src"]:.2f}; '
                     f'sil(src)={res["sil_crop_src"]:.2f}', color=INK)
        ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.0f}%)'); ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.0f}%)')
        ax.grid(color=GRID, lw=0.5); ax.set_axisbelow(True)
h = [plt.Line2D([], [], ls='', marker='o', color=C1, label='src with Batch_1 tile (baseline)'),
     plt.Line2D([], [], ls='', marker='o', color=C2, label='src without Batch_1 tile')] + \
    [plt.Line2D([], [], ls='', marker=mk, color=INK2, label=b) for b, mk in MK.items()]
fig.legend(handles=h, loc='upper center', ncol=5, frameon=False, bbox_to_anchor=(0.5, 0.965))
fig.suptitle('DINOv2 ViT-B/14 mean-patch, 448-px crops, PCA per panel: one continuous cloud (crop silhouette by src < 0); src labels at medians', y=0.995, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(os.path.join(OUT, 'fig1_embedding_pca.png'), dpi=130); plt.close(fig)

# fig 2: consistency heatmaps
cz = np.load(os.path.join(OUT, f'consistency_{FEAT}.npz')); names = list(cz['names'])
fig, axs = plt.subplots(1, 2, figsize=(12, 5.2))
for ax, key, ttl in [(axs[0], 'rho_pc1', '|Spearman| of src orderings along src-level PC1'),
                     (axs[1], 'mantel', 'Mantel r (Spearman) between src distance matrices')]:
    A = cz[key]; im = ax.imshow(A, cmap=SEQ, vmin=0, vmax=1)
    for i in range(9):
        for j in range(9):
            ax.text(j, i, f'{A[i, j]:.2f}', ha='center', va='center', fontsize=7, color='white' if A[i, j] > 0.6 else INK)
    ax.set_xticks(range(9), names, rotation=60, ha='right'); ax.set_yticks(range(9), names); ax.set_title(ttl, color=INK)
    for v in (2.5, 5.5): ax.axhline(v, color=SURF, lw=2); ax.axvline(v, color=SURF, lw=2)
fig.colorbar(im, ax=axs, shrink=0.8)
fig.suptitle('Cross-channel / cross-normalisation consistency (13 src centroids)', color=INK)
fig.savefig(os.path.join(OUT, 'fig2_consistency.png'), dpi=130, bbox_inches='tight'); plt.close(fig)

# fig 3: novelty
NZ = pd.read_csv(os.path.join(OUT, f'novelty_z_{FEAT}.csv'), index_col=0)
order = BASE + [s for s in SRCS if s not in BASE]
fig, axs = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
w = 0.26
for ax, chan in zip(axs, ['BSE', 'SEt', 'Inlens']):
    x = np.arange(len(order))
    for k, (norm, col) in enumerate([('raw', C1), ('rz', C2), ('heq', C3)]):
        ax.bar(x + (k - 1) * w, NZ.loc[order, f'{chan}/{norm}'], width=w - 0.03, color=col, label=norm)
    ax.axhline(2, color=INK2, ls='--', lw=1); ax.axhline(0, color=INK2, lw=0.6)
    ax.axvspan(-0.5, len(BASE) - 0.5, color='#f0efec', zorder=-1)
    ax.set_ylabel(f'{chan}\nnovelty z'); ax.grid(axis='y', color=GRID, lw=0.5); ax.set_axisbelow(True)
axs[0].legend(ncol=3, frameon=False, loc='upper left', title='input normalisation')
axs[0].text(len(BASE) / 2 - 0.5, axs[0].get_ylim()[1] * 0.9, 'baseline srcs (LOO null)', ha='center', color=INK2)
axs[-1].set_xticks(np.arange(len(order)), order, rotation=0)
fig.suptitle('kNN (k=5) distance of src crops to Batch_1 crops of other srcs, z vs baseline leave-src-out; dashed z=2', color=INK)
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'fig3_novelty.png'), dpi=130); plt.close(fig)
print('figs saved')
