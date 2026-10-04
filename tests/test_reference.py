"""Reference self-audit (role REFERENCE): Batch_1 renders through the normal machine, never as a QC verdict; each reference
micrograph is tested against a leave-one-parent-out frame, never against itself; incoming batches still use the full
reference; reference-derived limits produce actions and feed the Marker Frontier. Fixture-based unless marked."""
import json
import os

import numpy as np
import pytest

from qc import brief, contract, frontier, stats

ROOT = os.path.dirname(os.path.dirname(__file__))
fx = lambda name: json.load(open(os.path.join(ROOT, 'fixtures', name), encoding='utf-8'))
F1, F2, F3 = (fx(f'epistemic_field.Batch_{i}.json') for i in (1, 2, 3))
VERDICTS = ('ACCEPT', 'INVESTIGATE', 'REJECT')


def test_reference_field_is_a_role_not_a_verdict():
    assert F1['context']['role'] == 'reference'
    assert F1['decision']['verdict'] == 'REFERENCE' and F1['decision']['p_batch'] is None
    assert F1['decision']['self_audit']['method'] == 'leave_one_parent_out'
    assert contract.check(F1) == []
    assert all(e['leverage'] is None and not e['independence']['reference_linked'] for e in F1['entities'])


def test_reference_brief_never_shows_a_qc_verdict():
    B = brief.build(F1)
    assert brief.check(B, F1) == []
    assert B['hero']['decision']['state'] == 'REFERENCE'
    assert [B['hero'][k]['title'] for k in ('data_support', 'surviving_evidence', 'limits', 'acquisition_policy')] == \
           ['DATASET SELF-AUDIT', 'SURVIVING SIGNAL', 'OPEN LIMITS', 'NEXT ACQUISITION']
    for c in B['claims']:
        assert c['status'] not in VERDICTS and c['label'] not in VERDICTS
        for t in [c['text'], c.get('fact') or ''] + [d['text'] for d in c['details']]:
            assert not any(v in t for v in VERDICTS) and 'SUFFICIENT FOR QC' not in t
    assert 'SUFFICIENT FOR QC' not in json.dumps(B['hero'])


def test_check_rejects_a_verdict_or_a_defect_in_reference_mode():
    B = brief.build(F1)
    B['hero']['decision']['state'] = 'ACCEPT'
    assert any('REFERENCE' in v for v in brief.check(B, F1))
    B = brief.build(F1)
    c = next(x for x in B['claims'] if x['id'] == 'decision.verdict')
    c['template'] = '{0} contains a defect.'
    c['text'] = c['template'].format(F1['context']['batch'])
    assert any('defect' in v for v in brief.check(B, F1))


def test_every_reference_observation_uses_its_leave_one_out_frame():
    n = F1['decision']['self_audit']['n_parents']
    dims = {d['id']: d for d in F1['dimensions']}
    for o in F1['observations']:
        rr = o['reference_relation']
        if rr['status'] == 'not_measurable':
            continue
        assert rr['frame'] == 'leave_one_out'
        used = dims[o['dimension']]['reference']['n_micrographs']   # full-reference size for this KPI
        assert rr['frame_n'] == used - 1 <= n - 1                    # the parent itself is never in its frame


def _toy():
    """Six single-tile parents; parent P5 is an outlier on every KPI."""
    rng = np.random.default_rng(0)
    mgs, recs, parent_of = [], [], {}
    for i in range(6):
        pid = f'P{i}'
        kpi = {k: (40.0 if i == 5 else 20.0) + rng.normal(0, 1) for k in stats.KPIS}
        for t in range(2):
            key = f'B__{pid}_{t}'
            recs.append(dict(key=key, kpi={k: v + rng.normal(0, 0.5) for k, v in kpi.items()}, acq=dict(cnr_additive=10.0)))
            parent_of[key] = pid
        mgs.append(dict(parent=pid, kpi=kpi, n_tiles=1, gate={'additive': True, 'pore': True, 'structure': True}, gate_reasons=[],
                        tile_kpi={'t': kpi}, acq=dict(px_nm=25.0, cnr_additive=10.0)))
    return mgs, recs, parent_of


def test_leave_one_out_frames_exclude_the_held_out_parent():
    mgs, recs, parent_of = _toy()
    frames = stats.loo_frames(mgs, recs, parent_of, R_sim=2_000)
    for m in mgs:
        for k, R in frames[m['parent']]['kpi'].items():
            assert m['parent'] not in R['used'] and len(R['used']) == len(mgs) - 1
    # the outlier is far outside its leave-one-out frame, but would be partly absorbed by a model containing it
    k = next(iter(stats.KPIS))
    out = next(m for m in mgs if m['parent'] == 'P5')
    loo_t = stats.score(out, frames['P5'])[k]['t']
    full = stats._kpi_ref([m['kpi'][k] for m in mgs], [1] * 6, stats.within_sd(recs, parent_of)[k]['sd'], R_sim=2_000)
    self_t = stats.score(out, dict(kpi={k: full}))[k]['t']
    assert loo_t > 3 * self_t > 0


def test_incoming_batches_still_use_the_full_reference():
    for F in (F2, F3):
        assert 'role' not in F['context'] and F['decision']['verdict'] in VERDICTS
        assert all('frame' not in o['reference_relation'] for o in F['observations'])
        assert all(o['reference_relation'].get('approved_mean') == next(d for d in F['dimensions'] if d['id'] == o['dimension'])['reference']['mean']
                   for o in F['observations'] if o['reference_relation']['status'] != 'not_measurable')


def test_incoming_scientific_results_unchanged():
    assert (F2['decision']['verdict'], F3['decision']['verdict']) == ('ACCEPT', 'REJECT')
    assert F3['summary']['surviving'] == ['M2060:additive_density'] and F3['decision']['pivotal'] == ['M2060']
    assert F2['decision']['n_independent'] == 3 and F2['decision']['reference_linked'] == ['M2080', 'M2148', 'M2156']
    assert abs(F3['decision']['p_batch'] - 0.01666) < 1e-9


def test_reference_validity_failure_surfaces_and_produces_an_action():
    rim = next(r for r in F1['rims'] if r['id'] == 'validity:M2316')
    assert rim['consequential'] and 'contrast-to-noise' in rim['statement']
    assert all(o['reference_relation']['status'] == 'not_measurable' for o in F1['observations']
               if o['entity'] == 'M2316' and o['dimension'].startswith('additive'))
    B = brief.build(F1)
    assert 'limit.validity:M2316' in B['hero']['limits']['claims']
    act = next(a for a in F1['actions'] if 'validity:M2316' in a['triggered_by'])
    assert act['verb'] == 'REIMAGE' and act['tier'] == 1


def test_reference_limits_generate_acquisition_actions():
    triggered = {r for a in F1['actions'] for r in a['triggered_by']}
    for r in F1['rims']:
        if r['consequential']:
            assert r['id'] in triggered, r['id']
    assert {a['verb'] for a in F1['actions'] if a['tier'] == 1} >= {'REIMAGE', 'BASELINE'}


def test_reference_blindspots_feed_the_marker_frontier():
    idx = frontier.blindspot_index([F1, F2, F3])
    ref_cons = {b['key'] for b in idx if b['batch'] == 'Batch_1' and b['consequential']}
    assert {f"Batch_1/rims/{r['id']}" for r in F1['rims'] if r['consequential']} == ref_cons and ref_cons
    doc = frontier.build([F1, F2, F3], [])
    assert ref_cons <= set(doc['open_blindspots'])


def test_local_departures_are_never_called_defects():
    B = brief.build(F1)
    text = ' '.join([c['text'] for c in B['claims']] + [c.get('fact') or '' for c in B['claims']]).lower()
    assert 'defect' not in text
    reasons = ' '.join(F1['decision']['reasons']).lower()
    assert 'defect' not in reasons
    # the one departure in this reference fails scrutiny, and the hero says so instead of inventing a signal
    assert F1['summary']['surviving'] == [] and B['hero']['surviving_evidence']['state'] == 'NO STRONG INTERNAL DEPARTURE'


@pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, 'cache', 'reference.json')), reason='needs the local engine cache')
def test_committed_reference_fixture_matches_the_engine():
    F = json.load(open(os.path.join(ROOT, 'reports', 'Batch_1', 'field.json'), encoding='utf-8'))
    strip = lambda f: {k: v for k, v in contract.normalise(f).items() if k != 'assets'}
    assert strip(F) == {k: v for k, v in F1.items() if k != 'assets'}
