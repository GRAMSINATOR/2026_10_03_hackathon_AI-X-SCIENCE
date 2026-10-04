"""Cross-reference comparison over complete epistemic fields; never a batch classifier."""
import hashlib
import json


SCHEMA_VERSION = 'reference-sensitivity/1'


def _state(status):
    if status in ('deviant', 'out'):
        return 'outside'
    if status == 'not_measurable':
        return 'not_measurable'
    return 'inside'


def intrinsic_payload(field):
    """Only target-side measurements. Reference links, scores, scrutiny and envelopes are deliberately absent."""
    return dict(
        batch=field['context']['batch'],
        entities={e['id']: dict(fields=e['fields'], geometry=e['geometry'], validity=e['validity'],
                                acquisition_metrics=e['acquisition']['metrics']) for e in field['entities']},
        observations={o['id']: dict(value=o['value'], per_field=o['per_field']) for o in field['observations']},
        profiles={p['id']: [dict(column_centres_um=r['column_centres_um'], column_values=r['column_values'])
                            for r in p['runs']] for p in field['spatial_profiles']})


def intrinsic_digest(field):
    raw = json.dumps(intrinsic_payload(field), sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def build(fields, frame_index):
    fields = sorted(fields, key=lambda f: f['context']['reference'])
    eligible = [x for x in frame_index['frames'] if x['eligible']]
    eligible_ids = [x['id'] for x in eligible]
    evaluated = [f['context']['reference'] for f in fields]
    digests = {f['context']['reference']: intrinsic_digest(f) for f in fields}
    complete = set(evaluated) == set(eligible_ids)
    intrinsic_unchanged = len(set(digests.values())) == 1
    dims = {d['id'] for f in fields for d in f['dimensions'] if d['acquired']}
    by_frame = {}
    for f in fields:
        ref = f['context']['reference']
        obs = {o['id']: o for o in f['observations']}
        dim_defs = {d['id']: d for d in f['dimensions']}
        dimension_rows = {}
        for dim in sorted(dims):
            rows = [o for o in obs.values() if o['dimension'] == dim]
            measurable = [o for o in rows if o['reference_relation']['status'] != 'not_measurable']
            outside = [o for o in measurable if _state(o['reference_relation']['status']) == 'outside']
            definition = dim_defs[dim]
            reference = definition.get('reference') or {}
            spatial = definition.get('spatial_support') or {}
            scales = spatial.get('scale_dependent_heterogeneity') or []
            dimension_rows[dim] = dict(measurable=len(measurable), outside=len(outside),
                                       max_abs_z=max((abs(o['reference_relation']['z']) for o in measurable), default=None),
                                       reference_mean=reference.get('mean'), reference_sd=reference.get('sd'),
                                       reference_n=reference.get('n_micrographs'),
                                       spatial_regime=dict(cls=spatial.get('cls'), range_um=spatial.get('range_um'),
                                                           beta=spatial.get('window_variance_slope'),
                                                           tile_excess=spatial.get('tile_excess'),
                                                           fano_by_scale=[dict(window_um=x.get('window_um'), fano=x.get('fano'))
                                                                          for x in scales if x.get('fano') is not None]))
        by_frame[ref] = dict(verdict=f['decision']['verdict'], p_batch=f['decision']['p_batch'],
                             n_independent=f['decision']['n_independent'], reference_linked=f['decision']['reference_linked'],
                             support=next(x['support'] for x in eligible if x['id'] == ref), dimensions=dimension_rows)
    all_ids = sorted(set.intersection(*[{o['id'] for o in f['observations']} for f in fields])) if fields else []
    findings = []
    for oid in all_ids:
        rows = []
        for f in fields:
            o = next(o for o in f['observations'] if o['id'] == oid)
            d = next(d for d in f['dimensions'] if d['id'] == o['dimension'])
            rr = o['reference_relation']
            rows.append(dict(reference=f['context']['reference'], status=rr['status'], state=_state(rr['status']),
                             z=rr.get('z'), q95=rr.get('q95'), envelope95=rr.get('envelope95'),
                             reference_mean=rr.get('approved_mean'), reference_sd=d.get('reference', {}).get('sd'),
                             reference_n=d.get('reference', {}).get('n_micrographs'),
                             beyond_reference_support=rr.get('beyond_reference_support')))
        states = {r['state'] for r in rows}
        classification = 'reference_invariant' if complete and len(states) == 1 else 'reference_sensitive'
        means = [r['reference_mean'] for r in rows if r['reference_mean'] is not None]
        sds = [r['reference_sd'] for r in rows if r['reference_sd'] is not None]
        findings.append(dict(id=oid, entity=oid.split(':', 1)[0], dimension=oid.split(':', 1)[1],
                             classification=classification, invariant_state=next(iter(states)) if len(states) == 1 else None,
                             frames=rows, why=dict(reference_mean_range=[min(means), max(means)] if means else None,
                                                   reference_sd_range=[min(sds), max(sds)] if sds else None,
                                                   reference_parent_range=[min(r['reference_n'] for r in rows),
                                                                           max(r['reference_n'] for r in rows)])))
    sensitive = [x for x in findings if x['classification'] == 'reference_sensitive']
    invariant_unusual = [x['id'] for x in findings if x['classification'] == 'reference_invariant'
                         and x['invariant_state'] == 'outside']
    sensitive_dims = sorted({x['dimension'] for x in sensitive})
    stable_dims = sorted(dims - set(sensitive_dims)) if complete else []
    verdicts = {r['verdict'] for r in by_frame.values()}
    return dict(schema_version=SCHEMA_VERSION, mode='comparative_exploration_not_classification',
                eligible_frames=eligible_ids, frames_evaluated=evaluated, complete=complete,
                intrinsic_measurement_digest=next(iter(digests.values())) if intrinsic_unchanged and digests else None,
                intrinsic_unchanged=intrinsic_unchanged, measurement_digest_by_frame=digests,
                conclusion='reference_sensitive' if len(verdicts) > 1 else 'reference_insensitive',
                verdicts_by_frame={k: v['verdict'] for k, v in by_frame.items()}, frames=by_frame,
                stable_dimensions=stable_dims, sensitive_dimensions=sensitive_dims,
                invariant_findings=invariant_unusual, frame_dependent_findings=[x['id'] for x in sensitive],
                findings=findings,
                guardrail='All eligible frames are compared together; reference selection is not significance shopping.')
