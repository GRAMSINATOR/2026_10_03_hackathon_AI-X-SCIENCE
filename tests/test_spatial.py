"""Marker-aware spatial statistics and their renderer-independent support contract."""
import json
import os

import numpy as np

from qc import spatial


ROOT = os.path.dirname(os.path.dirname(__file__))


def load(batch='Batch_3'):
    return json.load(open(os.path.join(ROOT, 'fixtures', f'epistemic_field.{batch}.json'), encoding='utf-8'))


def test_field_maps_keep_phase_and_count_statistics_distinct():
    lab = np.ones((64, 64), np.uint8)
    lab[:16, :16] = 0
    for y, x in ((4, 40), (12, 52), (28, 36), (44, 44), (52, 12)):
        lab[y, x] = 2
    out = spatial.field_maps(lab, 1000)
    phase = out['win']['porosity']['2']
    assert phase['normalized_fluctuation'] == phase['variance'] / (phase['mean'] * (1 - phase['mean']))
    count = out['win']['additive_density']['2']
    scale = count['window_area_um2'] / 1000
    assert np.isclose(count['number_variance'], count['variance'] * scale ** 2)
    assert np.isclose(count['fano'], count['number_variance'] / count['mean_count'])
    assert count['support'] == 'non_overlapping_square_windows'


def test_pooling_audit_reports_equal_field_df_and_parent_estimates():
    rows = [
        dict(variance=1.0, n_windows=3, parent='a'),
        dict(variance=4.0, n_windows=9, parent='b'),
        dict(variance=9.0, n_windows=3, parent='b'),
    ]
    x = spatial._variance_estimates(rows)
    assert np.isclose(x['current_equal_field'], 14 / 3)
    assert np.isclose(x['df_pooled'], (2 + 32 + 18) / 12)
    assert np.isclose(x['parent_equal'], (1 + (32 + 18) / 10) / 2)


def test_parent_band_is_deterministic_clustered_and_explicit():
    records, chains = [], {}
    for i, values in enumerate(([1, 2, 3, 4, 5, 6], [2, 3, 4, 5, 6, 7], [4, 5, 6, 7, 8, 9])):
        parent, key = f'p{i}', f'B__f{i}'
        records.append(dict(key=key, parent=parent, spatial={'cols': {'porosity': values}}))
        chains[parent] = [key]
    a = spatial.band(records, 'porosity', chains=chains, n_boot=200)
    b = spatial.band(records, 'porosity', chains=chains, n_boot=200)
    assert a == b
    assert a['kind'] == 'parent_cluster_predictive_envelope' and not a['calibrated']
    assert a['n_parents'] == 3 and a['n_windows'] == 9
    assert a['audit_population_spread']['semantics'] == 'population_spread_audit'
    assert a['simultaneous']['kind'] == 'parent_cluster_bootstrap_maximum_standardized_excursion'
    assert len(a['simultaneous']['threshold_by_n_windows']) == 64


def test_contract_exposes_support_matched_profiles_and_marker_adapters():
    f = load()
    dims = {d['id']: d for d in f['dimensions']}
    assert dims['porosity']['uncertainty_model']['observation_family'] == 'bounded_phase_fraction'
    assert dims['additive_density']['uncertainty_model']['uncertainty_adapter'] == 'number_variance_fano'
    assert all(e['size_distribution']['uncertainty_model']['observation_family'] == 'particle_size_distribution'
               for e in f['entities'] if e['size_distribution'] is not None)
    rows = dims['additive_density']['spatial_support']['scale_dependent_heterogeneity']
    assert [r['window_um'] for r in rows] == [2, 4, 8, 16, 32]
    assert all(r['n_windows'] > 0 and r['n_parents'] > 0 and r['fano'] > 0 for r in rows)
    for p in f['spatial_profiles']:
        assert p['column_um'] == 25 and p['window_um'] == 100
        assert p['comparison_support']['matched'] and not p['comparison_support']['raw_columns_inference']
        assert p['reference_band']['kind'] == 'parent_cluster_predictive_envelope'
        assert p['whole_profile_excursion']['window_count_matched']


def test_extreme_profiles_survive_parent_aware_whole_profile_screen():
    f = load()
    profiles = {p['id']: p for p in f['spatial_profiles']}
    density = profiles['M2060:additive_density']
    porosity = profiles['M2088:porosity']
    for p in (density, porosity):
        w = p['whole_profile_excursion']
        assert w['exceeds_approved_parent_maximum']
        assert w['ratio_to_approved_parent_maximum'] > 1
        assert w['n_reference_parents'] >= 5
        assert not w['calibrated']
    assert max(max(r['window_means']) for r in density['runs']) > density['reference_band']['hi']


def test_new_descriptors_do_not_change_batch_verdicts():
    assert load('Batch_2')['decision']['verdict'] == 'ACCEPT'
    assert load('Batch_3')['decision']['verdict'] == 'REJECT'
