"""Governed decision brief (decision-brief/1): coherence with epistemic-field/1, determinism, governance, and the exact
human-facing states for the assessed batches. Runs on the committed fixtures (no engine cache needed)."""
import copy
import json
import os

import pytest

from qc import brief

ROOT = os.path.dirname(os.path.dirname(__file__))


def field(b):
    return json.load(open(os.path.join(ROOT, 'fixtures', f'epistemic_field.{b}.json'), encoding='utf-8'))


@pytest.fixture(params=['Batch_2', 'Batch_3', 'Hackathon-Polaron-test'])
def fb(request):
    F = field(request.param)
    return F, brief.build(F)


def claims(B):
    return {c['id']: c for c in B['claims']}


def test_brief_is_coherent_with_its_field(fb):
    F, B = fb
    assert brief.check(B, F) == []


def test_brief_is_deterministic(fb):
    F, B = fb
    assert json.dumps(brief.build(copy.deepcopy(F)), sort_keys=True) == json.dumps(B, sort_keys=True)


def test_committed_fixture_brief_matches_a_fresh_build(fb):
    F, B = fb
    committed = json.load(open(os.path.join(ROOT, 'fixtures', f"decision_brief.{F['context']['batch']}.json"), encoding='utf-8'))
    assert committed == json.loads(json.dumps(B))


def test_no_orphan_or_unreferenced_hero_claims(fb):
    F, B = fb
    C = claims(B)
    for h in B['hero'].values():
        assert h['claims']
        for cid in h['claims']:
            assert cid in C and C[cid]['proof_refs']


def test_selected_content_groups_are_unique_and_pointers_carry_no_numbers(fb):
    F, B = fb
    C = claims(B)
    selected = [C[i] for h in B['hero'].values() for i in h['claims']]
    groups = [c['group'] for c in selected if c['role'] == 'content']
    assert len(groups) == len(set(groups))
    for c in selected:
        if c['role'] == 'pointer':
            assert not any(ch.isdigit() for ch in c['text'])
            assert all(p in C for p in c.get('points_to', []))


def test_every_number_comes_from_the_field(fb):
    F, B = fb
    for c in B['claims']:
        for v in c['values'] + c['fact_values'] + [x for d in c['details'] for x in d['values']]:
            assert brief.resolve(F, v['ref']) == v['value']


@pytest.mark.parametrize('mutate, expect', [
    (lambda B: B['claims'][0]['proof_refs'].append({'collection': 'observations', 'id': 'M9999:nothing', 'path': None}), 'unresolved ref'),
    (lambda B: B['claims'][0].__setitem__('proof_refs', []), 'no proof_refs'),
    (lambda B: B['claims'][0]['fact_values'][0].__setitem__('value', 0.001), 'value differs'),
    (lambda B: B['claims'][0].__setitem__('fact', 'batch p = 0.001 against α = 0.05'), 'not the rendering'),
    (lambda B: B['claims'][0].__setitem__('template', '{0} crosses the rule in 9 of 10 cases.'), 'number written'),
    (lambda B: B['hero']['limits']['claims'].append('limit.nothing'), 'orphan claim'),
    (lambda B: B['hero']['limits']['claims'].append('decision.verdict'), 'selected twice'),
    (lambda B: B['hero']['decision'].__setitem__('state', 'ACCEPT' if B['hero']['decision']['state'] != 'ACCEPT' else 'REJECT'), 'differs from the field verdict'),
])
def test_check_catches_violations(mutate, expect):
    F = field('Batch_3')
    B = brief.build(F)
    mutate(B)
    assert any(expect in v for v in brief.check(B, F)), brief.check(B, F)


def test_overstating_language_is_rejected():
    F = field('Batch_3')
    B = brief.build(F)
    c = claims(B)['decision.verdict']
    c['template'] = '{0} is proven defective.'
    c['text'] = c['template'].format(F['context']['batch'])
    assert any('overstating' in v for v in brief.check(B, F))
    assert not any('overstating' in v for v in brief.check(brief.build(F), F))     # "approved" is not "prove"


def test_batch3_hero_states():
    F = field('Batch_3')
    B = brief.build(F)
    H, C = B['hero'], claims(B)
    assert H['decision']['state'] == 'REJECT' == F['decision']['verdict']
    assert C['support.qc']['status'] == 'sufficient'
    assert C['support.attribution']['status'] == 'change_modality'
    assert C['support.prevalence']['status'] == 'expansion_needed'
    assert H['data_support']['state'] == 'SUFFICIENT FOR QC' and 'NOT FOR ATTRIBUTION' in H['data_support']['qualifier']
    assert H['surviving_evidence']['state'] == 'M2060 · ADDITIVE DENSITY'
    ev = C['evidence.M2060:additive_density']
    assert ev['status'] == 'survives' and 'without M2060: ACCEPT' in ev['fact']
    assert [C[i]['label'] for i in H['limits']['claims']] == ['SCALE', 'COMPOSITION', 'PREVALENCE']
    assert H['acquisition_policy']['mode'] == 'verify_first' and H['acquisition_policy']['sequence'].startswith('Repeat M2060')
    assert C[H['acquisition_policy']['claims'][0]]['action_refs'] == ['repeat:1']
    # merged, not repeated: the scrutiny / leverage facts of M2060 appear once, inside the evidence claim
    merged = [s for s in B['governance']['suppressed'] if s['reason'] == 'merged']
    assert {s['into'] for s in merged} == {
        'evidence.M2060:additive_density', 'evidence.M2068:additive_d50_um'
    } and len(merged) == 8


def test_batch2_hero_states_after_independence_correction():
    F = field('Batch_2')
    B = brief.build(F)
    H, C = B['hero'], claims(B)
    assert H['decision']['state'] == 'ACCEPT'
    assert F['decision']['n_independent'] == 3 and len(F['decision']['reference_linked']) == 3
    assert C['support.qc']['status'] == 'at_minimum' and 'INVESTIGATE' in C['support.qc']['text']
    assert C['support.attribution']['status'] == 'not_applicable'
    assert H['surviving_evidence']['claims'] == ['evidence.none']
    assert [C[i]['label'] for i in H['limits']['claims']] == ['PREVALENCE']
    assert H['acquisition_policy']['mode'] == 'expand_sampling'
    assert C[H['acquisition_policy']['claims'][0]]['label'] == 'SECTIONS'


def test_stop_is_recommended_when_nothing_justifies_more_acquisition():
    F = field('Batch_2')
    F['actions'] = []
    for r in F['rims']:
        r['consequential'] = False
    F['summary']['consequential_rims'] = []
    B = brief.build(F)
    assert B['hero']['acquisition_policy']['mode'] == 'stop'
    stop = claims(B)['action.stop']
    assert stop['status'] == 'no_expansion_justified' and 'of this kind' in stop['text']
    assert claims(B)['support.prevalence']['status'] == 'sufficient'


def test_two_parent_batch_exposes_population_limit_and_resolving_capture():
    F = field('Hackathon-Polaron-test')
    B = brief.build(F)
    H, C = B['hero'], claims(B)
    assert F['decision']['verdict'] == 'INVESTIGATE' and F['decision']['n_independent'] == 2
    assert [C[i]['label'] for i in H['limits']['claims']] == ['PREVALENCE']
    assert H['acquisition_policy']['mode'] == 'expand_sampling'
    assert C[H['acquisition_policy']['claims'][0]]['label'] == 'SECTIONS'
    assert brief.check(B, F) == []


def test_compose_seam_cannot_change_states():
    F = field('Batch_3')
    B = brief.build(F)
    def bad_compositor(b):
        c = next(x for x in b['claims'] if x['id'] == 'decision.verdict')
        c['status'] = 'ACCEPT'
        return b
    assert any('verdict' in v for v in brief.check(brief.compose(B, bad_compositor), F))
    assert brief.compose(B) is B
