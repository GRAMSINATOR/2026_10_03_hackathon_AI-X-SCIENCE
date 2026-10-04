"""Marker Frontier (marker-frontier/1): ingestion socket, blindspot resolution, gate / state governance, fixture
isolation and reproducibility. Runs on the committed fixtures (no engine cache needed). The synthetic "literature" in
this file is test-only input (10.0000/* DOIs) and never written to a fixture."""
import copy
import json
import os

import jsonschema
import pytest

from qc import frontier

ROOT = os.path.dirname(os.path.dirname(__file__))
SCHEMA = json.load(open(frontier.SCHEMA_PATH, encoding='utf-8'))


@pytest.fixture(scope='module')
def seed():
    return frontier.fixture_inputs(example=False)


@pytest.fixture(scope='module')
def example():
    return frontier.fixture_inputs(example=True)


def by_id(doc, coll):
    return {x['id']: x for x in doc[coll]}


def bundle(kind='research_agent', **colls):
    return dict(schema_version='marker-research/1', bundle=dict(id=f'test.{kind}', kind=kind, produced_by='pytest'), **colls)


def paper(pid, group, target, gate, direction='SUPPORTIVE', directness='direct', method='strong', fixture=False):
    return dict(id=pid, title=f'Test source {pid}', year=2020, venue='test venue', doi=f'10.0000/{pid[6:]}', independence_group=group,
                provenance=dict(kind='fixture' if fixture else 'literature'),
                assessments=[dict(target=target, gate=gate, direction=direction, directness=directness, method_strength=method,
                                  transferability=dict(material='similar', modality='same', scale='same', task='same', process='unknown'),
                                  claim='test proposition', note='test')])


REF = dict(batch='Batch_3', collection='rims', id='scale:M2060', path='basis')


def record(rid, target, gate, outcome):
    return dict(id=rid, kind='current_data_test', title=rid, field_ref=REF, assessments=[dict(target=target, gate=gate, outcome=outcome, claim='test')])


def admissible_marker_bundle(review=True, measurable=True):
    t = 'marker:test_admit'
    m = dict(id=t, name='Test marker', family='spatial_statistic', proposition='test', current_capture_compatible=True,
             blindspot_refs=[dict(batch='Batch_3', collection='rims', id='scale:M2060')],
             known_confounds=[dict(id='c1', label='confound', controlled=True, basis=['record:t.rob'])])
    recs = [record('record:t.meas', t, 'measurability', 'passed' if measurable else 'inconclusive'),
            record('record:t.rob', t, 'robustness', 'passed'), record('record:t.nr', t, 'non_redundancy', 'passed')]
    pap = [paper('paper:t-a', 'g1', t, 'scientific_relevance'), paper('paper:t-b', 'g2', t, 'scientific_relevance', method='moderate')]
    rv = [dict(target=t, decision='admit', by='pytest reviewer', date='2026-10-04')] if review else []
    return bundle(markers=[m], records=recs, papers=pap, reviews=rv)


def critical_mass_bundle(review=False, demands=2):
    cap = 'capability:test_cap'
    ms, pap = [], [paper('paper:c-a', 'cg1', cap, 'literature_convergence'), paper('paper:c-b', 'cg2', cap, 'literature_convergence', method='moderate')]
    for i in range(demands):
        mid = f'marker:test_need{i}'
        ms.append(dict(id=mid, name=f'need {i}', family='composition', proposition='test', current_capture_compatible=False,
                       required_capabilities=[cap], blindspot_refs=[dict(batch='Batch_3', collection='rims', id='composition:M2060')]))
        pap += [paper(f'paper:m{i}-a', f'mg{i}a', mid, 'scientific_relevance'), paper(f'paper:m{i}-b', f'mg{i}b', mid, 'scientific_relevance', method='moderate')]
    c = dict(id=cap, name='Test capability', capability_type='spectroscopy',
             existing_capability_substitutes=[dict(id='s1', label='substitute', ruled_out=True,
                                                   basis=[dict(batch='Batch_3', collection='rims', id='composition:M2060', path='statement')])],
             integration=dict(burden='medium', acceptable=True))
    rv = [dict(target=cap, decision='recommend', by='pytest reviewer', date='2026-10-04')] if review else []
    return bundle(markers=ms, capabilities=[c], papers=pap, reviews=rv)


# ---------------------------------------------------------------- socket and reproducibility
@pytest.mark.parametrize('path', [os.path.join(ROOT, 'research', 'seed.controller.json'), frontier.EXAMPLE_BUNDLE])
def test_bundles_validate_against_the_ingestion_schema(path):
    jsonschema.validate(json.load(open(path, encoding='utf-8')), SCHEMA)


def test_schema_rejects_asserted_states_and_scores():
    b = json.load(open(frontier.EXAMPLE_BUNDLE, encoding='utf-8'))
    bad = copy.deepcopy(b)
    bad['markers'][0]['status'] = 'ADMITTED'
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, SCHEMA)
    bad = copy.deepcopy(b)
    bad['papers'][0]['assessments'][0]['evidence_score'] = 8.7
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, SCHEMA)


@pytest.mark.parametrize('example_mode', [False, True])
def test_committed_fixture_is_coherent_and_reproducible(example_mode):
    fields, bundles = frontier.fixture_inputs(example_mode)
    doc = frontier.build(fields, bundles)
    assert frontier.check(doc, fields, bundles) == []
    name = 'marker_frontier.example.json' if example_mode else 'marker_frontier.json'
    assert json.load(open(os.path.join(ROOT, 'fixtures', name), encoding='utf-8')) == json.loads(json.dumps(doc))


def test_build_is_deterministic(seed):
    fields, bundles = seed
    a = frontier.build(copy.deepcopy(fields), copy.deepcopy(bundles))
    b = frontier.build(list(reversed(copy.deepcopy(fields))), copy.deepcopy(bundles))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_lanes_are_in_rule_order(example):
    doc = frontier.build(*example)
    M = by_id(doc, 'markers')
    order = [frontier.MARKER_STATES.index(M[i]['status']) for i in doc['lanes']['current_capture']]
    assert order == sorted(order)
    tampered = copy.deepcopy(doc)
    tampered['lanes']['current_capture'].reverse()
    assert any('rule order' in v for v in frontier.check(tampered))


# ---------------------------------------------------------------- references resolve
def test_every_evidence_and_marker_reference_resolves(example):
    doc = frontier.build(*example)
    M, C = by_id(doc, 'markers'), by_id(doc, 'capabilities')
    for src in doc['papers'] + doc['records']:
        for a in src['assessments']:
            assert a['target'] in M or a['target'] in C
    for c in doc['capabilities']:
        for mid in c['markers_unlocked']:
            assert c['id'] in M[mid]['required_capabilities']
    for m in doc['markers']:
        assert all(cid in C for cid in m['required_capabilities'])


def test_dangling_evidence_target_is_a_violation(seed):
    fields, bundles = seed
    b = bundle(papers=[paper('paper:dangling', 'g', 'marker:does_not_exist', 'scientific_relevance')])
    doc = frontier.build(fields, bundles + [b])
    assert any('resolves to no case' in v for v in frontier.check(doc))


def test_blindspot_refs_resolve_or_are_explicitly_general(seed):
    doc = frontier.build(*seed)
    for case in doc['markers'] + doc['capabilities']:
        for r in case['blindspot_refs']:
            assert r['resolved'] or (r['external'] and r['general'])
    fields, bundles = seed
    b = bundle(markers=[dict(id='marker:stale', name='stale', family='scalar', proposition='x',
                             blindspot_refs=[dict(batch='Batch_9', collection='rims', id='scale:M9999')])])
    assert any('not marked general' in v for v in frontier.check(frontier.build(fields, bundles + [b])))


def test_engine_facts_and_project_records_resolve(seed):
    doc = frontier.build(*seed)
    for r in doc['records']:
        assert r.get('resolved', True)
        if r.get('source'):
            assert r['source']['locator'] in open(os.path.join(ROOT, r['source']['path']), encoding='utf-8').read()


def test_real_papers_need_a_canonical_link(seed):
    fields, bundles = seed
    p = paper('paper:nolink', 'g', 'marker:fines_subfloor_size', 'scientific_relevance')
    p['doi'] = None
    assert any('canonical https link' in v for v in frontier.check(frontier.build(fields, bundles + [bundle(papers=[p])])))
    ok = frontier.build(fields, bundles + [bundle(papers=[paper('paper:linked', 'g', 'marker:fines_subfloor_size', 'scientific_relevance')])])
    assert by_id(ok, 'papers')['paper:linked']['url'] == 'https://doi.org/10.0000/linked'


# ---------------------------------------------------------------- seeded states are the honest ones
def test_seeded_states_follow_the_current_field(seed):
    doc = frontier.build(*seed)
    M, C = by_id(doc, 'markers'), by_id(doc, 'capabilities')
    eds = C['capability:eds']
    assert eds['status'] == 'BUILDING_CASE'                       # one consequential need, from the engine
    assert 'Batch_3/rims/composition:M2060' in eds['closes_consequential']
    assert eds['gates']['literature_convergence']['state'] == 'open' and 'RESEARCH CASE OPEN' in eds['qualifiers']
    assert eds['gates']['non_substitutability']['state'] == 'partial'   # low-kV BSE not yet assessed
    assert M['marker:high_z_composition']['status'] == 'UNAVAILABLE' and M['marker:high_z_composition']['lane'] == 'new_capability'
    assert M['marker:latent_progression']['status'] == 'CONFOUNDED'     # research log #5
    assert M['marker:multiscale_heterogeneity']['status'] == 'REJECTED'  # research log #7
    assert M['marker:fines_subfloor_size']['status'] == 'BUILDING'
    assert M['marker:fines_subfloor_size']['existing_data_test']['status'] == 'requires_acquisition'
    assert [a['verb'] for a in M['marker:fines_subfloor_size']['existing_data_test']['requires_actions']] == ['ZOOM']
    assert C['capability:tomography_3d']['status'] == 'WATCHING'
    assert doc['context']['literature_present']
    assert M['marker:count_overdispersion_curve']['status'] == 'BUILDING'
    assert M['marker:phase_fraction_heterogeneity_curve']['status'] == 'BUILDING'
    for cid in ('marker:fines_subfloor_size', 'capability:eds'):
        assert (M.get(cid) or C.get(cid))['counts']['papers'] == 0


def test_open_blindspots_pull_research(seed):
    doc = frontier.build(*seed)
    assert 'Batch_3/rims/population:Batch_3' in doc['open_blindspots']
    assert 'Batch_3/reference_sensitivity/cross_reference' not in doc['open_blindspots']
    assert 'Batch_3/rims/composition:M2060' not in doc['open_blindspots']
    B = {b['key']: b for b in doc['blindspots']}
    assert B['Batch_3/reference_sensitivity/cross_reference']['actions'] == []
    assert 'marker:count_overdispersion_curve' in B['Batch_3/reference_sensitivity/cross_reference']['addressed_by']


# ---------------------------------------------------------------- opportunity topology
def test_current_frontier_is_deterministic_categorical_attention(seed):
    doc = frontier.build(*seed)
    M = by_id(doc, 'markers')
    assert doc['opportunity_map']['current_frontier'] == [
        'marker:fines_subfloor_size', 'marker:high_z_composition', 'marker:phase_conditioned_fines_distribution'
    ]
    assert [M[mid]['opportunity_rank'] for mid in doc['opportunity_map']['current_frontier']] == [1, 2, 3]
    assert doc['opportunity_map']['ranking_policy']
    for m in doc['markers']:
        assert m['ranking_factors']
        assert not any(k.endswith('_score') for k in m)


def test_candidate_classes_separate_capture_from_observability(seed):
    doc = frontier.build(*seed)
    groups = doc['opportunity_map']['candidate_markers']
    assert groups['computable_now'][:4] == [
        'marker:open_edge_persistence', 'marker:phase_fraction_heterogeneity_curve',
        'marker:spatial_correlation_length', 'marker:count_overdispersion_curve',
    ]
    assert {'marker:high_z_pair_correlation', 'marker:high_z_nearest_neighbour', 'marker:phase_boundary_morphology',
            'marker:phase_chord_distribution', 'marker:phase_lineal_path', 'marker:minkowski_phase_morphology'} <= set(groups['computable_now'])
    assert groups['needs_targeted_capture'] == ['marker:fines_subfloor_size']
    assert 'marker:phase_conditioned_fines_distribution' in groups['requires_new_observability']
    assert groups['set_aside'] == ['marker:latent_progression', 'marker:multiscale_heterogeneity']
    assert set().union(*map(set, groups.values())) == {m['id'] for m in doc['markers']}


def test_qualitative_marker_and_vortex_links_are_first_class(seed):
    doc = frontier.build(*seed)
    M, V = by_id(doc, 'markers'), by_id(doc, 'vortices')
    m = M['marker:open_edge_persistence']
    assert m['marker_kind'] == 'qualitative' and m['representation'] == 'categorical_state'
    assert m['observable'].startswith('Whether a measured deviation closes')
    assert 'record:engine.open_edge_M2060' in {e['id'] for e in m['evidence']}
    assert m['vortex_refs']
    for vid in m['vortex_refs']:
        assert m['id'] in V[vid]['marker_refs']
        assert V[vid]['evidence_refs']


def test_observability_attractor_pools_multiple_marker_opportunities(seed):
    doc = frontier.build(*seed)
    M, C = by_id(doc, 'markers'), by_id(doc, 'capabilities')
    eds = C['capability:eds']
    assert doc['opportunity_map']['tooling_attractors'][0] == eds['id']
    assert eds['marker_pool'] == ['marker:high_z_composition', 'marker:phase_conditioned_fines_distribution']
    assert len(eds['required_information']) == 2
    for mid in eds['marker_pool']:
        assert eds['id'] in M[mid]['required_capabilities']
        assert M[mid]['observability']['cls'] == 'requires_new_observability'


def test_roadmap_references_resolve_to_opportunities(seed):
    doc = frontier.build(*seed)
    M, C = by_id(doc, 'markers'), by_id(doc, 'capabilities')
    steps = doc['opportunity_map']['roadmap']
    assert [s['label'] for s in steps] == ['TEST CURRENT DATA', 'TARGETED CAPTURE', 'EXPAND OBSERVABILITY', 'RE-OBSERVE']
    assert all(mid in M for s in steps for mid in s.get('marker_refs', []))
    assert all(cid in C for s in steps for cid in s.get('capability_refs', []))


# ---------------------------------------------------------------- fixture isolation
def test_fixture_evidence_never_advances_a_gate(seed, example):
    a, b = frontier.build(*seed), frontier.build(*example)
    for coll in ('markers', 'capabilities'):
        A, B = by_id(a, coll), by_id(b, coll)
        for cid, case in A.items():
            assert {g: v['state'] for g, v in B[cid]['gates'].items()} == {g: v['state'] for g, v in case['gates'].items()}, cid
            assert B[cid]['status'] == case['status']
    eds = by_id(b, 'capabilities')['capability:eds']
    assert eds['counts']['fixture_papers'] == 2 and eds['counts']['supporting'] == 0
    assert eds['marker_demands'] == ['marker:high_z_composition', 'marker:phase_conditioned_fines_distribution']
    assert 'marker:fines_contaminant_screen' in eds['markers_unlocked']
    assert 'marker:fines_contaminant_screen' not in eds['marker_demands']      # the fixture marker is not demand
    assert set(eds['gates']['literature_convergence']['excluded_fixture']) == {'paper:fixture-eds-mapping', 'paper:fixture-eds-resolution'}


def test_fixture_bundle_cannot_extend_a_real_case(seed):
    fields, bundles = seed
    b = bundle('fixture', capabilities=[dict(id='capability:eds', name='EDS', capability_type='spectroscopy', provenance=dict(kind='fixture'),
                                             existing_capability_substitutes=[dict(id='x', label='x', ruled_out=True, basis=[REF])])])
    doc = frontier.build(fields, bundles + [b])
    assert doc['governance']['conflicts'][0]['reason'] == 'a fixture bundle may not extend a non-fixture case'
    assert len(by_id(doc, 'capabilities')['capability:eds']['existing_capability_substitutes']) == 2


# ---------------------------------------------------------------- contradictory evidence
def test_contradictory_papers_are_represented(example):
    doc = frontier.build(*example)
    eds = by_id(doc, 'capabilities')['capability:eds']
    assert [e['id'] for e in eds['contradictory_evidence']] == ['paper:fixture-eds-resolution']
    assert by_id(doc, 'papers')['paper:fixture-eds-resolution']['assessments'][0]['label'] == 'CONTRADICTORY'


def test_counted_contradiction_contests_the_gate(seed):
    fields, bundles = seed
    t = 'marker:fines_subfloor_size'
    sup = [paper('paper:s1', 'g1', t, 'scientific_relevance'), paper('paper:s2', 'g2', t, 'scientific_relevance', method='moderate')]
    doc = frontier.build(fields, bundles + [bundle(papers=sup)])
    assert by_id(doc, 'markers')[t]['gates']['scientific_relevance']['state'] == 'met'
    con = paper('paper:c1', 'g3', t, 'scientific_relevance', direction='CONTRADICTORY')
    doc = frontier.build(fields, bundles + [bundle(papers=sup + [con])])
    m = by_id(doc, 'markers')[t]
    assert m['gates']['scientific_relevance']['state'] == 'contested'
    assert m['counts']['contradictory'] == 1 and m['contradictory_evidence'][0]['id'] == 'paper:c1'
    assert frontier.check(doc) == []


def test_one_source_or_one_group_is_not_replication(seed):
    fields, bundles = seed
    t = 'marker:fines_subfloor_size'
    same_group = [paper('paper:r1', 'lab', t, 'scientific_relevance'), paper('paper:r2', 'lab', t, 'scientific_relevance')]
    m = by_id(frontier.build(fields, bundles + [bundle(papers=same_group)]), 'markers')[t]
    assert m['gates']['scientific_relevance']['state'] == 'partial'


# ---------------------------------------------------------------- admission and critical mass governance
def test_admission_needs_every_gate_and_a_review(seed):
    fields, bundles = seed
    doc = frontier.build(fields, bundles + [admissible_marker_bundle()])
    m = by_id(doc, 'markers')['marker:test_admit']
    assert m['status'] == 'ADMITTED' and frontier.check(doc) == []
    m = by_id(frontier.build(fields, bundles + [admissible_marker_bundle(review=False)]), 'markers')['marker:test_admit']
    assert m['status'] == 'TRACKABLE' and m['gates']['admission']['state'] == 'partial'
    doc = frontier.build(fields, bundles + [admissible_marker_bundle(measurable=False)])
    m = by_id(doc, 'markers')['marker:test_admit']
    assert m['status'] == 'SUPPORTED'                          # a review cannot lift a case whose gates are not met
    assert doc['governance']['ignored'][0]['target'] == 'marker:test_admit'


def test_admitted_without_measurability_or_robustness_is_a_violation(seed):
    fields, bundles = seed
    doc = frontier.build(*seed)
    tampered = copy.deepcopy(doc)
    m = by_id(tampered, 'markers')['marker:fines_subfloor_size']
    m['status'] = 'ADMITTED'
    v = frontier.check(tampered)
    assert any('ADMITTED without' in x for x in v) and any('does not follow from its gates' in x for x in v)
    assert any('differs from what the rules derive' in x for x in frontier.check(tampered, fields, bundles))


def test_critical_mass_needs_convergent_demand_and_a_consequential_blindspot(seed):
    fields, bundles = seed
    doc = frontier.build(fields, bundles + [critical_mass_bundle()])
    c = by_id(doc, 'capabilities')['capability:test_cap']
    assert c['status'] == 'CRITICAL_MASS' and len(c['credible_demands']) == 2 and frontier.check(doc) == []
    c = by_id(frontier.build(fields, bundles + [critical_mass_bundle(review=True)]), 'capabilities')['capability:test_cap']
    assert c['status'] == 'RECOMMENDED'
    c = by_id(frontier.build(fields, bundles + [critical_mass_bundle(demands=1)]), 'capabilities')['capability:test_cap']
    assert c['status'] == 'BUILDING_CASE'                      # one consequential need: a case, not critical mass
    tampered = copy.deepcopy(frontier.build(*seed))
    by_id(tampered, 'capabilities')['capability:tomography_3d']['status'] = 'CRITICAL_MASS'
    assert any('CRITICAL_MASS without' in x for x in frontier.check(tampered))


def test_no_opaque_overall_score(seed):
    doc = frontier.build(*seed)
    assert frontier.check(doc) == []
    tampered = copy.deepcopy(doc)
    tampered['markers'][0]['evidence_confidence'] = 0.87
    assert any('opaque score-like key' in v for v in frontier.check(tampered))


# ---------------------------------------------------------------- before any research
def test_frontier_without_any_research(seed):
    fields, _ = seed
    doc = frontier.build(fields, [])
    assert frontier.check(doc, fields, []) == []
    assert doc['markers'] == [] and doc['capabilities'] == [] and doc['lanes'] == dict(current_capture=[], new_capability=[])
    assert doc['opportunity_map']['roadmap'] == []
    assert set(doc['open_blindspots']) == {b['key'] for b in doc['blindspots'] if b['consequential']}


def test_inject_adds_an_escaped_payload_tag(seed):
    doc = frontier.build(*seed)
    doc['markers'][0]['proposition'] = 'contains </script> safely'
    html = frontier.inject('<html><body><div id="root"></div></body></html>', doc)
    assert html.count('id="frontier-payload"') == 1 and '</script> safely' not in html and html.endswith('</body></html>')
