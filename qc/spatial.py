"""Marker-aware capture geometry and spatial support.

The production QC observables remain phase fractions, additive counts and particle-size summaries. This module adds
an uncertainty adapter layer around them:

* bounded phase fractions -> raw and p(1-p)-normalised local-volume-fraction heterogeneity;
* additive density -> equal-area number variance and Fano descriptors (counts, never normalised densities);
* spatial profiles -> support-matched 100-um means against a parent-cluster reference envelope;
* every scale -> window area, window count, field count and independent-parent count.

The original unweighted Var ~ Area^beta fit remains the operational spatial-class input. Support-weighted and
parent-bootstrap fits are sensitivity analyses; they do not change the QC verdict path.
"""
import hashlib

import numpy as np
from scipy import stats
from skimage import measure

SPATIAL_KPIS = ('additive_area_frac', 'additive_density', 'porosity')
WIN_UM = (2, 4, 8, 16, 32)
COL_UM = 25.0
PSD_BINS = [0.36, 0.5, 0.7, 1.0, 1.5, 2.5, 4.0, 12.0, 1e9]
BAND_COLS = 4   # 100-um window for the strip band
PHASE_EPS = 1e-6
BOOTSTRAP_REPLICATES = 2000

# Small registry, not a plugin framework. The same four fields are emitted on epistemic-field dimensions and may be
# attached provisionally to Marker Frontier candidates.
UNCERTAINTY_ADAPTERS = {
    'additive_area_frac': dict(observation_family='bounded_phase_fraction', support_model='equal_area_square_windows',
                               uncertainty_adapter='phase_fraction_heterogeneity', reference_protocol='parent_cluster_predictive'),
    'porosity': dict(observation_family='bounded_phase_fraction', support_model='equal_area_square_windows',
                     uncertainty_adapter='phase_fraction_heterogeneity', reference_protocol='parent_cluster_predictive'),
    'additive_density': dict(observation_family='spatial_count_process', support_model='equal_area_count_windows',
                             uncertainty_adapter='number_variance_fano', reference_protocol='parent_cluster_predictive'),
    'additive_psd': dict(observation_family='particle_size_distribution', support_model='particles_nested_in_parent_micrograph',
                         uncertainty_adapter='parent_cluster_distribution', reference_protocol='matched_resolution_parent_reference'),
    'additive_d50_um': dict(observation_family='particle_size_distribution', support_model='particles_nested_in_parent_micrograph',
                            uncertainty_adapter='parent_cluster_quantile', reference_protocol='two_level_parent_reference'),
    'additive_d90_um': dict(observation_family='particle_size_distribution', support_model='particles_nested_in_parent_micrograph',
                            uncertainty_adapter='parent_cluster_quantile', reference_protocol='two_level_parent_reference'),
    'additive_max_um': dict(observation_family='particle_size_distribution', support_model='particles_nested_in_parent_micrograph',
                            uncertainty_adapter='parent_cluster_extreme', reference_protocol='two_level_parent_reference'),
    'pore_size_um': dict(observation_family='particle_size_distribution', support_model='pores_nested_in_parent_micrograph',
                         uncertainty_adapter='parent_cluster_weighted_mean', reference_protocol='two_level_parent_reference'),
    'solid_chord_x_um': dict(observation_family='length_distribution', support_model='line_intercepts_nested_in_parent_micrograph',
                             uncertainty_adapter='parent_cluster_distribution', reference_protocol='two_level_parent_reference'),
}


def uncertainty_adapter(marker):
    """Renderer-independent uncertainty metadata for an operational marker."""
    return dict(UNCERTAINTY_ADAPTERS.get(marker, dict(
        observation_family='parent_level_scalar', support_model='fields_nested_in_parent_micrograph',
        uncertainty_adapter='two_level_random_effects', reference_protocol='simulation_calibrated_parent_reference')))


def field_maps(lab, px_nm):
    px_um = px_nm / 1000.0
    bri, pore = lab == 2, lab == 0
    rp = [p for p in measure.regionprops(measure.label(bri)) if p.area * px_um ** 2 >= 0.1]
    cnt = np.zeros(lab.shape, np.float32)
    if rp:
        c = np.array([p.centroid for p in rp]).astype(int)
        np.add.at(cnt, (c[:, 0], c[:, 1]), 1.0)
    ecd = np.array([2 * np.sqrt(p.area * px_um ** 2 / np.pi) for p in rp])
    maps = dict(additive_area_frac=bri.astype(np.float32), porosity=pore.astype(np.float32), additive_density=cnt)
    col = int(round(COL_UM / px_um))
    out = dict(col_um=COL_UM, width_um=lab.shape[1] * px_um, height_um=lab.shape[0] * px_um, win={}, cols={},
               psd=np.histogram(ecd, PSD_BINS)[0].tolist() if len(ecd) else [0] * (len(PSD_BINS) - 1),
               area_um2=float(lab.size * px_um ** 2))
    for k, mp in maps.items():
        out['win'][k] = {}
        for w_um in WIN_UM:
            w = int(round(w_um / px_um))
            H, W = (mp.shape[0] // w) * w, (mp.shape[1] // w) * w
            if H < w or W < w:
                continue
            blocks = mp[:H, :W].reshape(H // w, w, W // w, w)
            area = float((w * px_um) ** 2)
            if k == 'additive_density':
                counts = blocks.sum((1, 3)).ravel()
                values = counts / area * 1000.0
            else:
                counts = None
                values = blocks.mean((1, 3)).ravel()
            if values.size > 2:
                summary = dict(mean=float(values.mean()), variance=float(values.var(ddof=1)), n_windows=int(values.size),
                               window_um=float(w_um), window_area_um2=area, support='non_overlapping_square_windows')
                if k == 'additive_density':
                    mean_count, number_variance = float(counts.mean()), float(counts.var(ddof=1))
                    summary.update(mean_count=mean_count, number_variance=number_variance,
                                   fano=float(number_variance / mean_count) if mean_count > 0 else None)
                else:
                    p = float(values.mean())
                    summary['normalized_fluctuation'] = float(summary['variance'] / (p * (1 - p))) if PHASE_EPS < p < 1 - PHASE_EPS else None
                out['win'][k][str(w_um)] = summary
        nc = mp.shape[1] // col
        values = mp[:, :nc * col].reshape(mp.shape[0], nc, col).mean((0, 2))
        if k == 'additive_density':
            values = values * 1000.0 / px_um ** 2
        out['cols'][k] = values.tolist()
    return out


def _runs(order):
    runs, cur = [], []
    for k in order:
        if k is None:
            runs.append(cur)
            cur = []
        else:
            cur.append(k)
    runs.append(cur)
    return [r for r in runs if r]


def _seed(label):
    return int.from_bytes(hashlib.sha256(label.encode('utf-8')).digest()[:8], 'little')


def _window_summary(record, marker, w_um):
    """Read new rich summaries and migrate legacy [variance, n] cache entries without changing their variance."""
    raw = record['spatial']['win'].get(marker, {}).get(str(w_um))
    if raw is None:
        return None
    area = float(w_um ** 2)
    if isinstance(raw, dict):
        out = dict(raw)
        out.setdefault('window_area_um2', area)
        out.setdefault('n_windows', out.get('n', 0))
        return out
    variance, n = float(raw[0]), int(raw[1])
    mean = float(record['kpi'][marker])
    out = dict(mean=mean, variance=variance, n_windows=n, window_um=float(w_um), window_area_um2=area,
               support='non_overlapping_square_windows', migrated_from='legacy_variance_and_count')
    if marker == 'additive_density':
        mean_count = mean * area / 1000.0
        number_variance = variance * (area / 1000.0) ** 2
        out.update(mean_count=mean_count, number_variance=number_variance,
                   fano=number_variance / mean_count if mean_count > 0 else None)
    else:
        out['normalized_fluctuation'] = variance / (mean * (1 - mean)) if PHASE_EPS < mean < 1 - PHASE_EPS else None
    return out


def _variance_estimates(items, value='variance'):
    """Current equal-field, df-pooled and equal-parent estimates for a within-window variance."""
    rows = [x for x in items if x.get(value) is not None and np.isfinite(x[value]) and x['n_windows'] > 1]
    if not rows:
        return None
    current = float(np.mean([x[value] for x in rows]))
    df = sum(x['n_windows'] - 1 for x in rows)
    pooled = float(sum((x['n_windows'] - 1) * x[value] for x in rows) / df) if df else current
    parents = {}
    for x in rows:
        parents.setdefault(x['parent'], []).append(x)
    parent_values = {}
    for pid, rr in parents.items():
        pdf = sum(x['n_windows'] - 1 for x in rr)
        parent_values[pid] = float(sum((x['n_windows'] - 1) * x[value] for x in rr) / pdf) if pdf else float(np.mean([x[value] for x in rr]))
    return dict(current_equal_field=current, df_pooled=pooled, parent_equal=float(np.mean(list(parent_values.values()))),
                parent_values=parent_values, df=int(df))


def _weighted_mean(items, value):
    rows = [x for x in items if x.get(value) is not None and np.isfinite(x[value]) and x['n_windows'] > 0]
    if not rows:
        return None
    return float(sum(x['n_windows'] * x[value] for x in rows) / sum(x['n_windows'] for x in rows))


def _mean_estimates(items, value):
    """Mean under field-, window- and parent-balanced aggregation for the same equal-area observations."""
    rows = [x for x in items if x.get(value) is not None and np.isfinite(x[value]) and x['n_windows'] > 0]
    if not rows:
        return None
    parents = {}
    for x in rows:
        parents.setdefault(x['parent'], []).append(x)
    parent_values = {p: sum(x['n_windows'] * x[value] for x in rr) / sum(x['n_windows'] for x in rr)
                     for p, rr in parents.items()}
    return dict(current_equal_field=float(np.mean([x[value] for x in rows])),
                window_weighted=_weighted_mean(rows, value), parent_equal=float(np.mean(list(parent_values.values()))))


def _fit_beta(area, variance, weights=None):
    area, variance = np.asarray(area, float), np.asarray(variance, float)
    keep = np.isfinite(area) & np.isfinite(variance) & (area > 0) & (variance > 0)
    area, variance = area[keep], variance[keep]
    if weights is not None:
        weights = np.asarray(weights, float)[keep]
    if len(area) < 2:
        return float('nan'), float('nan')
    beta, logc = np.polyfit(np.log(area), np.log(variance), 1, w=None if weights is None else np.sqrt(weights))
    return float(beta), float(logc)


def _bootstrap_beta(scale_parent_values, scales, marker, n_boot=BOOTSTRAP_REPLICATES):
    parents = sorted({p for w in scales for p in scale_parent_values.get(w, {})})
    if len(parents) < 2:
        return dict(n_parents=len(parents), n_bootstrap=0, median=None, interval95=[None, None])
    rng, betas = np.random.default_rng(_seed('beta:' + marker)), []
    for _ in range(n_boot):
        sample = rng.choice(parents, size=len(parents), replace=True)
        area, var = [], []
        for w in scales[1:]:  # preserve the operational fit's exclusion of the 2-um scale
            vals = [scale_parent_values[w][p] for p in sample if p in scale_parent_values.get(w, {})]
            if vals and np.mean(vals) > 0:
                area.append(w ** 2)
                var.append(float(np.mean(vals)))
        beta, _ = _fit_beta(area, var)
        if np.isfinite(beta):
            betas.append(beta)
    if not betas:
        return dict(n_parents=len(parents), n_bootstrap=0, median=None, interval95=[None, None])
    return dict(n_parents=len(parents), n_bootstrap=len(betas), median=float(np.median(betas)),
                interval95=[float(np.quantile(betas, .025)), float(np.quantile(betas, .975))])


def model(records, parent_of, chains, excluded_additive=()):
    """Reference-level support model. New descriptors are non-decision-driving; beta/class stay operational."""
    by_key = {r['key']: r for r in records if 'spatial' in r}
    out = {}
    for k in SPATIAL_KPIS:
        ok = [r for r in by_key.values() if not (k.startswith('additive') and parent_of[r['key']] in excluded_additive)]
        A, V, pooled_v, parent_v, support, scale_parent_values, heterogeneity = [], [], [], [], [], {}, []
        for w_um in WIN_UM:
            items = []
            for r in ok:
                x = _window_summary(r, k, w_um)
                if x:
                    items.append(dict(x, parent=parent_of[r['key']], field=r['key']))
            estimates = _variance_estimates(items)
            if not estimates:
                continue
            n_windows = sum(x['n_windows'] for x in items)
            A.append(w_um ** 2)
            V.append(estimates['current_equal_field'])                 # retained operational estimate
            pooled_v.append(estimates['df_pooled'])
            parent_v.append(estimates['parent_equal'])
            support.append(n_windows)
            scale_parent_values[w_um] = estimates['parent_values']
            row = dict(window_um=float(w_um), window_area_um2=float(w_um ** 2), n_windows=int(n_windows),
                       n_fields=len(items), n_parents=len({x['parent'] for x in items}),
                       min_windows_per_field=min(x['n_windows'] for x in items), max_windows_per_field=max(x['n_windows'] for x in items),
                       raw_variance=dict(current_equal_field=estimates['current_equal_field'], df_pooled=estimates['df_pooled'],
                                         parent_equal=estimates['parent_equal']))
            if k == 'additive_density':
                nv = _variance_estimates(items, 'number_variance')
                mean_count = _mean_estimates(items, 'mean_count')
                row.update(mean_count=None if mean_count is None else mean_count['window_weighted'],
                           mean_count_estimates=mean_count,
                           number_variance=None if nv is None else dict(current_equal_field=nv['current_equal_field'],
                                                                       df_pooled=nv['df_pooled'], parent_equal=nv['parent_equal']),
                           fano=None if nv is None or mean_count is None or not mean_count['parent_equal'] else
                                nv['parent_equal'] / mean_count['parent_equal'],
                           interpretation='descriptor only: relative to an equal-area Poisson count null; not a physical diagnosis')
            else:
                norm = _variance_estimates(items, 'normalized_fluctuation')
                row.update(normalized_fluctuation=None if norm is None else dict(current_equal_field=norm['current_equal_field'],
                                                                                 df_pooled=norm['df_pooled'], parent_equal=norm['parent_equal']),
                           interpretation='normalised by p(1-p) to reduce trivial dependence on global phase fraction; geometry remains')
            heterogeneity.append(row)
        A, V = np.array(A, float), np.array(V, float)
        pooled_v, parent_v, support = np.array(pooled_v, float), np.array(parent_v, float), np.array(support, float)
        beta, logc = _fit_beta(A[1:], V[1:])
        beta_weighted, _ = _fit_beta(A[1:], pooled_v[1:], support[1:])
        beta_parent, _ = _fit_beta(A[1:], parent_v[1:])
        boot = _bootstrap_beta(scale_parent_values, [int(np.sqrt(a)) for a in A], k)
        groups = {}
        for r in ok:
            groups.setdefault(parent_of[r['key']], []).append(r['kpi'][k])
        ss = sum(float(((np.array(g) - np.mean(g)) ** 2).sum()) for g in groups.values() if len(g) > 1)
        df = sum(len(g) - 1 for g in groups.values() if len(g) > 1)
        A_tile = float(np.mean([r['spatial']['area_um2'] for r in ok]))
        pred = float(np.exp(logc) * A_tile ** beta)
        v_tile = ss / df if df else float('nan')
        E = v_tile / pred if df else float('nan')
        ci = [v_tile * df / stats.chi2.ppf(0.975, df) / pred, v_tile * df / stats.chi2.ppf(0.025, df) / pred] if df else [np.nan, np.nan]
        # transect variogram along stitched sections (contiguous runs only)
        num, cnt = {}, {}
        for pid, order in chains.items():
            if k.startswith('additive') and pid in excluded_additive:
                continue
            for run in _runs(order):
                values = [by_key[x]['spatial']['cols'][k] for x in run if x in by_key]
                z = np.concatenate(values) if values else np.array([])
                for h in range(1, len(z)):
                    d = z[h:] - z[:-h]
                    num[h] = num.get(h, 0.0) + float((d ** 2).sum())
                    cnt[h] = cnt.get(h, 0) + len(d)
        hs = [h for h in sorted(num) if cnt[h] >= 20]
        gam = [0.5 * num[h] / cnt[h] for h in hs]
        lag_um = [h * COL_UM for h in hs]
        cls, rng = 'short-range', None
        if np.isfinite(ci[0]) and ci[0] > 1 and gam:
            g = np.array(gam)
            early = g[np.array(lag_um) <= 250].max()
            if g[-1] > 1.2 * early:
                cls, rng = 'long-range', float(lag_um[-1])
            else:
                cls, rng = 'fov-scale', float(lag_um[int(np.argmax(g >= 0.9 * g.max()))])
        model_sensitivity = dict(operational_unweighted_beta=float(beta), support_weighted_beta=beta_weighted,
                                 parent_equal_beta=beta_parent, parent_bootstrap=boot,
                                 material_difference=bool(np.isfinite(beta_weighted) and abs(beta_weighted - beta) >= 0.1),
                                 note='beta describes scale-dependent heterogeneity over the observed support; it is not a universal physical constant')
        out[k] = dict(beta=float(beta), windows_um=[float(np.sqrt(a)) for a in A], window_var=V.tolist(),
                      window_var_df_pooled=pooled_v.tolist(), window_var_parent_equal=parent_v.tolist(),
                      scale_dependent_heterogeneity=heterogeneity, scale_model_sensitivity=model_sensitivity,
                      observation_model=uncertainty_adapter(k), A_tile_um2=A_tile,
                      var_tile_obs=float(v_tile), var_tile_pred=pred, excess=float(E), excess_ci=[float(c) for c in ci], df=df,
                      variogram=dict(lag_um=lag_um, gamma=gam, n_pairs=[cnt[h] for h in hs]), cls=cls, range_um=rng,
                      max_coherent_um=float(max(sum(by_key[x]['spatial']['width_um'] for x in run if x in by_key)
                                                for o in chains.values() for run in _runs(o))))
    return out


def psd_density(records):
    """Additive count per size bin per 1000 um^2, pooled over records."""
    c = np.zeros(len(PSD_BINS) - 1)
    a = 0.0
    for r in records:
        c += np.array(r['spatial']['psd'], float)
        a += r['spatial']['area_um2']
    return (c / max(a, 1e-9) * 1000).tolist()


def _profile_windows(records, k, chains=None):
    """Return complete 100-um windows by parent without bridging an unknown section gap."""
    by_key = {r['key']: r for r in records}
    by_parent, used = {}, set()
    if chains:
        for pid, order in chains.items():
            parent_runs = []
            for run in _runs(order):
                current = []
                for key in run:
                    r = by_key.get(key)
                    if r is None or r.get('parent') != pid:
                        if current:
                            parent_runs.append(current)
                            current = []
                        continue
                    current.append(r)
                    used.add(key)
                if current:
                    parent_runs.append(current)
            for run in parent_runs:
                z = np.concatenate([np.asarray(r['spatial']['cols'][k], float) for r in run])
                if len(z) >= BAND_COLS:
                    by_parent.setdefault(pid, []).extend(np.convolve(z, np.ones(BAND_COLS) / BAND_COLS, mode='valid').tolist())
    # Retain records not represented in provenance chains, but never infer adjacency for them.
    for r in records:
        if r['key'] in used:
            continue
        z = np.asarray(r['spatial']['cols'][k], float)
        if len(z) >= BAND_COLS:
            by_parent.setdefault(r['parent'], []).extend(np.convolve(z, np.ones(BAND_COLS) / BAND_COLS, mode='valid').tolist())
    return {p: np.asarray(v, float) for p, v in by_parent.items() if len(v)}


def _weighted_quantile(values, weights, quantiles):
    order = np.argsort(values)
    values, weights = np.asarray(values)[order], np.asarray(weights, float)[order]
    cdf = (np.cumsum(weights) - .5 * weights) / weights.sum()
    return np.interp(quantiles, cdf, values, left=values[0], right=values[-1])


def band(records, k, excluded=(), chains=None, n_boot=BOOTSTRAP_REPLICATES):
    """Parent-cluster predictive envelope for support-matched 100-um local-window means.

    Bootstrap endpoints describe their sampling sensitivity with the available independent parents. They are not
    labelled as a calibrated confidence or prediction interval: the approved reference currently has few parents.
    The former flattened mean +/- 1.96 window SD is retained explicitly as an audit comparator.
    """
    eligible = [r for r in records if r.get('parent') not in excluded]
    parent_windows = _profile_windows(eligible, k, chains)
    if not parent_windows:
        return dict(mean=None, lo=None, hi=None, n=0, n_windows=0, n_fields=0, n_parents=0,
                    kind='parent_cluster_predictive_envelope', statistic='local_window_mean', column_um=COL_UM,
                    window_um=COL_UM * BAND_COLS, calibrated=False, bootstrap_replicates=0,
                    label='REFERENCE PARENT-BOOTSTRAP ENVELOPE', note='no eligible complete local windows')
    parents = sorted(parent_windows)
    flat = np.concatenate([parent_windows[p] for p in parents])
    parent_means = np.asarray([parent_windows[p].mean() for p in parents])
    center = float(parent_means.mean())
    # Equal parent weight for the centre; parent and within-parent dispersion remain visible in the predictive scale.
    predictive_var = float(np.mean([np.mean((parent_windows[p] - center) ** 2) for p in parents]))
    predictive_sd = float(np.sqrt(max(predictive_var, 0.0)))
    legacy_sd = float(flat.std(ddof=1)) if len(flat) > 1 else 0.0

    rng, endpoints, centres = np.random.default_rng(_seed('band:' + k)), [], []
    for _ in range(n_boot if len(parents) > 1 else 0):
        sample = rng.choice(parents, size=len(parents), replace=True)
        values = np.concatenate([parent_windows[p] for p in sample])
        weights = np.concatenate([np.full(len(parent_windows[p]), 1 / len(parent_windows[p])) for p in sample])
        endpoints.append(_weighted_quantile(values, weights, [.025, .975]))
        centres.append(float(np.mean([parent_windows[p].mean() for p in sample])))
    if endpoints:
        endpoints = np.asarray(endpoints)
        lo, hi = np.median(endpoints, axis=0)
        endpoint_sensitivity = dict(
            lower_80=[float(x) for x in np.quantile(endpoints[:, 0], [.1, .9])],
            upper_80=[float(x) for x in np.quantile(endpoints[:, 1], [.1, .9])],
            centre_80=[float(x) for x in np.quantile(centres, [.1, .9])],
        )
    else:
        weights = np.concatenate([np.full(len(parent_windows[p]), 1 / len(parent_windows[p])) for p in parents])
        lo, hi = _weighted_quantile(flat, weights, [.025, .975])
        endpoint_sensitivity = dict(lower_80=[float(lo), float(lo)], upper_80=[float(hi), float(hi)],
                                    centre_80=[center, center])
    standardized = {p: float(np.max(np.abs(parent_windows[p] - center)) / max(predictive_sd, 1e-12)) for p in parents}
    # Length-matched maximum screens. Whole parents are the resampling blocks; no overlapping window is treated as an
    # independent bootstrap unit. With few parents these thresholds cannot exceed observed parent behaviour, hence the
    # explicit uncalibrated/small-support labels.
    max_windows = 64
    max_rng = np.random.default_rng(_seed('profile-max:' + k))
    threshold_by_n = {}
    for target_n in range(1, max_windows + 1):
        maxima = []
        for _ in range(n_boot if len(parents) > 1 else 1):
            values = []
            while len(values) < target_n:
                p = max_rng.choice(parents)
                values.extend(parent_windows[p].tolist())
            z = np.abs(np.asarray(values[:target_n]) - center) / max(predictive_sd, 1e-12)
            maxima.append(float(np.max(z)))
        threshold_by_n[str(target_n)] = float(np.quantile(maxima, .95))
    native_n = max(len(parent_windows[p]) for p in parents)
    return dict(
        mean=center, lo=float(lo), hi=float(hi), scale=predictive_sd, n=int(len(flat)), n_windows=int(len(flat)),
        n_fields=len({r['key'] for r in eligible}), n_parents=len(parents), bootstrap_replicates=len(endpoints),
        kind='parent_cluster_predictive_envelope', statistic='local_window_mean', column_um=COL_UM,
        window_um=COL_UM * BAND_COLS, target_quantiles=[.025, .975], calibrated=False,
        small_parent_support=bool(len(parents) < 10), label='REFERENCE PARENT-BOOTSTRAP ENVELOPE',
        endpoint_sensitivity_80=endpoint_sensitivity,
        audit_population_spread=dict(mean=float(flat.mean()), sd=legacy_sd,
                                     lo=float(flat.mean() - 1.96 * legacy_sd), hi=float(flat.mean() + 1.96 * legacy_sd),
                                     kind='mean_plus_minus_1_96_window_sd', semantics='population_spread_audit'),
        simultaneous=dict(kind='parent_cluster_bootstrap_maximum_standardized_excursion',
                          threshold=threshold_by_n[str(native_n)], threshold_by_n_windows=threshold_by_n,
                          target_quantile=.95, maximum_supported_windows=max_windows, parent_maxima=standardized,
                          n_parents=len(parents), bootstrap_replicates=n_boot if len(parents) > 1 else 1,
                          calibrated=False,
                          note='descriptive whole-profile screen; parent clusters are resampled to the observed window count'),
        note=('parent-balanced 2.5th and 97.5th percentiles of support-matched 100-um reference windows with '
              'parent-cluster bootstrap sensitivity; descriptive and not coverage-calibrated'))
