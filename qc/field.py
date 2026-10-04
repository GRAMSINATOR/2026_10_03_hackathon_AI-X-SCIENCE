"""The uncertainty field: the single renderer-independent epistemic object (contract `epistemic-field/1`).

Scientific reality / model (qc.stats, qc.spatial, qc.robustness)  ->  this contract  ->  any renderer.

The field states what was measured, how it relates to the approved population, what bounds each envelope, which
evidence survives scrutiny, where support fades (rims) and which acquisition actions follow, each action pointing
back to the rims / observations that triggered it. It contains no visual instructions: no colours, sizes, orderings
with meaning, animation states or invented coordinates. Prose fields (`statement`, `title`, `evidence`, `rationale`,
`reasons`) are human-readable annotations of structured fields that sit beside them.

Model: frequentist two-level random-effects model per KPI
    x_jk = mu_k + b_j + e_j / sqrt(m_j),   b ~ N(0, sd_between^2),  e ~ N(0, sd_tile^2)
    V_jk = sd_between^2 + sd_tile^2 / m_j + s_k^2 / n_k     (approved material | spatial sampling | baseline support)
with simulation-calibrated thresholds (qc.stats). Not Bayesian. See docs/REPRESENTATION_CONTRACT.md.
"""
import numpy as np
from scipy import stats as sps

from .explain import acquisition_deviations
from .spatial import BAND_COLS, COL_UM, PSD_BINS, SPATIAL_KPIS, psd_density
from .stats import ALPHA_INVESTIGATE, ALPHA_REJECT, CNR_MIN, KPIS, _calibrate

SCHEMA_VERSION = 'epistemic-field/1'
ACQ_SHARE_MAX = 0.5      # a deviation survives if the worst tested acquisition change explains < 50% of it
VERB_ORDER = ['REPEAT', 'ZOOM', 'EDS', 'EXTEND', 'SECTIONS', 'SPACE', 'REIMAGE', 'BASELINE']
REF_VERB_ORDER = ['REIMAGE', 'ZOOM', 'SPACE', 'EXTEND', 'EDS', 'BASELINE']
CANON_UNIT = {'%': 'fraction'}   # KPI values are stored in canonical units; display factor converts
# reference self-audit (role REFERENCE): when estimating the baseline contributes at least this share of a 3-field
# envelope's variance on a robust KPI, the size of the reference itself limits every comparison made against it
REF_SUPPORT_SHARE = 1 / 3


def _oid(entity, dim):
    return f'{entity}:{dim}'


def _size_distribution(recs, ref):
    c = np.zeros(len(PSD_BINS) - 1)
    a = 0.0
    for r in recs:
        c += np.array(r['spatial']['psd'], float)
        a += r['spatial']['area_um2']
    pm = c / max(a, 1e-9) * 1000
    pr = np.array(ref['psd_ref'], float)
    ratio = pm / np.maximum(pr, 1e-9)
    exc = np.clip(pm - pr, 0, None)
    share = float(exc[:2].sum() / exc.sum()) if exc.sum() > 0 else 0.0
    peak = float(max(ratio[0], ratio[1]))
    piled = bool(share >= 0.5 and peak >= 1.5 and peak >= ratio[2:].max())
    return dict(bin_edges_um=PSD_BINS[:-1], density_per_1000um2=pm.tolist(), reference_density_per_1000um2=pr.tolist(),
                ratio_to_reference=ratio.tolist(), excess_share_below_0_7um=share, peak_ratio_at_floor=peak,
                detection_floor_um=PSD_BINS[0], excess_piled_at_floor=piled)


def _profile(entity, order, by_key, k, band, direction):
    """Column profile along the known section. Each contiguous run has its own frame starting at 0 µm;
    the separation between runs is unknown and is not encoded."""
    runs, cur = [], []
    for key in order:
        if key is None:
            runs.append(cur)
            cur = []
        else:
            cur.append(key)
    runs.append(cur)
    out_runs = []
    for run in [r for r in runs if r]:
        x0, cx, cv, fields = 0.0, [], [], []
        for key in run:
            r = by_key.get(key)
            if r is None:
                continue
            for i, v in enumerate(r['spatial']['cols'][k]):
                cx.append(x0 + (i + 0.5) * r['spatial']['col_um'])
                cv.append(v)
            fields.append(dict(field=key, batch=r['batch'], x0_um=x0, width_um=r['spatial']['width_um']))
            x0 += r['spatial']['width_um']
        cv, cx = np.array(cv), np.array(cx)
        if len(cv) >= BAND_COLS:   # windows fully inside the captured run (no edge padding)
            wm = np.convolve(cv, np.ones(BAND_COLS) / BAND_COLS, mode='valid')
            wx = np.convolve(cx, np.ones(BAND_COLS) / BAND_COLS, mode='valid')
        else:
            wm, wx = cv, cx
        outside = (wm > band['hi']) if direction > 0 else (wm < band['lo'])
        out_runs.append(dict(fields=fields, length_um=float(x0), column_centres_um=cx.tolist(), column_values=cv.tolist(),
                             window_centres_um=wx.tolist(), window_means=wm.tolist(),
                             open_at_start=bool(len(wm) and outside[0]), open_at_end=bool(len(wm) and outside[-1]),
                             fraction_outside_band=float(outside.mean()) if len(wm) else 0.0))
    return dict(id=_oid(entity, k), entity=entity, dimension=k, column_um=COL_UM, window_um=COL_UM * BAND_COLS, deviation_direction=int(direction),
                reference_band=dict(band, window_um=COL_UM * BAND_COLS, approximate=True,
                                    note='approved local-window range; basis of open-edge tests, not a decision statistic'),
                run_separation='unknown', runs=out_runs, captured_length_um=float(sum(r['length_um'] for r in out_runs)))


def _prevalence(k, n):
    lo = sps.beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
    hi = sps.beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return float(lo), float(hi)


def _mdc_at(R, n_new):
    """MDC (95%, 3-tile micrograph) if the approved reference had n_new single-tile micrographs (same variance model)."""
    q = _calibrate(R['sd'] ** 2, R['sd_within_tile'], [1] * n_new, R=20_000)
    return float(q['3'][0] * np.sqrt(R['sd_between'] ** 2 + R['sd_within_tile'] ** 2 / 3 + R['sd'] ** 2 / n_new))


def _dimensions(ref):
    sp, rob = ref.get('spatial', {}), ref.get('robustness', {})
    dims = []
    for k, meta in KPIS.items():
        R = ref['kpi'][k]
        s = sp.get(k)
        rb = rob.get(k, {})
        dims.append(dict(
            id=k, kind='kpi', acquired=True, label=meta['label'], short_label=meta['short'], family=meta['family'],
            unit=CANON_UNIT.get(meta['unit'], meta['unit']), display=dict(unit=meta['unit'], factor=meta['scale']),
            modalities=['BSE'], cross_checks=['SE'] if k == 'porosity' else [],
            robustness=dict(cls=meta['cls'], worst_perturbation=rb.get('worst'), worst_shift=rb.get('max_abs'),
                            worst_shift_over_tile_sd=(rb['max_abs'] / R['sd_within_tile']) if rb and R['sd_within_tile'] else None),
            reference=dict(mean=R['mean'], sd=R['sd'], sd_between=R['sd_between'], sd_tile=R['sd_within_tile'], var_mean=R['var_mu'],
                           n_micrographs=R['n'], excluded=R.get('excluded', []), mdc95_3tiles=R['mdc95'],
                           tile_range=ref.get('tile_range', {}).get(k)),
            spatial_support=None if s is None else dict(cls=s['cls'], window_variance_slope=s['beta'], tile_excess=s['excess'],
                                                        tile_excess_ci95=s['excess_ci'], df=s['df'], range_um=s['range_um'],
                                                        variogram=s['variogram'])))
    dims.append(dict(id='composition', kind='missing', acquired=False, label='Composition of the high-Z phase', short_label='Composition',
                     family='composition', would_require=['EDS', 'spectroscopy'],
                     note='not acquired in this dataset; relevance per entity in missing_dimensions'))
    return dims


def build(res, ref, recs, chains, all_records, frames=None):
    """frames: leave-one-parent-out reference frames (qc.stats.loo_frames). Given, the field is the reference's
    self-audit (role REFERENCE): each reference micrograph is related to its own frame, never to a model containing it,
    and rims are consequential when they weaken the reference as a comparison anchor. Absent, an incoming batch."""
    by_key = {r['key']: r for r in all_records}
    d = res['decision']
    is_ref = frames is not None
    batch = res['batch']
    sp, rob = ref.get('spatial', {}), ref.get('robustness', {})
    dims = _dimensions(ref)
    entities, observations, profiles, missing, rims = [], [], [], [], []
    rec_by = {m['parent']: [by_key[k] for k in m['keys'] if k in by_key] for m in res['micrographs']}
    links_by = {}
    for l in res.get('links', []):
        links_by.setdefault(l['parent'], []).append(l)
    batch_links = {}
    for r in all_records:
        if r['batch'] != batch:
            batch_links.setdefault(r['key'], r['batch'])

    for m in sorted(res['micrographs'], key=lambda x: x['parent']):
        pid = m['parent']
        lev = m.get('leverage')
        order = chains.get(pid, m['keys'])
        differs = acquisition_deviations(m, ref, 'acq_envelope')
        untested = acquisition_deviations(m, ref, 'acq_tested') if 'acq_tested' in ref else differs
        others = sorted({by_key[k]['batch'] for k in order if k and k in by_key and by_key[k]['batch'] != batch})
        ent = dict(
            id=pid, kind='parent_micrograph', fields=[f'{batch}__{f}' for f in m['fids']], n_fields=m['n_tiles'],
            independence=dict(reference_linked=bool(m.get('ref_linked')), also_in_batches=others),
            geometry=dict(known_section_um=float(sum(by_key[k]['spatial']['width_um'] for k in order if k and k in by_key)),
                          batch_coverage_um=float(sum(r['spatial']['width_um'] for r in rec_by[pid])),
                          field_height_um=float(np.mean([r['spatial']['height_um'] for r in rec_by[pid]]))),
            validity=dict(measurable=m['gate'], reasons=m['gate_reasons'], cnr_min=CNR_MIN),
            acquisition=dict(metrics={a: v for a, v in m['acq'].items()}, differs_from_approved=differs, outside_tested_range=untested),
            leverage=None if lev is None else dict(verdict_without=lev['verdict_without'], p_without=lev['p_without'], flips=lev['flips'],
                                                   cause='min_independent_count' if 'below 3' in lev['why'] else 'carries_decisive_evidence'),
            status=m['status'], size_distribution=_size_distribution(rec_by[pid], ref) if 'psd_ref' in ref else None)
        if is_ref:   # this parent against the others only: size distribution, tile support range, influence on the reference
            others = [x for x in res['micrographs'] if x['parent'] != pid]
            ok = [by_key[k] for x in others if x['gate']['additive'] for k in x['keys'] if k in by_key]
            ent['size_distribution'] = _size_distribution(rec_by[pid], dict(ref, psd_ref=psd_density(ok))) if ok else None
            ent['reference_influence'] = m.get('reference_influence', {})
        entities.append(ent)
        surviving_additive = []
        for k, meta in KPIS.items():
            R, sc = (frames[pid]['kpi'].get(k) if is_ref else ref['kpi'][k]), m['score'][k]
            o = dict(id=_oid(pid, k), entity=pid, dimension=k, value=sc.get('value'),
                     per_field={f'{batch}__{f}': v.get(k) for f, v in m['tile_kpi'].items()}, rims=[])
            if sc['status'] == 'not measurable':
                o.update(reference_relation=dict(status='not_measurable'), variance_shares=None,
                         scrutiny=dict(outcome='not_applicable'), acquisition_explains_deviation=False)
                observations.append(o)
                continue
            x, mu = sc['value'], R['mean']
            comp = dict(approved_material=R['sd_between'] ** 2, spatial_sampling=R['sd_within_tile'] ** 2 / m['n_tiles'], baseline_support=R['var_mu'])
            tot = sum(comp.values()) or 1e-30
            delta = abs(x - mu)
            shift = rob.get(k, {}).get('max_abs', 0.0)
            acq_share = shift / delta if delta > 0 else None
            deviating = sc['status'] in ('deviant', 'out')
            lo_s, hi_s = ref.get('tile_range', {}).get(k, [None, None])
            if is_ref:   # support range of the OTHER reference micrographs' fields
                tv = [t[k] for x in res['micrographs'] if x['parent'] != pid and x['gate'][meta['family']]
                      for t in x['tile_kpi'].values() if t.get(k) is not None and np.isfinite(t[k])]
                lo_s, hi_s = (min(tv), max(tv)) if tv else (None, None)
            o['reference_relation'] = dict(status=sc['status'], z=sc['t'], q95=sc['q95'], q99=sc['q99'], envelope95=sc.get('pi95'),
                                           approved_mean=mu, exceedance_ratio=abs(sc['t']) / sc['q95'], direction=int(np.sign(x - mu)),
                                           beyond_reference_support=bool(lo_s is not None and (x < lo_s or x > hi_s)))
            if is_ref:
                o['reference_relation'].update(frame='leave_one_out', frame_n=R['n'])
            o['variance_shares'] = {kk: v / tot for kk, v in comp.items()}
            scr = dict(outcome='not_applicable', robust_dimension=meta['cls'] == 'robust', tile_consistent=bool(sc.get('consistent')),
                       fields_beyond_95=sc.get('tiles_beyond95'), n_fields=sc.get('n_tiles'), acquisition_share=acq_share,
                       acquisition_share_max=ACQ_SHARE_MAX, failed=[], conditional_on_untested_acquisition=False)
            if deviating:
                if meta['cls'] != 'robust':
                    scr['failed'].append('moderate_robustness_dimension')
                if not sc.get('consistent'):
                    scr['failed'].append('spatially_inconsistent')
                if acq_share is not None and acq_share >= ACQ_SHARE_MAX:
                    scr['failed'].append('acquisition_could_explain')
                scr['outcome'] = 'fails' if scr['failed'] else 'survives'
                scr['conditional_on_untested_acquisition'] = bool(not scr['failed'] and untested)
                if meta['family'] == 'additive' and not scr['failed']:
                    surviving_additive.append(o['id'])
            o['scrutiny'] = scr
            o['acquisition_explains_deviation'] = bool(deviating and acq_share is not None and acq_share >= ACQ_SHARE_MAX)
            observations.append(o)
        obs = {o['dimension']: o for o in observations if o['entity'] == pid}
        dev = lambda k: obs[k]['reference_relation'].get('status') in ('deviant', 'out')
        # scale rim: deviation in the additive family, excess piled at the detection floor
        sd = ent['size_distribution']
        add_dev = [k for k in KPIS if KPIS[k]['family'] == 'additive' and dev(k)]
        if sd and add_dev and sd['excess_piled_at_floor']:
            rid = f'scale:{pid}'
            for k in add_dev:
                obs[k]['rims'].append(rid)
            rims.append(dict(id=rid, type='scale', scope='entity', target=pid, consequential=bool(surviving_additive) if is_ref else bool(lev and lev['flips']),
                             basis=dict(excess_share_below_0_7um=sd['excess_share_below_0_7um'], peak_ratio_at_floor=sd['peak_ratio_at_floor'],
                                        detection_floor_um=sd['detection_floor_um'], pixel_nm=float(m['acq']['px_nm']), observations=[_oid(pid, k) for k in add_dev]),
                             statement=f"{100 * sd['excess_share_below_0_7um']:.0f}% of the excess high-Z objects are < 0.7 µm and the excess ratio peaks "
                                       f"at the {sd['detection_floor_um']} µm detection floor ({sd['peak_ratio_at_floor']:.1f}×): the anomalous population "
                                       "is truncated by the pixel size."))
        # spatial profiles and observation-level spatial rims
        for k in SPATIAL_KPIS:
            direction = obs[k]['reference_relation'].get('direction', 1) or 1
            prof = _profile(pid, order, by_key, k, ref['band'][k], direction)
            profiles.append(prof)
            s = sp.get(k)
            if dev(k) and s and s['cls'] in ('fov-scale', 'long-range'):
                edges = sorted({e for run in prof['runs'] for e, f in (('start', run['open_at_start']), ('end', run['open_at_end'])) if f})
                if edges or not obs[k]['scrutiny']['tile_consistent']:
                    rid = f'spatial:{pid}:{k}'
                    obs[k]['rims'].append(rid)
                    rims.append(dict(id=rid, type='spatial', scope='observation', target=_oid(pid, k),
                                     consequential=(obs[k]['scrutiny'].get('outcome') == 'survives') if is_ref else bool(lev and lev['flips']),
                                     basis=dict(open_edges=edges, captured_length_um=prof['captured_length_um'],
                                                fraction_outside_band=max(r['fraction_outside_band'] for r in prof['runs']),
                                                tile_consistent=obs[k]['scrutiny']['tile_consistent'], dimension_spatial_class=s['cls'],
                                                dimension_range_um=s['range_um']),
                                     statement=(f"deviation still outside the approved local band at the {' and '.join(edges)} of the "
                                                f"{prof['captured_length_um']:.0f} µm captured section") if edges else
                                               (f"deviation present in {obs[k]['scrutiny']['fields_beyond_95']}/{obs[k]['scrutiny']['n_fields']} fields while this "
                                                f"KPI varies on {s['cls']} scales")))
        # missing dimension relevance (composition)
        fu = m['kpi'].get('additive_fines_u')
        rf = ref['secondary'].get('additive_fines_u')
        missing.append(dict(id=_oid(pid, 'composition'), entity=pid, dimension='composition', consequential=bool(surviving_additive),
                            basis=dict(dependent_observations=surviving_additive, fines_bse_intensity_u=fu,
                                       approved_fines_bse_intensity_range=[rf['min'], rf['max']] if rf else None)))
        if surviving_additive:
            rims.append(dict(id=f'composition:{pid}', type='composition', scope='entity', target=pid, consequential=True if is_ref else bool(lev and lev['flips']),
                             basis=dict(missing_dimension='composition', dependent_observations=surviving_additive, fines_bse_intensity_u=fu,
                                        approved_fines_bse_intensity_range=[rf['min'], rf['max']] if rf else None),
                             statement='the surviving deviation is in the high-Z phase, whose chemistry is not measured: BSE alone cannot '
                                       'separate a finer additive from a different lower-Z phase.'))
        if untested:
            # reference: outside the tested range only matters on its own when the measurements are otherwise valid; with a
            # validity failure, the validity rim carries the consequence (the acquisition difference is its likely cause)
            rims.append(dict(id=f'acquisition:{pid}', type='acquisition', scope='entity', target=pid,
                             consequential=(not m['gate_reasons']) if is_ref else bool(lev and lev['flips']),
                             basis=dict(outside_tested_range=untested),
                             statement='acquired outside the tested acquisition range; sensitivity bounds do not apply.'))
        if m['gate_reasons']:
            rims.append(dict(id=f'validity:{pid}', type='validity', scope='entity', target=pid, consequential=is_ref,
                             basis=dict(measurable=m['gate'], reasons=m['gate_reasons']), statement='; '.join(m['gate_reasons'])))

    # batch-level population support
    indep = [e for e in entities if not e['independence']['reference_linked']]
    n_out = len([e for e in indep if e['status'] == 'out'])
    prev = _prevalence(n_out, len(indep)) if indep else (0.0, 1.0)
    pivotal = [e['id'] for e in entities if e['leverage'] and e['leverage']['flips']]
    n_ref = [dm['reference']['n_micrographs'] for dm in dims if dm['acquired']]
    if is_ref:   # reference support: how much of a 3-field envelope is the uncertainty of estimating the reference itself
        share = {}
        for k, meta in KPIS.items():
            R = ref['kpi'][k]
            tot = R['sd_between'] ** 2 + R['sd_within_tile'] ** 2 / 3 + R['var_mu']
            share[k] = float(R['var_mu'] / tot) if tot > 0 else 0.0
        robust = [k for k in KPIS if KPIS[k]['cls'] == 'robust']
        kmax = max(robust, key=lambda k: share[k])
        n_out = len([e for e in entities if e['status'] == 'out'])
        prev = _prevalence(n_out, len(entities))
        excl = sorted({p for k in KPIS for p in ref['kpi'][k].get('excluded', [])})
        rims.insert(0, dict(id=f'population:{batch}', type='population', scope='batch', target=batch,
                            consequential=bool(share[kmax] >= REF_SUPPORT_SHARE),
                            basis=dict(n_reference_min=min(n_ref), n_reference_max=max(n_ref), n_independent=len(entities), n_reference_linked=0,
                                       pivotal=[], pivotal_cause=[], prevalence=dict(out_of_family=n_out, n=len(entities), ci95=prev),
                                       baseline_share_3_fields=share, max_baseline_share=share[kmax], max_baseline_share_dimension=kmax,
                                       support_share_threshold=REF_SUPPORT_SHARE, excluded_by_validity=excl),
                            statement=f"reference = {min(n_ref)}-{max(n_ref)} micrographs per KPI"
                                      + (f" ({', '.join(excl)} excluded by the validity gate for some KPIs)" if excl else '')
                                      + f"; estimating the reference is {100 * share[kmax]:.0f}% of a 3-field envelope's variance for "
                                      f"{KPIS[kmax]['label'].lower()}"))
        pr = np.array(ref.get('psd_ref') or [], float)
        if pr.size >= 2:   # does the reference's own size distribution turn over before the detection floor?
            truncated = bool(pr[0] >= pr[1:].max())
            rims.append(dict(id=f'scale:{batch}', type='scale', scope='batch', target=batch, consequential=truncated,
                             basis=dict(bin_edges_um=PSD_BINS[:-1], reference_density_per_1000um2=pr.tolist(), detection_floor_um=PSD_BINS[0],
                                        floor_bin_density=float(pr[0]), max_density_above_floor=float(pr[1:].max()),
                                        truncated_at_floor=truncated, pixel_nm=float(ref['px_nm'])),
                             statement=(f"the reference high-Z size distribution is highest in its smallest resolved bin ({PSD_BINS[0]}-{PSD_BINS[1]} "
                                        f"µm: {pr[0]:.2f} vs at most {pr[1:].max():.2f} /1000 µm² above): it has not turned over at the "
                                        f"{PSD_BINS[0]} µm detection floor, so normal fines below the floor are unobserved")
                                       if truncated else f"the reference size distribution turns over above the {PSD_BINS[0]} µm detection floor"))
    else:
        rims.insert(0, dict(id=f'population:{batch}', type='population', scope='batch', target=batch, consequential=bool(pivotal),
                            basis=dict(n_reference_min=min(n_ref), n_reference_max=max(n_ref), n_independent=len(indep),
                                       n_reference_linked=len(entities) - len(indep), pivotal=pivotal,
                                       pivotal_cause=sorted({e['leverage']['cause'] for e in entities if e['id'] in pivotal}),
                                       prevalence=dict(out_of_family=n_out, n=len(indep), ci95=prev)),
                            statement=f"approved reference = {min(n_ref)}-{max(n_ref)} micrographs; {len(indep)} independent incoming micrographs"
                                      + (f"; verdict rests on {', '.join(pivotal)}" if pivotal else '')
                                      + f"; out-of-family prevalence {n_out}/{len(indep)} (95% CI {100 * prev[0]:.0f}-{100 * prev[1]:.0f}%)"))
    for dm in dims:
        s = dm.get('spatial_support')
        if s and s['cls'] != 'short-range':
            # reference: the adjacent-tile sampling assumption is challenged when the tile-excess 95% CI excludes 1
            rims.append(dict(id=f'spatial-dimension:{dm["id"]}', type='spatial', scope='dimension', target=dm['id'],
                             consequential=bool(is_ref and s['tile_excess_ci95'][0] > 1),
                             basis=dict(cls=s['cls'], tile_excess=s['tile_excess'], tile_excess_ci95=s['tile_excess_ci95'], range_um=s['range_um']),
                             statement=f"{dm['short_label']}: adjacent-tile variance {s['tile_excess']:.1f}× the short-range prediction (95% CI "
                                       f"{s['tile_excess_ci95'][0]:.1f}-{s['tile_excess_ci95'][1]:.1f}); " +
                                       (f"variogram range ≈ {s['range_um']:.0f} µm" if s['cls'] == 'fov-scale' else
                                        f"variogram still rising at {s['range_um']:.0f} µm (structure larger than the longest coherent capture)")))

    actions = (_reference_actions if is_ref else _actions)(entities, observations, dims, profiles, missing, rims, ref, d, sp)
    devs = [o['id'] for o in observations if o['reference_relation'].get('status') in ('deviant', 'out')]
    surv = [o['id'] for o in observations if o['scrutiny'].get('outcome') == 'survives']
    fields = sorted({f['field'] for p in profiles for run in p['runs'] for f in run['fields']} | {k for e in entities for k in e['fields']})
    context = dict(batch=batch, reference=ref['name'], statistical_unit='parent_micrograph',
                   model='two-level random-effects (approved material + tile sampling + baseline support), simulation-calibrated; not Bayesian')
    if is_ref:
        context['role'] = 'reference'
    out = dict(
        schema_version=SCHEMA_VERSION,
        context=context,
        decision=dict(verdict=d['verdict'], p_batch=d['p_batch'], d99=d['d99'], d95=d['d95'], severity=d.get('severity'),
                      tests=dict(severity_p=d['null'].get('p_severity'), count_p=d['null'].get('p_count'), combination='bonferroni_2'),
                      null_calibration=dict(p_any_outside_99=d['null'].get('p_any99'), p_any_outside_95=d['null'].get('p_any95')),
                      n_entities=len(entities), n_independent=len(indep), reference_linked=d.get('ref_linked', []), pivotal=pivotal,
                      consistent_out=d.get('consistent_out', []), moderate_out=d.get('moderate_out', []), validity_failed=d.get('gate_fail', []),
                      thresholds=dict(alpha_reject=ALPHA_REJECT, alpha_investigate=ALPHA_INVESTIGATE, acquisition_share_max=ACQ_SHARE_MAX, cnr_min=CNR_MIN),
                      reasons=d['reasons']),
        dimensions=dims, entities=entities, observations=observations, missing_dimensions=missing, spatial_profiles=profiles,
        rims=rims, actions=actions,
        provenance=dict(fields=[dict(id=k, batch=by_key[k]['batch'], fid=by_key[k]['fid'], entity=next((e['id'] for e in entities if k in e['fields']), None)
                                     or next((p['entity'] for p in profiles for run in p['runs'] for f in run['fields'] if f['field'] == k), None),
                                     width_um=by_key[k]['spatial']['width_um'], height_um=by_key[k]['spatial']['height_um'], px_nm=by_key[k]['px_nm'])
                                for k in fields if k in by_key],
                        edge_links=res.get('links', [])),
        summary=dict(deviating=devs, surviving=surv, n_deviating=len(devs), n_surviving=len(surv),
                     consequential_rims=[r['id'] for r in rims if r['consequential']]))
    if is_ref:
        out['decision']['self_audit'] = d['self_audit']
    return out


def _reference_actions(entities, observations, dims, profiles, missing, rims, ref, d, sp):
    """How the reference dataset itself should next be acquired. Every action is triggered by a reference-derived rim;
    tier 1 when that rim is consequential for the reference as a comparison anchor."""
    A = []
    dim = {x['id']: x for x in dims}
    R = {r['id']: r for r in rims}
    pop = rims[0]

    def add(**a):
        a['targets'] = dict(observations=a.pop('obs', []), entities=a.pop('ents', []), dimensions=a.pop('dims', []))
        a['triggered_by'] = [r for r in a.pop('rims', []) if r in R]
        a['trigger_facts'] = [dict(collection=c, id=i, path=p) for c, i, p in a.pop('facts', [])]
        a.setdefault('effect', None)
        A.append(a)

    tier = lambda rid: 1 if R[rid]['consequential'] else 2
    for e in entities:
        rid = f"validity:{e['id']}"
        if rid in R:
            fams = [f for f, ok in e['validity']['measurable'].items() if not ok]
            add(verb='REIMAGE', tier=tier(rid), addresses='validity', status='grounded', cost='low', ents=[e['id']], rims=[rid],
                facts=[('entities', e['id'], 'validity')],
                obs=[o['id'] for o in observations if o['entity'] == e['id'] and o['reference_relation']['status'] == 'not_measurable'],
                title=f"Re-image reference {e['id']} at the approved BSE settings", evidence=e['validity']['reasons'],
                rationale=f"{e['id']} belongs to the reference, but its {', '.join(fams)} measurements are not trustworthy at this "
                          'contrast-to-noise, so those reference statistics rest on one micrograph fewer. Re-imaging restores it; no analysis can.')
    rid = f"scale:{pop['target']}"
    if rid in R and R[rid]['consequential']:
        b = R[rid]['basis']
        add(verb='ZOOM', tier=1, addresses='scale', status='grounded', cost='low', dims=['additive_density', 'additive_d50_um'], rims=[rid],
            facts=[('rims', rid, 'basis')], title='Higher-magnification BSE on reference micrographs: resolve the approved fines below the floor',
            evidence=[R[rid]['statement']],
            rationale=f"The reference cannot say what normal looks like below {b['detection_floor_um']} µm, so any incoming sub-floor population "
                      'is compared with an unobserved baseline. A finer pixel (≤ 10 nm) on approved material resolves it.')
    for k in SPATIAL_KPIS:
        rid = f'spatial-dimension:{k}'
        if rid not in R or not R[rid]['consequential']:
            continue
        b = R[rid]['basis']
        if b['cls'] == 'fov-scale':
            add(verb='SPACE', tier=1, addresses='spatial_sampling', status='computed', cost='medium', dims=[k], rims=[rid],
                facts=[('dimensions', k, 'spatial_support')],
                title=f"{dim[k]['short_label']}: space reference fields ≥ {b['range_um']:.0f} µm apart instead of adjacent tiles",
                evidence=[R[rid]['statement']], effect=dict(kind='field_spacing', min_spacing_um=b['range_um'], basis=b['cls']),
                rationale='Adjacent reference tiles re-measure the same structure, so the tile-sampling spread they supply mixes sampling noise '
                          'with spatial structure. Fields spaced by the correlation range sample it approximately independently.')
        else:
            add(verb='EXTEND', tier=1, addresses='spatial_extent', status='computed', cost='low', dims=[k], rims=[rid],
                facts=[('dimensions', k, 'spatial_support')],
                title=f"{dim[k]['short_label']}: one longer coherent reference capture (> {b['range_um']:.0f} µm)",
                evidence=[R[rid]['statement']],
                rationale='The variogram has not reached its plateau within the longest reference capture, so the scale of this structure is '
                          'unknown; one longer mosaic of approved material locates it, and then tells how far apart fields must be.')
    for o in observations:
        rid = f"spatial:{o['id']}"
        if rid in R and R[rid]['basis']['open_edges'] and o['scrutiny'].get('outcome') == 'survives':
            edges = R[rid]['basis']['open_edges']
            add(verb='EXTEND', tier=tier(rid), addresses='spatial_extent', status='computed', cost='low', obs=[o['id']], ents=[o['entity']],
                rims=[rid], facts=[('spatial_profiles', o['id'], 'runs')], title=f"Extend reference {o['entity']} beyond its {' and '.join(edges)}",
                evidence=[R[rid]['statement']], effect=dict(kind='spatial_extent', known_extent_um=R[rid]['basis']['captured_length_um'], open_edges=edges),
                rationale='Tells whether this local departure is a bounded feature of approved material or part of a larger zone.')
    surv = [o['id'] for o in observations if o['scrutiny'].get('outcome') == 'survives']
    pick = sorted([x for x in dims if x['acquired'] and x['robustness']['cls'] == 'robust'],
                  key=lambda x: -pop['basis']['baseline_share_3_fields'][x['id']])[:3]
    proj = [dict(dimension=x['id'], mdc95_now=x['reference']['mdc95_3tiles'],
                 mdc95_with_plus5=_mdc_at(ref['kpi'][x['id']], ref['kpi'][x['id']]['n'] + 5)) for x in pick]
    add(verb='BASELINE', tier=1 if pop['consequential'] else 3, addresses='population', status='computed', cost='high', rims=[pop['id']], obs=surv,
        dims=[x['id'] for x in pick], facts=[('rims', pop['id'], 'basis')] + [('dimensions', x['id'], 'reference') for x in pick],
        title='Add independent reference micrographs (+5)',
        evidence=[pop['statement']] + ([f"local departures to place: {', '.join(surv)}"] if surv else []),
        effect=dict(kind='minimum_detectable_change', tiles_per_micrograph=3, projected=proj),
        rationale='Shrinks the baseline-estimation part of every envelope' + (
            ', and tells whether each local departure is a tail of the approved population or a distinct morphology' if surv else '') + '.')
    # reference order: restore invalid measurements first (cheap, recovers a micrograph), then resolve, then resample, then add
    A.sort(key=lambda a: (a['tier'], REF_VERB_ORDER.index(a['verb'])))
    for i, a in enumerate(A):
        a['id'] = f"{a['verb'].lower()}:{i + 1}"
        a['rank'] = i + 1
    return A


def _actions(entities, observations, dims, profiles, missing, rims, ref, d, sp):
    A = []
    O = {o['id']: o for o in observations}
    dim = {x['id']: x for x in dims}
    rim_ids = {r['id'] for r in rims}
    pop = rims[0]

    def add(**a):
        a['targets'] = dict(observations=a.pop('obs', []), entities=a.pop('ents', []), dimensions=a.pop('dims', []))
        a['triggered_by'] = [r for r in a.pop('rims', []) if r in rim_ids]
        a['trigger_facts'] = [dict(collection=c, id=i, path=p) for c, i, p in a.pop('facts', [])]
        a.setdefault('effect', None)
        A.append(a)

    for e in entities:
        if e['independence']['reference_linked']:
            continue
        pid, lev = e['id'], e['leverage']
        pivotal = bool(lev and lev['flips'])
        tier = 1 if pivotal else 2
        surv = [o for o in observations if o['entity'] == pid and o['scrutiny'].get('outcome') == 'survives']
        if pivotal and e['acquisition']['differs_from_approved'] and surv:
            add(verb='REPEAT', tier=1, addresses='acquisition', status='grounded', cost='low', obs=[o['id'] for o in surv], ents=[pid],
                rims=[pop['id'], f'acquisition:{pid}'], facts=[('entities', pid, 'leverage'), ('entities', pid, 'acquisition.differs_from_approved')], title=f'Repeat {pid} under the approved acquisition settings',
                evidence=[f"verdict changes without {pid} ({d['verdict']} → {lev['verdict_without']}, p = {lev['p_without']:.2f})",
                          f"{len(e['acquisition']['differs_from_approved'])} acquisition metrics differ from the approved micrographs"],
                rationale='The only test that separates acquisition from material for the decision-driving evidence. Tested perturbations '
                          'explain little, but kV / working distance / dwell were never varied; new fields elsewhere would confound both.')
        if f'scale:{pid}' in rim_ids:
            sd = e['size_distribution']
            add(verb='ZOOM', tier=tier, addresses='scale', status='grounded', cost='low', ents=[pid], rims=[f'scale:{pid}'], facts=[('entities', pid, 'size_distribution')],
                obs=[o['id'] for o in observations if f'scale:{pid}' in o['rims']], title=f'Higher magnification + low-kV BSE on {pid} fines',
                evidence=[f"{100 * sd['excess_share_below_0_7um']:.0f}% of excess objects < 0.7 µm; excess ratio {sd['peak_ratio_at_floor']:.1f}× at the "
                          f"{sd['detection_floor_um']} µm detection floor"],
                rationale='The anomalous population is cut off by the pixel size. A wider field only adds more truncated counts; a finer pixel '
                          '(≤ 10 nm) resolves the population, and low kV suppresses the sub-surface signal that makes fines look dim.')
        mr = next(x for x in missing if x['entity'] == pid)
        if mr['consequential']:
            fu = mr['basis']['fines_bse_intensity_u']
            add(verb='EDS', tier=tier, addresses='composition', status='future', cost='medium', ents=[pid], dims=['composition'],
                obs=mr['basis']['dependent_observations'], rims=[f'composition:{pid}'], facts=[('missing_dimensions', _oid(pid, 'composition'), 'basis')], title=f'Paired EDS: {pid} fines vs approved additive',
                evidence=['composition dimension not acquired'] + ([f'fine objects at the dim end of the approved BSE range (u = {fu:.2f})'] if fu is not None else []),
                rationale='BSE contrast cannot distinguish a finer specified additive from a different lower-Z phase; no further BSE capture '
                          'resolves chemistry. This decides supplier attribution.')
        for k in SPATIAL_KPIS:
            rid = f'spatial:{pid}:{k}'
            rim = next((r for r in rims if r['id'] == rid), None)
            if rim and rim['basis']['open_edges']:
                edges = rim['basis']['open_edges']
                add(verb='EXTEND', tier=tier, addresses='spatial_extent', status='computed', cost='low', obs=[_oid(pid, k)], ents=[pid], rims=[rid], facts=[('spatial_profiles', _oid(pid, k), 'runs')],
                    title=f"Extend the {pid} mosaic beyond its {' and '.join(edges)}",
                    evidence=[f"{dim[k]['short_label']} outside the approved local band along {100 * rim['basis']['fraction_outside_band']:.0f}% of the "
                              f"{rim['basis']['captured_length_um']:.0f} µm section and still outside at the {' and '.join(edges)}"],
                    effect=dict(kind='spatial_extent', known_extent_um=rim['basis']['captured_length_um'], open_edges=edges),
                    rationale='Bounds the anomalous region (local inclusion vs extended zone). More tiles inside the current section are '
                              'redundant: the deviation is already measured there (z = %.1f).' % O[_oid(pid, k)]['reference_relation']['z'])
    piv = [e for e in entities if e['leverage'] and e['leverage']['flips']]
    indep = [e for e in entities if not e['independence']['reference_linked']]
    prev = pop['basis']['prevalence']
    if piv or len(indep) < 5:
        proj = []
        for add_n in (7, 14, 21):
            kk = round(prev['out_of_family'] * (prev['n'] + add_n) / max(prev['n'], 1))
            lo, hi = _prevalence(kk, prev['n'] + add_n)
            proj.append(dict(added_sections=add_n, ci_width=hi - lo))
        redundant = [k for k in SPATIAL_KPIS if sp.get(k, {}).get('cls') in ('long-range', 'fov-scale')]
        add(verb='SECTIONS', tier=1 if piv else 2, addresses='population', status='computed', cost='medium',
            obs=[o['id'] for e in piv for o in observations if o['entity'] == e['id'] and o['scrutiny'].get('outcome') == 'survives'],
            ents=[e['id'] for e in piv], rims=[pop['id']] + [f'spatial-dimension:{k}' for k in redundant], facts=[('decision', 'batch', 'pivotal')] + [('entities', e['id'], 'leverage') for e in piv],
            title='Independent cross-sections from the lot (not adjacent tiles)',
            evidence=[pop['statement']] + ([f"adjacent tiles are partly redundant for {', '.join(dim[k]['short_label'] for k in redundant)} (structure ≥ field scale)"] if redundant else []),
            effect=dict(kind='prevalence_ci_width', assumption='same out-of-family rate', current=prev['ci95'][1] - prev['ci95'][0], projected=proj),
            rationale='Answers how much of the lot is affected. More tiles of an anomalous micrograph refine a number that is already decisive; '
                      'only independent sections constrain prevalence.')
    for k in SPATIAL_KPIS:
        s = sp.get(k)
        if not s or s['cls'] == 'short-range':
            continue
        incons = [e['id'] for e in indep if O[_oid(e['id'], k)]['reference_relation'].get('status') in ('deviant', 'out')
                  and not O[_oid(e['id'], k)]['scrutiny']['tile_consistent']]
        if incons:
            add(verb='SPACE', tier=2, addresses='spatial_sampling', status='computed', cost='medium', obs=[_oid(p, k) for p in incons], ents=incons,
                dims=[k], rims=[f'spatial-dimension:{k}'] + [f'spatial:{p}:{k}' for p in incons], facts=[('dimensions', k, 'spatial_support')] + [('observations', _oid(p, k), 'scrutiny') for p in incons],
                title=f"{dim[k]['short_label']}: fields spaced ≥ {s['range_um']:.0f} µm instead of adjacent tiles",
                evidence=[f"adjacent-tile variance {s['excess']:.1f}× short-range prediction (95% CI {s['excess_ci'][0]:.1f}-{s['excess_ci'][1]:.1f})",
                          f"deviation inconsistent across fields in {', '.join(incons)}"],
                effect=dict(kind='field_spacing', min_spacing_um=s['range_um'], basis=s['cls']),
                rationale='Fields closer than the correlation range re-measure the same structure; spacing them by at least the range makes each '
                          'field an approximately independent sample of this KPI.')
    for e in indep:
        if e['validity']['reasons']:
            add(verb='REIMAGE', tier=2, addresses='validity', status='grounded', cost='low', ents=[e['id']], rims=[f"validity:{e['id']}"], facts=[('entities', e['id'], 'validity')],
                obs=[o['id'] for o in observations if o['entity'] == e['id'] and o['reference_relation']['status'] == 'not_measurable'],
                title=f"Re-image {e['id']} at approved BSE settings", evidence=e['validity']['reasons'],
                rationale='The KPI cannot be measured at the current contrast-to-noise; no analysis can recover it.')
    hot = {o['dimension'] for o in observations if o['reference_relation'].get('status') in ('deviant', 'out')}
    pick = sorted([x for x in dims if x['acquired']], key=lambda x: (x['id'] not in hot, x['robustness']['cls'] != 'robust'))[:3]
    proj = [dict(dimension=x['id'], mdc95_now=x['reference']['mdc95_3tiles'],
                 mdc95_with_plus5=_mdc_at(ref['kpi'][x['id']], ref['kpi'][x['id']]['n'] + 5)) for x in pick]
    add(verb='BASELINE', tier=3, addresses='population', status='computed', cost='high', rims=[pop['id']], dims=[x['id'] for x in pick], facts=[('dimensions', x['id'], 'reference') for x in pick],
        title='Expand the approved reference (+5 independent micrographs)',
        evidence=[f"approved reference = {pop['basis']['n_reference_min']}-{pop['basis']['n_reference_max']} micrographs"],
        effect=dict(kind='minimum_detectable_change', tiles_per_micrograph=3, projected=proj),
        rationale='Every envelope is partly baseline-estimation uncertainty; this shrinks all of them, but changes no current flag.')
    A.sort(key=lambda a: (a['tier'], VERB_ORDER.index(a['verb'])))
    for i, a in enumerate(A):
        a['id'] = f"{a['verb'].lower()}:{i + 1}"
        a['rank'] = i + 1
    return A
