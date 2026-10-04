import copy
import json
from pathlib import Path

import pytest

from qc import contract, reference_frames, reference_sensitivity


ROOT = Path(__file__).parents[1]


def fixture(batch):
    return json.loads((ROOT / 'fixtures' / f'epistemic_field.{batch}.json').read_text(encoding='utf-8'))


def test_active_reference_and_support_registry_are_serialized():
    field = fixture('Hackathon-Polaron-test')
    assert field['context']['reference_frame']['id'] == 'Batch_1'
    assert field['context']['reference_frame']['selection'] == 'explicit'
    assert field['context']['reference_frame']['externally_approved'] is False
    rows = {x['id']: x for x in field['reference_frames']}
    assert {x for x, row in rows.items() if row['eligible']} == {'Batch_1', 'Batch_2', 'Batch_3'}
    assert rows['Hackathon-Polaron-test']['eligible'] is False
    assert any('at least 4' in reason for reason in rows['Hackathon-Polaron-test']['unavailable_reasons'])


def test_cross_reference_comparison_is_complete_and_keeps_source_measurements():
    field = fixture('Batch_3')
    sensitivity = field['reference_sensitivity']
    assert sensitivity['complete'] is True
    assert set(sensitivity['frames_evaluated']) == {'Batch_1', 'Batch_2', 'Batch_3'}
    assert sensitivity['intrinsic_unchanged'] is True
    assert len(set(sensitivity['measurement_digest_by_frame'].values())) == 1
    assert sensitivity['frame_dependent_findings']
    assert sensitivity['invariant_findings']
    assert sensitivity['mode'] == 'comparative_exploration_not_classification'
    assert contract.check(field) == []


def test_self_reference_uses_parent_leave_one_out_frames():
    field = fixture('Batch_1')
    assert field['context']['role'] == 'reference'
    assert field['decision']['verdict'] == 'REFERENCE'
    measurable = [o for o in field['observations'] if o['reference_relation']['status'] != 'not_measurable']
    assert measurable
    assert all(o['reference_relation']['frame'] == 'leave_one_out' for o in measurable)
    assert all(o['reference_relation']['frame_n'] < field['decision']['self_audit']['n_parents'] for o in measurable)
    assert field['decision']['n_entities'] == len(field['entities'])


def test_sensitivity_classification_uses_all_frames_and_only_relative_values_change():
    base = fixture('Batch_2')
    fields = [copy.deepcopy(base) for _ in range(3)]
    names = ['A', 'B', 'C']
    index = {'frames': [dict(id=n, eligible=True, support={'n_parent_micrographs': 6}) for n in names]}
    oid = fields[0]['observations'][0]['id']
    stable_oid = fields[0]['observations'][1]['id']
    for name, field in zip(names, fields):
        field['context']['reference'] = name
        field['context']['reference_frame']['id'] = name
    for state, field in zip(('out', 'in', 'in'), fields):
        next(o for o in field['observations'] if o['id'] == oid)['reference_relation']['status'] = state
    result = reference_sensitivity.build(fields, index)
    assert result['intrinsic_unchanged'] is True
    assert next(x for x in result['findings'] if x['id'] == oid)['classification'] == 'reference_sensitive'
    assert next(x for x in result['findings'] if x['id'] == stable_oid)['classification'] == 'reference_invariant'
    incomplete = reference_sensitivity.build(fields[:2], index)
    assert incomplete['complete'] is False
    assert all(x['classification'] == 'reference_sensitive' for x in incomplete['findings'])
    fields[2]['observations'][0]['value'] += 1
    assert reference_sensitivity.build(fields, index)['intrinsic_unchanged'] is False


def test_under_supported_reference_is_rejected():
    weak = {'name': 'weak', 'eligibility': {'eligible': False,
            'unavailable_reasons': ['2 independent parent micrographs; at least 4 are required']}}
    path = ROOT / 'work' / '_weak_reference_test.json'
    path.parent.mkdir(exist_ok=True)
    try:
        path.write_text(json.dumps(weak), encoding='utf-8')
        with pytest.raises(ValueError, match='at least 4'):
            reference_frames.resolve(str(path))
    finally:
        path.unlink(missing_ok=True)
