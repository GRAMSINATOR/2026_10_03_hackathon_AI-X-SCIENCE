"""Instrument renderer host: injects exactly the contract + registered assets; no scientific logic."""
import json
import os
import re

import pytest

from qc import instrument

ROOT = os.path.dirname(os.path.dirname(__file__))


@pytest.fixture(scope='module')
def built():
    if not os.path.exists(instrument.DIST):
        pytest.skip('renderer not built (cd renderer && npm run build)')
    f = json.load(open(os.path.join(ROOT, 'fixtures', 'epistemic_field.Batch_3.json'), encoding='utf-8'))
    return f, instrument.render(f, asset_dir=os.path.join(ROOT, 'fixtures', 'assets'))


def payload(html):
    m = re.search(r'<script id="evidence-payload" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1).replace('<\\/', '</'))


def test_payload_is_the_contract_verbatim(built):
    f, html = built
    assert instrument.PLACEHOLDER not in html
    p = payload(html)
    assert p['field'] == json.loads(json.dumps(f))
    assert set(p) == {'field', 'assets', 'imagery', 'brief'} and p['imagery'] is True


def test_assets_are_registered_to_provenance_fields(built):
    f, html = built
    a = payload(html)['assets']
    fields = {x['id']: x for x in f['provenance']['fields']}
    assert set(a) <= set(fields)
    for fid, x in a.items():
        assert x['bse'].startswith('data:image/jpeg;base64,')
        assert x['seg'].startswith('data:image/png;base64,') and x['seg_encoding'] == {'0': 'pore', '1': 'matrix', '2': 'high_z'}
        assert x['width_um'] == fields[fid]['width_um'] and x['height_um'] == fields[fid]['height_um']


def test_rejects_other_contracts(built):
    f, _ = built
    with pytest.raises(ValueError):
        instrument.render(dict(f, schema_version='x'))


def test_host_contains_no_scientific_logic():
    src = open(instrument.__file__, encoding='utf-8').read()
    assert 'from .' not in src and 'qc.' not in src.replace('qc/instrument.py', '')
