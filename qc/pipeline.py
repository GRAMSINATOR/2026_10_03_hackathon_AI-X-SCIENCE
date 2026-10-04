"""End-to-end: folder -> fields -> features -> provenance -> micrographs -> reference / decision -> JSON report."""
import glob
import json
import os
from multiprocessing import Pool

import numpy as np

from . import brief, explain, field, hero, instrument, provenance, reference_frames, reference_sensitivity, spatial, stats
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


def build_reference(baseline_dir, noise_dirs=(), workers=None, out_path=None, activate=True):
    """Reference = baseline micrographs (location, between-micrograph spread). Tile-sampling noise is pooled from
    replicate tiles of the same micrograph across baseline + noise_dirs (spread only, never their means)."""
    recs = process_folder(baseline_dir, workers)
    for d in noise_dirs:
        process_folder(d, workers)
    allr = known_records()
    prov = provenance.build(allr)
    mgs = stats.micrographs(recs, prov['parent_of'])
    name = os.path.basename(os.path.normpath(baseline_dir))
    support_batches = {name, *(os.path.basename(os.path.normpath(d)) for d in noise_dirs)}
    noise_support = [r for r in allr if r['batch'] in support_batches]
    sw = stats.within_sd(noise_support, prov['parent_of'])
    # Stop before fitting a statistical frame when the candidate cannot meet the
    # minimum parent/KPI support.  It still gets a cached artifact and explicit
    # reasons in the registry, so an unavailable folder never vanishes silently.
    px = float(np.median([m['acq']['px_nm'] for m in mgs]))
    for m in mgs:
        stats.gate(m, px)
    valid_n = {k: sum(bool(m['gate'][meta['family']]) and np.isfinite(m['kpi'][k]) for m in mgs)
               for k, meta in stats.KPIS.items()}
    if len(mgs) < reference_frames.MIN_REFERENCE_PARENTS or min(valid_n.values(), default=0) < reference_frames.MIN_KPI_PARENTS:
        ref = dict(name=name, px_nm=px, micrographs=mgs,
                   kpi={k: dict(n=n, used=[m['parent'] for m in mgs
                                           if m['gate'][stats.KPIS[k]['family']] and np.isfinite(m['kpi'][k])])
                        for k, n in valid_n.items()},
                   secondary={}, acq_envelope={}, acq_tested={}, within=sw,
                   robustness={}, robustness_tiles=[], spatial={}, band={}, tile_range={}, self_audit=[])
        ref = reference_frames.annotate(_clean(ref))
        named_path = out_path or reference_frames.artifact_path(name)
        os.makedirs(os.path.dirname(named_path) or '.', exist_ok=True)
        json.dump(ref, open(named_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        return ref
    ref = stats.build_reference(mgs, name, sw)
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
    # Reference population structure is estimated from the selected frame itself.  The shared within-parent term above
    # may use explicitly named noise-support batches, but no other population's means enter these curves or envelopes.
    ref['spatial'] = spatial.model(recs, prov['parent_of'], prov['chains'], gated)
    ok_add = [r for r in recs if prov['parent_of'][r['key']] not in gated]
    ref['psd_ref'] = spatial.psd_density(ok_add)
    tagged = [dict(r, parent=prov['parent_of'][r['key']]) for r in recs]
    ref['band'] = {k: spatial.band(tagged, k, gated if k.startswith('additive') else (), chains=prov['chains'])
                   for k in spatial.SPATIAL_KPIS}
    ref['tile_range'] = {}
    for k, meta in stats.KPIS.items():
        v = [t[k] for m in ref['micrographs'] if m['gate'][meta['family']] for t in m['tile_kpi'].values() if t.get(k) is not None]
        ref['tile_range'][k] = [float(min(v)), float(max(v))]
    ref = reference_frames.annotate(_clean(ref))
    named_path = out_path or reference_frames.artifact_path(name)
    os.makedirs(os.path.dirname(named_path) or '.', exist_ok=True)
    json.dump(ref, open(named_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if activate:
        os.makedirs(os.path.dirname(REF_PATH) or '.', exist_ok=True)
        json.dump(ref, open(REF_PATH, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    return ref


def build_reference_frames(batch_dirs, workers=None, activate=None):
    """Build every candidate independently, record unavailable frames with reasons, and activate one explicitly."""
    batch_dirs = list(batch_dirs)
    if not batch_dirs:
        raise ValueError('at least one candidate reference folder is required')
    activate = activate or os.path.basename(os.path.normpath(batch_dirs[0]))
    refs = []
    for d in batch_dirs:
        name = os.path.basename(os.path.normpath(d))
        refs.append(build_reference(d, [x for x in batch_dirs if x != d], workers,
                                    out_path=reference_frames.artifact_path(name), activate=name == activate))
    index = reference_frames.write_index(refs)
    os.makedirs(REPORTS, exist_ok=True)
    json.dump(index, open(os.path.join(REPORTS, 'reference_frames.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    active = next((r for r in refs if r['name'] == activate), None)
    if active is None or not active['eligibility']['eligible']:
        why = '; '.join((active or {}).get('eligibility', {}).get('unavailable_reasons', []))
        raise ValueError(f'active reference frame {activate} is unavailable: {why}')
    return index


def _write_outputs(res, ref, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    json.dump(_clean(res), open(os.path.join(out_dir, 'result.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    open(os.path.join(out_dir, 'report.md'), 'w', encoding='utf-8').write(explain.markdown_report(_clean(res), ref))
    fpath = os.path.join(out_dir, 'field.json')
    json.dump(_clean(res['field']), open(fpath, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    F = json.load(open(fpath, encoding='utf-8'))
    open(os.path.join(out_dir, 'evidence_field.html'), 'w', encoding='utf-8').write(hero.render(F))
    B = brief.write(F, os.path.join(out_dir, 'brief.json'))
    bad = brief.check(B, F)
    if bad:
        raise ValueError(f'decision brief incoherent with the field: {bad[:5]}')
    if os.path.exists(instrument.DIST):
        open(os.path.join(out_dir, 'instrument.html'), 'w', encoding='utf-8').write(instrument.render(F, brief=B))


def assess(batch_dir, workers=None, ref=None, report_dir=None):
    explicit_reference = ref is not None
    if ref is None:
        ref = json.load(open(REF_PATH, encoding='utf-8'))
    elif isinstance(ref, (str, os.PathLike)):
        ref = reference_frames.resolve(os.fspath(ref))
    if ref.get('eligibility') and not ref['eligibility']['eligible']:
        raise ValueError(f"reference frame {ref['name']} is unavailable: {'; '.join(ref['eligibility']['unavailable_reasons'])}")
    recs = process_folder(batch_dir, workers)
    batch = recs[0]['batch']
    is_ref = batch == ref['name']
    allr = known_records()
    prov = provenance.build(allr)
    mgs = stats.micrographs(recs, prov['parent_of'])
    frames = None
    if is_ref:   # role REFERENCE: self-audit, each reference micrograph against the other parents only (never itself)
        for m in mgs:
            stats.gate(m, ref['px_nm'])
        frames = stats.loo_frames(mgs, allr, prov['parent_of'])
        decision = stats.self_audit(mgs, ref, frames)
    else:        # incoming batch: compared with the complete configured reference, exactly as before
        decision = stats.decide(mgs, ref, {m['parent'] for m in ref['micrographs']})
    links = _links(batch, prov, allr)
    # a reference micrograph is explained against its own leave-one-out frame, an incoming one against the full reference
    mtexts = [explain.micrograph_text(m, dict(ref, kpi=frames[m['parent']]['kpi']), links, against='the other reference micrographs')
              if frames else explain.micrograph_text(m, ref, links) for m in mgs]
    chains = {pid: ch for pid, ch in prov['chains'].items() if pid in {m['parent'] for m in mgs}}
    res = dict(batch=batch, reference=ref['name'], decision=decision, summary=explain.batch_summary(batch, decision, mtexts),
               micrographs=mgs, explanations=mtexts, chains=chains,
               links=[l for l in prov['links'] if l['parent'] in chains], n_fields=len(recs),
               mdc95={k: ref['kpi'][k]['mdc95'] for k in stats.KPIS})
    res['field'] = field.build(_clean(res), ref, recs, prov['chains'], allr, frames=frames)
    res['actions'] = [f"[{a['verb']}] {a['title']}" for a in res['field']['actions']]
    out_dir = report_dir or (os.path.join(REPORTS, batch, 'references', ref['name']) if explicit_reference
                             else os.path.join(REPORTS, batch))
    _write_outputs(res, ref, out_dir)
    return res


def compare_references(batch_dir, references=None, workers=None, active=None):
    """Evaluate one unchanged target against every eligible requested frame and serialize their joint sensitivity."""
    index = reference_frames.load_index()
    available = [x['id'] for x in index['frames'] if x['eligible']]
    names = list(references or available)
    invalid = [n for n in names if n not in available]
    if invalid:
        details = {x['id']: x['unavailable_reasons'] for x in index['frames'] if x['id'] in invalid}
        raise ValueError(f'unavailable reference frames requested: {details}')
    batch = os.path.basename(os.path.normpath(batch_dir))
    evaluated = []
    for name in names:
        ref = reference_frames.resolve(name)
        out = os.path.join(REPORTS, batch, 'references', name)
        res = assess(batch_dir, workers, ref=ref, report_dir=out)
        evaluated.append((name, ref, res, out))
    sensitivity = reference_sensitivity.build([x[2]['field'] for x in evaluated], index)
    for name, ref, res, out in evaluated:
        F = res['field']
        F['reference_frames'] = [dict(x, selected=x['id'] == name) for x in index['frames']]
        F['reference_sensitivity'] = sensitivity
        F['context']['reference_frame'] = dict(id=name, label=name, selection='explicit', externally_approved=False,
                                               support=next(x['support'] for x in index['frames'] if x['id'] == name))
        res['field'], res['reference_sensitivity'] = F, sensitivity
        _write_outputs(res, ref, out)
    active = active or (json.load(open(REF_PATH, encoding='utf-8'))['name'] if os.path.exists(REF_PATH) else names[0])
    if active in names:
        name, ref, res, _ = next(x for x in evaluated if x[0] == active)
        _write_outputs(res, ref, os.path.join(REPORTS, batch))
    return sensitivity
