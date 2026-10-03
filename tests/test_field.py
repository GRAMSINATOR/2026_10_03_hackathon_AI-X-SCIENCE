"""Scientific claims carried by the field are preserved (contract epistemic-field/1)."""
import json
import os

import pytest

from qc.field import _prevalence

ROOT = os.path.dirname(os.path.dirname(__file__))


def load(b):
    p = os.path.join(ROOT, 'reports', b, 'field.json')
    if not os.path.exists(p):
        pytest.skip('run the pipeline first')
    return json.load(open(p, encoding='utf-8'))


def obs(f, oid):
    return next(o for o in f['observations'] if o['id'] == oid)


def test_batch3_survival_leverage_and_rims():
    f = load('Batch_3')
    assert f['decision']['verdict'] == 'REJECT' and abs(f['decision']['p_batch'] - 0.017) < 0.005
    assert f['summary']['deviating'] == ['M2060:additive_density', 'M2068:additive_d50_um', 'M2088:porosity', 'M2088:pore_size_um']
    assert f['summary']['surviving'] == ['M2060:additive_density']
    assert f['decision']['pivotal'] == ['M2060']
    m = next(e for e in f['entities'] if e['id'] == 'M2060')
    assert m['leverage']['verdict_without'] == 'ACCEPT' and m['leverage']['cause'] == 'carries_decisive_evidence'
    assert set(obs(f, 'M2060:additive_density')['rims']) == {'scale:M2060', 'spatial:M2060:additive_density'}
    assert next(x for x in f['missing_dimensions'] if x['id'] == 'M2060:composition')['consequential']
    o = obs(f, 'M2088:porosity')
    assert o['scrutiny']['outcome'] == 'fails' and o['acquisition_explains_deviation']
    assert set(o['scrutiny']['failed']) == {'moderate_robustness_dimension', 'spatially_inconsistent', 'acquisition_could_explain'}
    assert obs(f, 'M2068:additive_d50_um')['scrutiny']['failed'] == ['spatially_inconsistent']


def test_scale_rim_numbers():
    f = load('Batch_3')
    r = next(r for r in f['rims'] if r['id'] == 'scale:M2060')
    assert r['basis']['excess_share_below_0_7um'] > 0.6 and r['basis']['peak_ratio_at_floor'] > 2.0 and r['basis']['detection_floor_um'] == 0.36


def test_actions_ranked_justified_and_traceable():
    for b in ('Batch_2', 'Batch_3'):
        for a in load(b)['actions']:
            assert a['evidence'] and a['rationale'] and (a['triggered_by'] or a['trigger_facts'])
    A = load('Batch_3')['actions']
    assert [a['verb'] for a in A] == ['REPEAT', 'ZOOM', 'EDS', 'EXTEND', 'SECTIONS', 'EXTEND', 'SPACE', 'BASELINE']
    assert A[0]['targets']['observations'] == ['M2060:additive_density']
    assert next(a for a in A if a['verb'] == 'EDS')['status'] == 'future'
    ext = A[3]
    assert ext['effect']['open_edges'] == ['start'] and ext['triggered_by'] == ['spatial:M2060:additive_density']
    assert not {'REPEAT', 'ZOOM', 'EDS'} & {a['verb'] for a in load('Batch_2')['actions']}


def test_reference_linked_entities_are_not_independent():
    f2, f3 = load('Batch_2'), load('Batch_3')
    assert f2['decision']['n_independent'] == 3 and set(f2['decision']['reference_linked']) == {'M2080', 'M2148', 'M2156'}
    assert f2['decision']['verdict'] == 'ACCEPT' and set(f2['decision']['pivotal']) == {'M2048', 'M2068', 'M2272'}
    assert {e['leverage']['cause'] for e in f2['entities'] if e['leverage']} == {'min_independent_count'}
    assert f3['decision']['reference_linked'] == ['M2080'] and f3['decision']['n_independent'] == 6


def test_spatial_classes():
    D = {d['id']: d for d in load('Batch_3')['dimensions']}
    assert D['additive_area_frac']['spatial_support']['cls'] == 'short-range'
    assert D['porosity']['spatial_support']['cls'] == 'fov-scale' and D['porosity']['spatial_support']['tile_excess_ci95'][0] > 1
    assert D['additive_density']['spatial_support']['cls'] == 'long-range'
    assert D['composition']['acquired'] is False


def test_m2060_extent_open_at_start():
    f = load('Batch_3')
    p = next(p for p in f['spatial_profiles'] if p['id'] == 'M2060:additive_density')
    assert len(p['runs']) == 1 and p['runs'][0]['open_at_start'] and p['runs'][0]['fraction_outside_band'] > 0.9


def test_prevalence_interval():
    lo, hi = _prevalence(1, 7)
    assert 0.003 < lo < 0.005 and 0.57 < hi < 0.59
    assert _prevalence(0, 5)[0] == 0.0
