"""End-to-end: folder -> fields -> features -> provenance -> micrographs -> reference / decision -> JSON report."""
import glob
import json
import os
from multiprocessing import Pool

import numpy as np

from . import brief, explain, field, hero, instrument, provenance, spatial, stats
from .features import CACHE, process_field
from .io import discover

REF_PATH = os.environ.get('QC_REF', 'cache/reference.json')
REPORTS = os.environ.get('QC_REPORTS', 'reports')


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def process_folder(folder, workers=None, force=False):
    fields = discover(folder)
    if not fields:
        raise SystemExit(f'no BSE fields found in {folder}')
    workers = workers or max(1, min(len(fields), (os.cpu_count() or 4) - 2, 10))
    with Pool(workers) as P:
        return P.starmap(process_field, [(f, force) for f in fields])


def known_records():
    return [json.load(open(p)) for p in sorted(glob.glob(os.path.join(CACHE, '*.json')))]


def _links(batch, prov, records):
    """For each parent in `batch`, which other batches contain tiles of the same parent micrograph."""
    out = {}
    for r in records:
        pid = prov['parent_of'][r['key']]
        if r['batch'] != batch:
            out.setdefault(pid, set()).add(r['batch'])
    return {k: sorted(v) for k, v in out.items()}


def build_reference(baseline_dir, noise_dirs=(), workers=None):
    """Reference = baseline micrographs (location, between-micrograph spread). Tile-sampling noise is pooled from
    replicate tiles of the same micrograph across baseline + noise_dirs (spread only, never their means)."""
    recs = process_folder(baseline_dir, workers)
    for d in noise_dirs:
        process_folder(d, workers)
    allr = known_records()
    prov = provenance.build(allr, os.path.basename(os.path.normpath(baseline_dir)))
    mgs = stats.micrographs(recs, prov['parent_of'])
    sw = stats.within_sd(allr, prov['parent_of'])
    ref = stats.build_reference(mgs, os.path.basename(os.path.normpath(baseline_dir)), sw)
    from .io import discover
    from . import robustness
    paths = {f['fid']: f['channels']['BSE'] for f in discover(baseline_dir)}
    pick = [m['fids'][0] for m in ref['micrographs'] if all(m['gate'].values())][:4]  # one valid tile per micrograph
    with Pool(min(12, (os.cpu_count() or 4) - 2)) as P:
        ref['robustness'], tested = robustness.card([paths[f] for f in pick], P)
    ref['robustness_tiles'] = pick
    # acquisition range whose KPI effect was actually measured = approved micrographs U perturbed images
    ref['acq_tested'] = {a: [min(lo, tested.get(a, [lo, hi])[0]), max(hi, tested.get(a, [lo, hi])[1])]
                         for a, (lo, hi) in ref['acq_envelope'].items()}
    # capture-geometry / spatial support model (spread and correlation only)
    gated = [m['parent'] for m in ref['micrographs'] if not m['gate']['additive']]
    ref['spatial'] = spatial.model(allr, prov['parent_of'], prov['chains'], gated)
    ok_add = [r for r in recs if prov['parent_of'][r['key']] not in gated]
    ref['psd_ref'] = spatial.psd_density(ok_add)
    tagged = [dict(r, parent=prov['parent_of'][r['key']]) for r in recs]
    ref['band'] = {k: spatial.band(tagged, k, gated if k.startswith('additive') else ()) for k in spatial.SPATIAL_KPIS}
    ref['tile_range'] = {}
    for k, meta in stats.KPIS.items():
        v = [t[k] for m in ref['micrographs'] if m['gate'][meta['family']] for t in m['tile_kpi'].values() if t.get(k) is not None]
        ref['tile_range'][k] = [float(min(v)), float(max(v))]
    os.makedirs(os.path.dirname(REF_PATH) or '.', exist_ok=True)
    json.dump(_clean(ref), open(REF_PATH, 'w'), indent=1)
    return ref


def assess(batch_dir, workers=None, ref=None):
    ref = ref or json.load(open(REF_PATH))
    recs = process_folder(batch_dir, workers)
    batch = recs[0]['batch']
    is_ref = batch == ref['name']
    allr = known_records()
    prov = provenance.build(allr, ref['name'])
    mgs = stats.micrographs(recs, prov['parent_of'])
    linked = set() if is_ref else {m['parent'] for m in ref['micrographs']}
    decision = stats.decide(mgs, ref, linked)
    if is_ref:
        decision.update(verdict='REFERENCE', reasons=['approved baseline: self-audit (leave-one-micrograph-out) shown per micrograph.']
                        + [f"{a['parent']}: {a['status']} (max |t| {a['max_t']:.1f}) {'; '.join(a['gate_reasons'])}" for a in ref['self_audit']])
    links = _links(batch, prov, allr)
    mtexts = [explain.micrograph_text(m, ref, links) for m in mgs]
    chains = {pid: ch for pid, ch in prov['chains'].items() if pid in {m['parent'] for m in mgs}}
    res = dict(batch=batch, reference=ref['name'], decision=decision, summary=explain.batch_summary(batch, decision, mtexts),
               micrographs=mgs, explanations=mtexts, chains=chains,
               links=[l for l in prov['links'] if l['parent'] in chains], n_fields=len(recs),
               mdc95={k: ref['kpi'][k]['mdc95'] for k in stats.KPIS})
    res['field'] = field.build(_clean(res), ref, recs, prov['chains'], allr)
    res['actions'] = [f"[{a['verb']}] {a['title']}" for a in res['field']['actions']]
    os.makedirs(os.path.join(REPORTS, batch), exist_ok=True)
    json.dump(_clean(res), open(os.path.join(REPORTS, batch, 'result.json'), 'w'), indent=1)
    open(os.path.join(REPORTS, batch, 'report.md'), 'w', encoding='utf-8').write(explain.markdown_report(_clean(res), ref))
    # representation boundary: the contract is written first; the V1 renderer reads only that JSON
    fpath = os.path.join(REPORTS, batch, 'field.json')
    json.dump(_clean(res['field']), open(fpath, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    open(os.path.join(REPORTS, batch, 'evidence_field.html'), 'w', encoding='utf-8').write(
        hero.render(json.load(open(fpath, encoding='utf-8'))))
    # human decision layer: governed brief derived from the contract only, checked against it before anything renders it
    F = json.load(open(fpath, encoding='utf-8'))
    B = brief.write(F, os.path.join(REPORTS, batch, 'brief.json'))
    bad = brief.check(B, F)
    if bad:
        raise ValueError(f'decision brief incoherent with the field: {bad[:5]}')
    if os.path.exists(instrument.DIST):   # primary renderer (build once: cd renderer && npm run build)
        open(os.path.join(REPORTS, batch, 'instrument.html'), 'w', encoding='utf-8').write(instrument.render(F, brief=B))
    return res
