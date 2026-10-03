"""Representation contract epistemic-field/1: schema, coherence, determinism, renderer independence."""
import glob
import json
import os

import jsonschema
import pytest

from qc import contract, hero

ROOT = os.path.dirname(os.path.dirname(__file__))
FIXTURE = os.path.join(ROOT, 'fixtures', 'epistemic_field.Batch_3.json')


@pytest.fixture(scope='module')
def fixture():
    return json.load(open(FIXTURE, encoding='utf-8'))


@pytest.fixture(scope='module')
def schema():
    return json.load(open(contract.SCHEMA_PATH, encoding='utf-8'))


def live(b):
    p = os.path.join(ROOT, 'reports', b, 'field.json')
    if not os.path.exists(p):
        pytest.skip('run python -m qc assess first')
    return json.load(open(p, encoding='utf-8'))


def test_fixture_validates_against_schema(fixture, schema):
    jsonschema.validate(fixture, schema)


@pytest.mark.parametrize('b', ['Batch_2', 'Batch_3'])
def test_live_fields_validate_and_are_coherent(b, schema):
    f = live(b)
    jsonschema.validate(f, schema)
    assert contract.check(f) == []


def test_fixture_is_internally_coherent(fixture):
    assert contract.check(fixture) == []


def test_fixture_assets_exist(fixture):
    for fid, a in fixture['assets'].items():
        assert os.path.exists(os.path.join(ROOT, 'fixtures', a['image'])), fid
    assert set(fixture['assets']) == {f['id'] for f in fixture['provenance']['fields']}


def test_fixture_is_reproducible_from_the_engine(fixture):
    """Rebuilding the field from cached engine outputs gives the fixture (deterministic, seeded simulations)."""
    from qc import field
    res = json.load(open(os.path.join(ROOT, 'reports', 'Batch_3', 'result.json'), encoding='utf-8'))
    ref = json.load(open(os.path.join(ROOT, 'cache', 'reference.json'), encoding='utf-8'))
    allr = [json.load(open(p, encoding='utf-8')) for p in glob.glob(os.path.join(ROOT, 'cache', 'fields', '*.json'))]
    recs = [r for r in allr if r['batch'] == 'Batch_3']
    rebuilt = contract.normalise(field.build({k: v for k, v in res.items() if k != 'field'}, ref, recs, res['chains'], allr))
    rebuilt = json.loads(json.dumps(rebuilt))
    expected = {k: v for k, v in fixture.items() if k != 'assets'}
    assert rebuilt == expected


def test_detects_incoherence(fixture):
    """The checker is not vacuous: corrupt a few invariants and expect violations."""
    bad = json.loads(json.dumps(fixture))
    o = next(o for o in bad['observations'] if o['scrutiny']['outcome'] == 'survives')
    o['scrutiny']['tile_consistent'] = False
    bad['actions'][0]['triggered_by'].append('spatial:NOPE:x')
    bad['observations'][0]['variance_shares']['spatial_sampling'] += 0.2
    bad['dimensions'][0]['ring_width'] = 3
    v = contract.check(bad)
    assert any('survives but' in x for x in v) and any('trigger rim' in x for x in v)
    assert any('variance shares' in x for x in v) and any('presentation vocabulary' in x for x in v)


def test_v1_renderer_consumes_only_the_contract(fixture):
    src = open(hero.__file__, encoding='utf-8').read()
    assert 'from .' not in src and 'import qc' not in src            # no scientific engine import
    for old in ('F.cells', 'F.rows', '.dominant', 'acq_sensitive', 'reducible_share'):
        assert old not in hero.TEMPLATE                                # pre-contract structure gone
    html = hero.render(fixture, asset_dir=os.path.join(ROOT, 'fixtures', 'assets'))
    assert '"schema_version": "epistemic-field/1"' in html and html.count('data:image/jpeg;base64') == len(fixture['assets'])


def test_no_invented_geometry(fixture):
    for p in fixture['spatial_profiles']:
        assert p['run_separation'] == 'unknown'
        for run in p['runs']:
            assert run['fields'][0]['x0_um'] == 0                      # each run has its own frame
            assert abs(sum(f['width_um'] for f in run['fields']) - run['length_um']) < 1e-5 * run['length_um']
