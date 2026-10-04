"""Representation contract `epistemic-field/1`: export, normalisation and coherence checks.

scientific model (qc.*)  ->  field.json (this contract)  ->  renderer (qc.hero V1, or any other).
A renderer needs only the JSON (and optional image assets); it must not import the scientific engine.
"""
import json
import math
import os

from PIL import Image

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema', 'epistemic_field.v1.schema.json')
PRESENTATION_WORDS = ('color', 'colour', 'brightness', 'hue', 'ring', 'flicker', 'pulse', 'glow', 'opacity', 'pixel_x', 'screen')


def normalise(o, sig=6):
    """Round floats to `sig` significant digits (stable fixtures); NaN/inf -> None."""
    if isinstance(o, dict):
        return {k: normalise(v, sig) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [normalise(v, sig) for v in o]
    if isinstance(o, float):
        if not math.isfinite(o):
            return None
        return float(f'{o:.{sig}g}')
    return o


def export_fixture(report_dir, out_dir, asset_src='cache/fields'):
    """Write a self-contained fixture: <out>/epistemic_field.<batch>.json + <out>/assets/<field>_BSE.jpg."""
    f = json.load(open(os.path.join(report_dir, 'field.json'), encoding='utf-8'))
    os.makedirs(os.path.join(out_dir, 'assets'), exist_ok=True)
    assets = {}
    for fld in f['provenance']['fields']:
        src = os.path.join(asset_src, f"{fld['id']}_BSE.jpg")
        if os.path.exists(src):
            rel = f"assets/{fld['id']}_BSE.jpg"
            im = Image.open(src).convert('L')
            im.resize((im.width // 2, im.height // 2)).save(os.path.join(out_dir, rel), quality=80)
            assets[fld['id']] = dict(image=rel, detector='BSE', downsample=8, image_px_um=fld['px_nm'] * 8 / 1000,
                                     width_um=fld['width_um'], height_um=fld['height_um'])
            lab = os.path.join(asset_src, f"{fld['id']}_lab.png")
            if os.path.exists(lab):   # registered segmentation produced by the engine (same frame as the BSE image)
                srel = f"assets/{fld['id']}_seg.png"
                L = Image.open(lab)
                L.resize((L.width // 2, L.height // 2), Image.NEAREST).save(os.path.join(out_dir, srel), optimize=True)
                assets[fld['id']]['segmentation'] = dict(image=srel, encoding={'0': 'pore', '1': 'matrix', '2': 'high_z'},
                                                         image_px_um=fld['px_nm'] * 8 / 1000)
    fx = normalise(dict(f, assets=assets))
    path = os.path.join(out_dir, f"epistemic_field.{f['context']['batch']}.json")
    json.dump(fx, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    from . import brief   # the matching governed decision brief, derived from the fixture itself
    brief.write(fx, os.path.join(out_dir, f"decision_brief.{f['context']['batch']}.json"))
    return path


def check(f):
    """Referential integrity + internal rule coherence. Returns a list of violations (empty = coherent)."""
    bad = []
    E = {e['id']: e for e in f['entities']}
    Dm = {d['id']: d for d in f['dimensions']}
    O = {o['id']: o for o in f['observations']}
    R = {r['id']: r for r in f['rims']}
    P = {p['id']: p for p in f['spatial_profiles']}
    M = {m['id']: m for m in f['missing_dimensions']}
    coll = dict(entities=E, dimensions=Dm, observations=O, rims=R, spatial_profiles=P, missing_dimensions=M)
    frames = f.get('reference_frames', [])
    selected = [x for x in frames if x.get('selected')]
    if len(selected) != 1 or selected[0].get('id') != f['context'].get('reference'):
        bad.append('exactly one serialized reference frame must be selected and match context.reference')
    unavailable = [x for x in frames if not x.get('eligible') and not x.get('unavailable_reasons')]
    if unavailable:
        bad.append('unavailable reference frames require explicit reasons')
    rf = f['context'].get('reference_frame', {})
    if rf.get('id') != f['context'].get('reference') or rf.get('selection') != 'explicit':
        bad.append('active reference identity is not explicit or does not match context.reference')
    sens = f.get('reference_sensitivity', {})
    if sens.get('complete'):
        if set(sens.get('frames_evaluated', [])) != set(sens.get('eligible_frames', [])):
            bad.append('complete reference sensitivity did not evaluate every eligible frame')
        if not sens.get('intrinsic_unchanged') or len(set(sens.get('measurement_digest_by_frame', {}).values())) != 1:
            bad.append('reference switching altered intrinsic target measurements')
    if sens.get('invariant_findings') and not sens.get('complete'):
        bad.append('reference-invariant findings require a complete cross-frame evaluation')
    classified = {x.get('id'): x.get('classification') for x in sens.get('findings', [])}
    if any(classified.get(x) != 'reference_invariant' for x in sens.get('invariant_findings', [])):
        bad.append('invariant finding lacks cross-frame agreement')
    if any(classified.get(x) != 'reference_sensitive' for x in sens.get('frame_dependent_findings', [])):
        bad.append('frame-dependent finding lacks a changed cross-frame state')
    adapter_fields = {'observation_family', 'support_model', 'uncertainty_adapter', 'reference_protocol'}
    for d in Dm.values():
        if not d['acquired']:
            continue
        if set(d.get('uncertainty_model', {})) != adapter_fields:
            bad.append(f"dimension {d['id']}: incomplete uncertainty adapter")
        sp = d.get('spatial_support')
        if not sp:
            continue
        if sp.get('observation_model') != d.get('uncertainty_model'):
            bad.append(f"dimension {d['id']}: spatial observation model differs from uncertainty adapter")
        rows = sp.get('scale_dependent_heterogeneity', [])
        for row in rows:
            if abs(row.get('window_area_um2', 0) - row.get('window_um', 0) ** 2) > 1e-6:
                bad.append(f"dimension {d['id']}: spatial window area does not match its side length")
            if min(row.get('n_windows', 0), row.get('n_fields', 0), row.get('n_parents', 0)) <= 0:
                bad.append(f"dimension {d['id']}: spatial support counts must be positive")
            if d['id'] == 'additive_density' and any(row.get(x) is None for x in ('mean_count', 'number_variance', 'fano')):
                bad.append('dimension additive_density: count-process descriptor missing')
            if d['id'] in ('additive_area_frac', 'porosity') and row.get('normalized_fluctuation') is None:
                bad.append(f"dimension {d['id']}: phase-fraction normalisation missing")
    for o in f['observations']:
        if o['entity'] not in E or o['dimension'] not in Dm or not Dm[o['dimension']]['acquired']:
            bad.append(f"observation {o['id']}: dangling entity/dimension")
        for r in o['rims']:
            if r not in R:
                bad.append(f"observation {o['id']}: unknown rim {r}")
        if o['entity'] in E and not set(o['per_field']) <= set(E[o['entity']]['fields']):
            bad.append(f"observation {o['id']}: per_field keys are not fields of its entity")
        rr, sc = o['reference_relation'], o['scrutiny']
        if rr['status'] == 'not_measurable':
            if sc['outcome'] != 'not_applicable':
                bad.append(f"{o['id']}: unmeasurable but scrutinised")
            continue
        z, q95, q99 = abs(rr['z']), rr['q95'], rr['q99']
        exp = 'out' if z > q99 else 'deviant' if z > q95 else 'in'
        if exp != rr['status']:
            bad.append(f"{o['id']}: status {rr['status']} inconsistent with |z|={z:.3g}, q95={q95:.3g}, q99={q99:.3g}")
        if abs(rr['exceedance_ratio'] - z / q95) > 1e-3 * max(1, z / q95):
            bad.append(f"{o['id']}: exceedance_ratio != |z|/q95")
        if abs(sum(o['variance_shares'].values()) - 1) > 1e-4:
            bad.append(f"{o['id']}: variance shares do not sum to 1")
        deviating = rr['status'] in ('deviant', 'out')
        if deviating != (sc['outcome'] != 'not_applicable'):
            bad.append(f"{o['id']}: scrutiny applicability inconsistent with status")
        if sc['outcome'] == 'survives' and (sc['failed'] or not sc['robust_dimension'] or not sc['tile_consistent']
                                           or (sc['acquisition_share'] or 0) >= sc['acquisition_share_max']):
            bad.append(f"{o['id']}: survives but a scrutiny condition fails")
        if sc['outcome'] == 'fails' and not sc['failed']:
            bad.append(f"{o['id']}: fails without a reason code")
        if rr['envelope95'] and not (rr['envelope95'][0] <= rr['approved_mean'] <= rr['envelope95'][1]):
            bad.append(f"{o['id']}: approved mean outside its own envelope")
    for e in f['entities']:
        sd = e.get('size_distribution')
        if sd is not None and set(sd.get('uncertainty_model', {})) != adapter_fields:
            bad.append(f"entity {e['id']}: particle-size distribution uncertainty adapter missing")
        for d in Dm.values():
            if d['acquired'] and f"{e['id']}:{d['id']}" not in O:
                bad.append(f"missing observation {e['id']}:{d['id']}")
            if not d['acquired'] and f"{e['id']}:{d['id']}" not in M:
                bad.append(f"missing-dimension relevance absent for {e['id']}:{d['id']}")
        lev = e['leverage']
        if f['context'].get('role') == 'reference':
            if lev is not None or e['independence']['reference_linked']:
                bad.append(f"entity {e['id']}: a reference self-audit has no decision leverage and no reference-linked entities")
        elif e['independence']['reference_linked'] != (lev is None):
            bad.append(f"entity {e['id']}: leverage must be null exactly for reference-linked entities")
    dec = f['decision']
    if f['context'].get('role') == 'reference':   # a role, never a verdict; every measurable observation in its own frame
        if dec['verdict'] != 'REFERENCE' or dec['p_batch'] is not None or 'self_audit' not in dec:
            bad.append('reference role: verdict must be REFERENCE, with no batch p and a self_audit block')
        for o in f['observations']:
            if o['reference_relation']['status'] != 'not_measurable' and o['reference_relation'].get('frame') != 'leave_one_out':
                bad.append(f"{o['id']}: reference observation not related to its leave-one-out frame")
    elif dec['verdict'] == 'REFERENCE':
        bad.append('verdict REFERENCE without the reference role')
    if sorted(dec['pivotal']) != sorted(e['id'] for e in f['entities'] if e['leverage'] and e['leverage']['flips']):
        bad.append('decision.pivotal inconsistent with entity leverage')
    if dec['n_independent'] != sum(not e['independence']['reference_linked'] for e in f['entities']):
        bad.append('decision.n_independent inconsistent with entities')
    for r in f['rims']:
        tgt = r['target']
        ok = {'batch': tgt == f['context']['batch'], 'entity': tgt in E, 'observation': tgt in O, 'dimension': tgt in Dm}[r['scope']]
        if not ok:
            bad.append(f"rim {r['id']}: target {tgt} not found for scope {r['scope']}")
    for m in f['missing_dimensions']:
        if m['entity'] not in E or m['dimension'] not in Dm or Dm[m['dimension']]['acquired']:
            bad.append(f"missing-dimension entry {m['id']} dangling")
        if m['consequential'] != bool(m['basis']['dependent_observations']):
            bad.append(f"missing-dimension {m['id']}: consequential flag inconsistent with dependent observations")
    for p in f['spatial_profiles']:
        if p['entity'] not in E or p['dimension'] not in Dm:
            bad.append(f"profile {p['id']} dangling")
        support, band = p.get('comparison_support', {}), p.get('reference_band', {})
        if not support.get('matched') or support.get('observed_window_um') != p['window_um'] or \
                support.get('reference_window_um') != p['window_um']:
            bad.append(f"profile {p['id']}: observed and reference support differ")
        if band.get('kind') != 'parent_cluster_predictive_envelope' or band.get('statistic') != 'local_window_mean':
            bad.append(f"profile {p['id']}: reference band semantics missing")
        excursion = p.get('whole_profile_excursion', {})
        if not excursion.get('support_matched') or not excursion.get('window_count_matched') or \
                excursion.get('n_reference_parents') != band.get('n_parents'):
            bad.append(f"profile {p['id']}: whole-profile diagnostic support mismatch")
        if excursion.get('calibrated') is not False or band.get('calibrated') is not False:
            bad.append(f"profile {p['id']}: descriptive diagnostics must not claim calibration")
        for run in p['runs']:
            if run['fields'] and run['fields'][0]['x0_um'] != 0:
                bad.append(f"profile {p['id']}: run frame must start at 0 (run separation is unknown)")
    ranks = [a['rank'] for a in f['actions']]
    if ranks != list(range(1, len(ranks) + 1)) or [a['tier'] for a in f['actions']] != sorted(a['tier'] for a in f['actions']):
        bad.append('actions not ranked by tier')
    for a in f['actions']:
        for o in a['targets']['observations']:
            if o not in O:
                bad.append(f"action {a['id']}: target observation {o} missing")
        for e in a['targets']['entities']:
            if e not in E:
                bad.append(f"action {a['id']}: target entity {e} missing")
        for d in a['targets']['dimensions']:
            if d not in Dm:
                bad.append(f"action {a['id']}: target dimension {d} missing")
        for r in a['triggered_by']:
            if r not in R:
                bad.append(f"action {a['id']}: trigger rim {r} missing")
        for t in a['trigger_facts']:
            if t['collection'] == 'decision':
                continue
            if t['id'] not in coll.get(t['collection'], {}):
                bad.append(f"action {a['id']}: trigger fact {t} unresolved")
        if not (a['triggered_by'] or a['trigger_facts']):
            bad.append(f"action {a['id']}: no trigger")
    s = f['summary']
    if s['surviving'] != [o['id'] for o in f['observations'] if o['scrutiny'].get('outcome') == 'survives']:
        bad.append('summary.surviving inconsistent')
    if s['consequential_rims'] != [r['id'] for r in f['rims'] if r['consequential']]:
        bad.append('summary.consequential_rims inconsistent')

    def keys(o, path=''):
        if isinstance(o, dict):
            for k, v in o.items():
                yield path + '.' + k
                yield from keys(v, path + '.' + k)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v, path)
    for k in keys({kk: vv for kk, vv in f.items() if kk != 'assets'}):
        leaf = k.rsplit('.', 1)[-1].lower()
        if any(w in leaf for w in PRESENTATION_WORDS):
            bad.append(f'presentation vocabulary in contract key {k}')
    return bad
