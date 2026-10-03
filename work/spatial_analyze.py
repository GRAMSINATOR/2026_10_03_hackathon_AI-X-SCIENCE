import json

import numpy as np

D = json.load(open('work/spatial_raw.json'))
R, parent_of, chains = D['R'], D['parent_of'], D['chains']
ref = json.load(open('cache/reference.json'))
PX = 0.025
GATED = {'M2316'}  # additive not measurable
KP = ['additive_area_frac', 'additive_density', 'porosity']
out = {}
for k in KP:
    keys = [key for key in R if not (k.startswith('additive') and parent_of[key] in GATED)]
    rows = []
    for w in ['80', '160', '320', '640', '1280']:
        v = [np.var(R[key]['win'][k][w], ddof=1) for key in keys if w in R[key]['win'][k] and len(R[key]['win'][k][w]) > 2]
        rows.append(((int(w) * PX) ** 2, float(np.mean(v)), len(v)))
    A = np.array([r[0] for r in rows]); V = np.array([r[1] for r in rows])
    beta, logc = np.polyfit(np.log(A[1:]), np.log(V[1:]), 1)          # fit 4-32 um windows
    # tile scale: pooled variance between tiles of the same micrograph (all batches)
    groups = {}
    for key in keys:
        groups.setdefault(parent_of[key], []).append(R[key][k])
    ss = sum(((np.array(g) - np.mean(g)) ** 2).sum() for g in groups.values() if len(g) > 1)
    df = sum(len(g) - 1 for g in groups.values() if len(g) > 1)
    A_tile = float(np.mean([R[key]['H'] * R[key]['W'] for key in keys]) * PX ** 2)
    v_tile = ss / df
    v_pred_tile = float(np.exp(logc) * A_tile ** beta)
    v_pred_tile_iid = float(V[-1] * A[-1] / A_tile)                    # if beyond 32 um the field were uncorrelated (slope -1)
    # micrograph scale: variance of micrograph means among baseline micrographs (excl. gated)
    R_ = ref['kpi'][k]
    out[k] = dict(windows=rows, beta=float(beta), A_tile=A_tile, var_tile_obs=float(v_tile), df_tile=df,
                  var_tile_pred_powerlaw=v_pred_tile, var_tile_pred_iid=v_pred_tile_iid,
                  excess_tile=float(v_tile / v_pred_tile), sd_between_baseline=R_['sd_between'])
    # integral range (indicator fields): A_int = Var(A) * A / sigma2_point, using largest window
    if k != 'additive_density':
        p = np.mean([R[key][k] for key in keys])
        out[k]['A_int_um2_at32'] = float(V[-1] * A[-1] / (p * (1 - p)))
    print(f"\n{k}: slope beta = {beta:.2f} (−1 = short-range / iid beyond window)")
    for a, v, n in rows:
        print(f"   window {np.sqrt(a):5.1f} µm: var {v:.4g} (n tiles {n})")
    print(f"   tile scale ({A_tile:.0f} µm²): observed between-adjacent-tile var {v_tile:.4g} (df {df}); "
          f"power-law extrapolation {v_pred_tile:.4g}; iid-beyond-32µm {v_pred_tile_iid:.4g}; excess ×{v_tile / v_pred_tile:.1f}")
    print(f"   baseline between-micrograph SD (two-level model) {R_['sd_between']:.4g}; tile SD {R_['sd_within_tile']:.4g}")

# 1-D variograms along stitched cross-sections (25 um columns, full height)
print('\n--- transect variograms (25 µm columns) ---')
vg = {}
for k in KP:
    num, cnt = {}, {}
    totvar = []
    for pid, order in chains.items():
        if k.startswith('additive') and pid in GATED:
            continue
        runs, cur = [], []
        for key in order:
            if key is None:
                runs.append(cur); cur = []
            else:
                cur.append(key)
        runs.append(cur)
        for run in runs:
            # de-duplicate keys already seen in another batch? each key unique; chains mix batches (physically contiguous)
            z = np.concatenate([R[key]['cols'][k] for key in run if key in R]) if run else np.array([])
            if len(z) < 8:
                continue
            totvar.append(np.var(z))
            for h in range(1, min(len(z) - 1, 24)):
                d = z[h:] - z[:-h]
                num[h] = num.get(h, 0) + float((d ** 2).sum()); cnt[h] = cnt.get(h, 0) + len(d)
    hs = sorted(num)
    g = [0.5 * num[h] / cnt[h] for h in hs]
    vg[k] = dict(h_um=[h * 25 for h in hs], gamma=g, n_pairs=[cnt[h] for h in hs])
    print(k, ' '.join(f"{h * 25}µm:{gg:.3g}" for h, gg in zip(hs, g) if h in (1, 2, 3, 4, 6, 8, 12, 16, 20, 23)))
out['variogram'] = vg
json.dump(out, open('work/spatial.json', 'w'), indent=1)
