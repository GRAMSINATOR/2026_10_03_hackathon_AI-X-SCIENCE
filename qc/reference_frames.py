"""Explicit, cached scientific reference frames and their eligibility contract."""
import json
import os


SCHEMA_VERSION = 'reference-frame/1'
MIN_REFERENCE_PARENTS = 4
MIN_KPI_PARENTS = 3
SPATIAL_DIMENSIONS = ('additive_area_frac', 'additive_density', 'porosity')
ROOT = os.path.dirname(os.path.dirname(__file__))
REFERENCE_DIR = os.environ.get('QC_REFERENCES', os.path.join('cache', 'references'))
INDEX_PATH = os.path.join(REFERENCE_DIR, 'index.json')


def artifact_path(name):
    return os.path.join(REFERENCE_DIR, f'{name}.json')


def assess_support(ref):
    n_parents = len(ref.get('micrographs', []))
    by_dimension = {k: int(v.get('n', 0)) for k, v in ref.get('kpi', {}).items()}
    spatial = {k: dict(n_parents=int(v.get('scale_dependent_heterogeneity', [{}])[-1].get('n_parents', 0))
                           if v.get('scale_dependent_heterogeneity') else 0,
                       n_windows=int(v.get('scale_dependent_heterogeneity', [{}])[-1].get('n_windows', 0))
                           if v.get('scale_dependent_heterogeneity') else 0)
               for k, v in ref.get('spatial', {}).items()}
    bands = {k: int(v.get('n_parents', 0)) for k, v in ref.get('band', {}).items()}
    reasons = []
    if n_parents < MIN_REFERENCE_PARENTS:
        reasons.append(f'{n_parents} independent parent micrographs; at least {MIN_REFERENCE_PARENTS} are required')
    weak = sorted(k for k, n in by_dimension.items() if n < MIN_KPI_PARENTS)
    if weak:
        reasons.append('fewer than 3 valid parents for: ' + ', '.join(weak))
    if len(ref.get('robustness_tiles', [])) < 2:
        reasons.append('fewer than 2 fully valid acquisitions for robustness testing')
    missing_spatial = sorted(k for k in SPATIAL_DIMENSIONS if k not in spatial or
                             spatial[k]['n_parents'] < MIN_KPI_PARENTS or spatial[k]['n_windows'] < 1)
    if missing_spatial:
        reasons.append('insufficient spatial support for: ' + ', '.join(missing_spatial))
    quality = ('unavailable' if reasons else 'limited' if n_parents < 6 or min(by_dimension.values(), default=0) < 5
               or min(bands.values(), default=0) < 5 else 'supported')
    return dict(eligible=not reasons, unavailable_reasons=reasons, support_quality=quality,
                n_parent_micrographs=n_parents, n_valid_by_dimension=by_dimension,
                spatial_support=spatial, local_envelope_parents=bands,
                robustness_parent_tiles=len(ref.get('robustness_tiles', [])),
                acquisition_metrics=sorted(ref.get('acq_envelope', {})))


def annotate(ref):
    ref['schema_version'] = SCHEMA_VERSION
    ref['frame_identity'] = dict(id=ref['name'], source_batch=ref['name'], externally_approved=False,
                                 selection_semantics='explicit_comparison_frame')
    ref['eligibility'] = assess_support(ref)
    return ref


def entry(ref, path=None):
    return dict(id=ref['name'], label=ref['name'], eligible=ref['eligibility']['eligible'],
                unavailable_reasons=ref['eligibility']['unavailable_reasons'],
                support_quality=ref['eligibility']['support_quality'],
                support={k: v for k, v in ref['eligibility'].items()
                         if k not in ('eligible', 'unavailable_reasons', 'support_quality')},
                artifact=path or artifact_path(ref['name']), externally_approved=False)


def write_index(refs, path=INDEX_PATH):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    doc = dict(schema_version='reference-frame-index/1', frames=[entry(r) for r in sorted(refs, key=lambda x: x['name'])],
               eligibility_policy=dict(minimum_parent_micrographs=MIN_REFERENCE_PARENTS,
                                       minimum_valid_parents_per_production_kpi=MIN_KPI_PARENTS,
                                       parent_unit='parent_micrograph'))
    json.dump(doc, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    return doc


def load_index(path=INDEX_PATH):
    return json.load(open(path, encoding='utf-8'))


def resolve(selector):
    path = selector if selector and os.path.exists(selector) else artifact_path(selector)
    ref = json.load(open(path, encoding='utf-8'))
    if not ref.get('eligibility', {}).get('eligible'):
        why = '; '.join(ref.get('eligibility', {}).get('unavailable_reasons', [])) or 'eligibility was not established'
        raise ValueError(f'reference frame {ref.get("name", selector)} is unavailable: {why}')
    return ref
