"""DINOv2 ViT-B/14 crop embeddings for all tiles x channels x normalisation variants,
plus a synthetic-perturbation set. Outputs: work/emb/emb_crops.npz + work/emb/meta.csv"""
import os, glob, time
import numpy as np, pandas as pd, torch, timm
from scipy.ndimage import gaussian_filter

ROOT = r'C:\Code\2026_10_03_hackathon_AI-X-SCIENCE'
OUT = os.path.join(ROOT, 'work', 'emb')
CROP, EDGE, BS = 448, 8, 32
NORMS = ['raw', 'rz', 'heq']
src_df = pd.read_csv(os.path.join(ROOT, 'work', 'sources.csv'))
SRC = {(r.batch, r.fid): r.src for r in src_df.itertuples()}
CH = {'BSE': 'BSE', 'Inlens': 'Inlens', 'ETD': 'SEt', 'SE': 'SEt'}

dev = 'cuda'
model = timm.create_model('vit_base_patch14_dinov2.lvd142m', pretrained=True, img_size=CROP,
                          num_classes=0).to(dev).eval()
NP = model.num_prefix_tokens
MEAN = torch.tensor([0.485, 0.456, 0.406], device=dev).view(1, 3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225], device=dev).view(1, 3, 1, 1)


def normalise(u8, mode):
    """u8: edge-cropped uint8 tile -> float32 [0,1]; stats computed per image."""
    x = u8.astype(np.float32)
    if mode == 'raw':
        return x / 255.
    if mode == 'rz':  # robust z-score, +-3 robust sigma -> [0,1]
        p25, p50, p75 = np.percentile(x, [25, 50, 75])
        s = max((p75 - p25) / 1.349, 1.0)
        return np.clip(0.5 + (x - p50) / (6 * s), 0, 1)
    if mode == 'heq':  # mid-rank histogram equalisation (invariant to monotone grey maps)
        h = np.bincount(u8.ravel(), minlength=256).astype(np.float64)
        lut = ((np.cumsum(h) - h / 2) / h.sum()).astype(np.float32)
        return lut[u8]
    raise ValueError(mode)


def grid(H, W, size):
    nr, nc = H // size, W // size
    y0, x0 = (H - nr * size) // 2, (W - nc * size) // 2
    return [(y0 + i * size, x0 + j * size, i, j) for i in range(nr) for j in range(nc)]


@torch.no_grad()
def embed(crops):
    cls_l, mp_l = [], []
    for k in range(0, len(crops), BS):
        t = torch.from_numpy(np.stack(crops[k:k + BS]).astype(np.float32)).to(dev).unsqueeze(1).expand(-1, 3, -1, -1)
        t = (t - MEAN) / STD
        with torch.autocast('cuda', dtype=torch.float16):
            tok = model.forward_features(t)
        cls_l.append(tok[:, 0].float().cpu().numpy())
        mp_l.append(tok[:, NP:].float().mean(1).cpu().numpy())
    return np.concatenate(cls_l), np.concatenate(mp_l)


def crops_of(xn, scale):
    out, pos = [], []
    size = CROP * scale
    for (y, x, i, j) in grid(*xn.shape, size):
        c = xn[y:y + size, x:x + size]
        if scale > 1:
            c = c.reshape(CROP, scale, CROP, scale).mean((1, 3))
        out.append(np.ascontiguousarray(c, dtype=np.float32)); pos.append((y, x, i, j))
    return out, pos


def perturb(u8, kind, rng):
    x = u8.astype(np.float32)
    if kind == 'b+20': x = x + 20
    elif kind == 'b-20': x = x - 20
    elif kind == 'c0.7': x = x.mean() + 0.7 * (x - x.mean())
    elif kind == 'c1.3': x = x.mean() + 1.3 * (x - x.mean())
    elif kind == 'g0.7': x = 255 * (x / 255) ** 0.7
    elif kind == 'g1.4': x = 255 * (x / 255) ** 1.4
    elif kind == 'blur1.5': x = gaussian_filter(x, 1.5)
    elif kind == 'noise10': x = x + rng.normal(0, 10, x.shape)
    return np.clip(np.round(x), 0, 255).astype(np.uint8)


PERTS = ['b+20', 'b-20', 'c0.7', 'c1.3', 'g0.7', 'g1.4', 'blur1.5', 'noise10']
PERT_FIDS = ['4ih2ggld', 'f1vzngrs', '71vgq3fw', '9luzk4jm', 'rxax5ozo', '0grcilhi']  # S2316,S2148,S2060,S2088,S2068,S1904

meta, CLS, MP = [], [], []
t0 = time.time()
files = sorted(glob.glob(os.path.join(ROOT, 'cache', '*.npy')))
for f in files:
    b, n, fid, det = os.path.basename(f)[:-4].split('_')
    batch = f'{b}_{n}'
    u8 = np.load(f)[:, EDGE:-EDGE]
    base = dict(batch=batch, fid=fid, det=det, chan=CH[det], src=SRC[(batch, fid)])
    for norm in NORMS:
        xn = normalise(u8, norm)
        for scale in (1, 2):
            cr, pos = crops_of(xn, scale)
            c, m = embed(cr)
            CLS.append(c); MP.append(m)
            meta += [dict(base, norm=norm, scale=scale, pert='none', y=p[0], x=p[1], r=p[2], c=p[3]) for p in pos]
    # perturbation set (native scale, fixed subset of 24 crops)
    if fid in PERT_FIDS:
        rng = np.random.default_rng(0)
        g = grid(*u8.shape, CROP)
        sel = sorted(rng.choice(len(g), size=min(24, len(g)), replace=False))
        for kind in PERTS:
            up = perturb(u8, kind, rng)
            for norm in NORMS:
                xn = normalise(up, norm)
                cr = [np.ascontiguousarray(xn[g[k][0]:g[k][0] + CROP, g[k][1]:g[k][1] + CROP]) for k in sel]
                c, m = embed(cr)
                CLS.append(c); MP.append(m)
                meta += [dict(base, norm=norm, scale=1, pert=kind, y=g[k][0], x=g[k][1], r=g[k][2], c=g[k][3]) for k in sel]
    print(f'{os.path.basename(f)} done, n={len(meta)}, {time.time()-t0:.0f}s', flush=True)

meta = pd.DataFrame(meta)
meta.to_csv(os.path.join(OUT, 'meta.csv'), index_label='i')
np.savez(os.path.join(OUT, 'emb_crops.npz'), cls=np.concatenate(CLS).astype(np.float16),
         mp=np.concatenate(MP).astype(np.float16))
print('saved', meta.shape, f'{time.time()-t0:.0f}s')
