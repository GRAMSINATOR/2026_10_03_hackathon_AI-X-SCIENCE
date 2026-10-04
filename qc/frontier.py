"""Marker Frontier (marker-frontier/1): expanding what the controller can know, above epistemic-field/1.

    epistemic-field/1 (blindspots: rims, missing dimensions)  +  research bundles (marker-research/1, the qte77 socket)
        -> merge, resolve, derive gates and states (this module)  ->  marker-frontier/1  ->  renderer

Two accumulation objects:
  * Marker Case: can a scientifically useful new marker be tracked with acquisition data we can already collect?
  * Capability Case: do independently supported marker demands converge on a new measurement capability strongly
    enough, on consequential enough blindspots, that adding it to the workflow is justified?

Governance (there is no overall score anywhere):
  * research bundles never assert a state. They supply evidence (paper assessments, project records, engine facts,
    reviews). Each gate is a categorical function of that evidence, and each state is a function of the gates;
  * evidence from a FIXTURE bundle is shown but never advances a gate, demand or count that drives a state;
  * every blindspot link resolves against a loaded epistemic field, or is explicitly `general` (a vocabulary gap);
  * ADMITTED and RECOMMENDED also need a non-fixture review: evidence makes a case eligible, a person selects it
    (GRAMSINATOR decides what crosses into the product, docs/JOB_SPLIT_V2.MD §1);
  * contradictory evidence is kept beside the case and can contest a gate; it is never dropped.
See docs/MARKER_FRONTIER.md.
"""
import argparse
import copy
import glob
import json
import os
import re

from .brief import resolve as resolve_ref   # the {collection, id, path} resolver shared with decision-brief/1

SCHEMA_VERSION = 'marker-frontier/1'
INPUT_VERSION = 'marker-research/1'
ROOT = os.path.dirname(os.path.dirname(__file__))
RESEARCH_DIR = os.environ.get('QC_RESEARCH', os.path.join(ROOT, 'research'))
SCHEMA_PATH = os.path.join(ROOT, 'schema', 'marker_research.v1.schema.json')
BUNDLE_KINDS = ('controller_seed', 'research_agent', 'fixture')

MARKER_STATES = ['ADMITTED', 'TRACKABLE', 'SUPPORTED', 'BUILDING', 'CANDIDATE', 'UNAVAILABLE', 'CONFOUNDED', 'REJECTED']
CAPABILITY_STATES = ['INTEGRATED', 'RECOMMENDED', 'CRITICAL_MASS', 'BUILDING_CASE', 'WATCHING', 'REJECTED']
TERMINAL = {'REJECTED', 'CONFOUNDED'}
GATE_STATES = ('met', 'partial', 'contested', 'failed', 'open')
MARKER_RAIL = [('scientific_relevance', 'SCIENTIFIC BASIS'), ('measurability', 'TESTABLE WITH CURRENT CAPTURE'),
               ('robustness', 'ROBUSTNESS / CONFOUND CONTROL'), ('blindspot_closure', 'INQUIRY VALUE'), ('admission', 'PROMOTION REVIEW')]
CAPABILITY_RAIL = [('marker_demand', 'MARKER POOL'), ('literature_convergence', 'LITERATURE BASIS'),
                   ('consequential_closure', 'INQUIRY VALUE'), ('non_substitutability', 'NO ADEQUATE SUBSTITUTE'),
                   ('integration_case', 'LAB FIT')]
MARKER_GATES = [g for g, _ in MARKER_RAIL[:4]] + ['non_redundancy', 'admission']
EVIDENCE_GATES = ('scientific_relevance', 'measurability', 'robustness', 'non_redundancy')   # gates fed by evidence, not by links
ADMISSION_GATES = ('scientific_relevance', 'measurability', 'robustness', 'blindspot_closure', 'non_redundancy')

# paper assessment: direction-free strength from method strength x relevance (directness x transferability); see docs
TRANSFER_AXES = ('material', 'modality', 'scale', 'task', 'process')
STRENGTH = {'strong': {'R1': 'STRONG DIRECT', 'R2': 'STRONG TRANSFERABLE', 'R3': 'SUPPORTING', 'R4': 'INDIRECT'},
            'moderate': {'R1': 'SUPPORTING', 'R2': 'SUPPORTING', 'R3': 'SUPPORTING', 'R4': 'INDIRECT'},
            'weak': {'R1': 'WEAK', 'R2': 'WEAK', 'R3': 'WEAK', 'R4': 'WEAK'}}
RANK = {'STRONG DIRECT': 4, 'STRONG TRANSFERABLE': 3, 'SUPPORTING': 2, 'INDIRECT': 1, 'WEAK': 0}
TYPE_LABEL = {'scale': 'SCALE', 'composition': 'COMPOSITION', 'spatial': 'EXTENT', 'population': 'PREVALENCE',
              'acquisition': 'ACQUISITION', 'validity': 'VALIDITY'}
VORTEX_KIND = {'scale': 'resolution_limit', 'composition': 'identity_uncertainty', 'spatial': 'unresolved_spatial_structure',
               'population': 'sampling_uncertainty', 'acquisition': 'acquisition_sensitivity', 'validity': 'measurement_validity'}
FAMILY_REPRESENTATION = {'scalar': 'scalar', 'distribution': 'distribution', 'spatial_pattern': 'spatial_field',
                         'morphology': 'morphological_class', 'cross_modality': 'cross_marker_relation',
                         'acquisition_signature': 'categorical_state', 'spatial_statistic': 'scalar',
                         'composition': 'categorical_state', 'process_variation': 'multiscale_signature', 'other': 'other'}
QUALITATIVE_REPRESENTATIONS = {'morphological_class', 'categorical_state'}
OBSERVABILITY_LABEL = {'computable_now': 'COMPUTABLE / TESTABLE NOW', 'needs_targeted_capture': 'NEEDS TARGETED CAPTURE',
                       'requires_new_observability': 'REQUIRES NEW OBSERVABILITY'}
INVESTIGATION_STATE = {'ADMITTED': 'PROMOTED', 'TRACKABLE': 'TESTABLE', 'SUPPORTED': 'PROMISING',
                       'BUILDING': 'INVESTIGATING', 'CANDIDATE': 'CANDIDATE', 'UNAVAILABLE': 'OBSERVABILITY GAP',
                       'CONFOUNDED': 'DEPRIORITIZED', 'REJECTED': 'DEPRIORITIZED'}
ATTRACTOR_STATE = {'INTEGRATED': 'INTEGRATED', 'RECOMMENDED': 'READY FOR REVIEW', 'CRITICAL_MASS': 'STRONG PAYLOAD',
                   'BUILDING_CASE': 'BUILDING PAYLOAD', 'WATCHING': 'EARLY SIGNAL', 'REJECTED': 'SET ASIDE'}
OPAQUE_KEYS = re.compile(r'(score|confidence|probability|likelihood|credence)', re.I)

STATUS_BASIS = {
    'ADMITTED': 'every evidence gate met (relevance, measurability, robustness, blindspot value, non-redundancy) and a recorded admission review',
    'TRACKABLE': 'scientific relevance and measurability with current capture are both met',
    'SUPPORTED': 'scientific relevance met (replicated, uncontested literature); measurability not yet met',
    'BUILDING': 'some evidence gate is partly supported; scientific relevance not met',
    'CANDIDATE': 'proposed; no evidence gate supported yet (links to blindspots are relationships, not evidence)',
    'UNAVAILABLE': 'current capture cannot observe it; it counts as demand on the capability it names',
    'CONFOUNDED': 'a tested confound explains the signal under current capture',
    'REJECTED': 'tested without decision value, fully redundant, or rejected by a recorded review',
    'INTEGRATED': 'the capability is part of the workflow (recorded review)',
    'RECOMMENDED': 'critical mass and an accepted integration case with a recorded review',
    'CRITICAL_MASS': 'convergent credible marker demand, uncontested literature convergence, a consequential blindspot and no adequate substitute',
    'BUILDING_CASE': 'multiple credible marker needs, or one need that closes a consequential blindspot',
    'WATCHING': 'one or weak marker need and no consequential blindspot',
}
MISSING = {
    'scientific_relevance': {'open': 'no counted literature yet: needs one strong source (direct or transferable) plus an independent supporting source',
                             'partial': 'needs replication: one strong source and a second independent supporting source',
                             'contested': 'contradictory evidence at least as strong as the best support must be answered first'},
    'measurability': {'open': 'state whether current capture can observe it, then run the current-data test',
                      'partial': 'run the current-data test on existing micrographs (or acquire as stated) and record the result',
                      'failed': 'current capture cannot observe it: demand routes to the capability it names'},
    'robustness': {'open': 'run the acquisition-perturbation suite and control each listed confound',
                   'partial': 'every listed confound needs a control backed by evidence, and the perturbation test must pass',
                   'contested': 'published confound evidence must be answered by a passing robustness test',
                   'failed': 'a tested confound explains the signal'},
    'blindspot_closure': {'open': 'link it to a current blindspot or decision',
                          'partial': 'closes no consequential blindspot in the loaded fields',
                          'failed': 'tested: no decision value'},
    'non_redundancy': {'open': 'show it adds information beyond the tracked dimensions (a recorded test)',
                       'partial': 'overlap with tracked dimensions is stated but untested',
                       'failed': 'tested: redundant with a tracked dimension'},
    'admission': {'open': 'every evidence gate must be met first', 'partial': 'all evidence gates met: awaiting a recorded admission review'},
    'marker_demand': {'open': 'no marker case needs this capability yet',
                      'partial': 'needs a second independently credible marker demand (scientific relevance met)'},
    'literature_convergence': {'open': 'no counted literature yet: research case open',
                               'partial': 'needs one strong source and a second independent supporting source',
                               'contested': 'contradictory evidence at least as strong as the best support must be answered first'},
    'consequential_closure': {'open': 'link it to a current blindspot', 'partial': 'closes no consequential blindspot in the loaded fields'},
    'non_substitutability': {'open': 'list the existing capabilities that might substitute and rule each in or out with evidence',
                             'partial': 'some substitutes are not yet ruled out with evidence',
                             'failed': 'an existing capability substitutes: the expansion is not justified'},
    'integration_case': {'open': 'state integration requirements, burden and cost class',
                         'partial': 'integration case drafted: needs acceptance in a recorded review'},
}
GOVERNANCE_RULES = [
    'a state is a function of categorical gates; a gate is a function of structured evidence; research prose never sets either',
    'evidence from fixture bundles is displayed but never advances a gate, a demand or a state-driving count',
    'scientific relevance / literature convergence: met = one strong source (STRONG DIRECT or STRONG TRANSFERABLE) and two '
    'independent supporting sources, uncontested; contested = a contradictory source at least as strong as the best support',
    'a counted project record that fails a proposition contests scientific relevance; a failed robustness record makes a marker CONFOUNDED',
    'a blindspot link is a relationship, not evidence: alone it leaves a marker CANDIDATE',
    'a marker that measures a dimension the field records as not acquired is non-redundant by construction',
    'capability demand counts only active, non-fixture marker cases; a credible demand has scientific relevance met',
    'ADMITTED and RECOMMENDED additionally require a non-fixture review; a review cannot lift a case whose gates are not met',
    'contradictory evidence is listed with the case it bears on and is never dropped',
]


# ---------------------------------------------------------------- loading and merging
def load_bundles(where=None):
    """Research bundles from a directory (sorted by file name) or an explicit list of paths."""
    where = RESEARCH_DIR if where is None else where
    paths = sorted(glob.glob(os.path.join(where, '*.json'))) if isinstance(where, str) else list(where)
    return [json.load(open(p, encoding='utf-8')) for p in paths]


def _fx(meta, item):
    return meta['kind'] == 'fixture' or (item.get('provenance') or {}).get('kind') == 'fixture'


LIST_KEYS = {'markers': ('blindspot_refs', 'decision_refs', 'known_confounds', 'known_failure_modes', 'redundant_with',
                         'required_capabilities', 'required_modalities'),
             'capabilities': ('blindspot_refs', 'decision_refs', 'existing_capability_substitutes')}
BIB_KEYS = ('title', 'year', 'venue', 'doi', 'url')


def merge(bundles):
    """One input set from many bundles. A later bundle may extend an earlier case (lists are extended, unset scalars
    filled); conflicting scalars are recorded, never overwritten. A fixture bundle may not extend a non-fixture case."""
    I = dict(markers={}, capabilities={}, papers={}, records={}, reviews=[], bundles=[])
    conflicts = []
    for b in bundles:
        if b.get('schema_version') != INPUT_VERSION:
            raise ValueError(f"research bundle {b.get('bundle', {}).get('id')} is not {INPUT_VERSION}")
        meta = b['bundle']
        if meta['kind'] not in BUNDLE_KINDS:
            raise ValueError(f"bundle {meta['id']}: unknown kind {meta['kind']}")
        I['bundles'].append(dict(id=meta['id'], kind=meta['kind'], produced_by=meta.get('produced_by'), produced_at=meta.get('produced_at'),
                                 notes=meta.get('notes'), n=dict((k, len(b.get(k, []))) for k in ('markers', 'capabilities', 'papers', 'records', 'reviews'))))
        for coll in ('markers', 'capabilities'):
            for x in b.get(coll, []):
                x = dict(copy.deepcopy(x), bundle=meta['id'], fixture=_fx(meta, x))
                cur = I[coll].get(x['id'])
                if cur is None:
                    I[coll][x['id']] = x
                    continue
                if x['fixture'] and not cur['fixture']:
                    conflicts.append(dict(collection=coll, id=x['id'], key='*', kept=cur['bundle'], ignored=meta['id'],
                                          reason='a fixture bundle may not extend a non-fixture case'))
                    continue
                for k, v in x.items():
                    if k in ('id', 'bundle', 'fixture', 'provenance', 'extended_by'):
                        continue
                    if k in LIST_KEYS[coll]:
                        cur[k] = cur.get(k, []) + [i for i in v if i not in cur.get(k, [])]
                    elif cur.get(k) is None:
                        cur[k] = v
                    elif cur[k] != v:
                        conflicts.append(dict(collection=coll, id=x['id'], key=k, kept=cur['bundle'], ignored=meta['id'], reason='conflicting value'))
                cur['extended_by'] = cur.get('extended_by', []) + [meta['id']]
        for coll in ('papers', 'records'):
            for x in b.get(coll, []):
                x = dict(copy.deepcopy(x), bundle=meta['id'], fixture=_fx(meta, x))
                cur = I[coll].get(x['id'])
                if cur is None:
                    I[coll][x['id']] = x
                elif cur['fixture'] == x['fixture'] and all(cur.get(k) == x.get(k) for k in BIB_KEYS):
                    cur['assessments'] += [a for a in x.get('assessments', []) if a not in cur['assessments']]
                else:
                    conflicts.append(dict(collection=coll, id=x['id'], key='*', kept=cur['bundle'], ignored=meta['id'],
                                          reason='same id, different source'))
        for r in b.get('reviews', []):
            I['reviews'].append(dict(copy.deepcopy(r), bundle=meta['id'], fixture=_fx(meta, r)))
    return I, conflicts


# ---------------------------------------------------------------- blindspots (from epistemic-field/1)
def _short(F, target):
    if ':' in target:
        e, d = target.split(':', 1)
        dim = next((x for x in F['dimensions'] if x['id'] == d), None)
        return f"{e} · {dim['short_label'] if dim else d}"
    return target


def blindspot_index(fields):
    """Every rim of every loaded field, plus consequential missing dimensions, with the controller actions that already
    address each one. Keys: '<batch>/<collection>/<id>'."""
    out = []
    for F in sorted(fields, key=lambda f: f['context']['batch']):
        b = F['context']['batch']
        acts = sorted(F['actions'], key=lambda a: a['rank'])
        for r in F['rims']:
            out.append(dict(key=f"{b}/rims/{r['id']}", batch=b, collection='rims', id=r['id'], type=r['type'], scope=r['scope'],
                            target=r['target'], consequential=bool(r['consequential']), statement=r['statement'],
                            label=f"{TYPE_LABEL.get(r['type'], r['type'].upper())} · {_short(F, r['target'])}",
                            actions=[dict(id=a['id'], verb=a['verb'], tier=a['tier'], status=a['status'], cost=a['cost'], title=a['title'])
                                     for a in acts if r['id'] in a['triggered_by']]))
        dims = {d['id']: d for d in F['dimensions']}
        for m in F['missing_dimensions']:
            if not m['consequential']:
                continue
            d = dims[m['dimension']]
            out.append(dict(key=f"{b}/missing_dimensions/{m['id']}", batch=b, collection='missing_dimensions', id=m['id'], type=d['family'],
                            scope='entity', target=m['entity'], consequential=True, not_acquired=True, would_require=d.get('would_require', []),
                            statement=f"{d['label']}: not acquired; consequential for {m['entity']}",
                            label=f"{TYPE_LABEL.get(d['family'], d['family'].upper())} · {m['entity']} (not acquired)",
                            actions=[dict(id=a['id'], verb=a['verb'], tier=a['tier'], status=a['status'], cost=a['cost'], title=a['title']) for a in acts
                                     if m['dimension'] in a['targets']['dimensions'] and m['entity'] in a['targets']['entities']]))
    return out


def _bs(ref, BI):
    if 'general' in ref:
        return dict(general=ref['general'], label=ref.get('label') or ref['general'], external=True, resolved=False, consequential=False)
    key = f"{ref['batch']}/{ref['collection']}/{ref['id']}"
    b = BI.get(key)
    if b is None:
        return dict(key=key, batch=ref['batch'], collection=ref['collection'], id=ref['id'], resolved=False, external=False, consequential=False)
    return dict(key=key, batch=b['batch'], collection=b['collection'], id=b['id'], resolved=True, external=False,
                consequential=b['consequential'], type=b['type'], label=b['label'], not_acquired=bool(b.get('not_acquired')))


def _preview(v):
    if isinstance(v, dict):
        return ' · '.join(f'{k} {_preview(x)}' for k, x in list(v.items())[:5] if not isinstance(x, (dict, list)))
    if isinstance(v, list):
        return ', '.join(_preview(x) for x in v[:4]) + (f' … ({len(v)})' if len(v) > 4 else '')
    if isinstance(v, float):
        return f'{v:.3g}'
    s = str(v)
    return s if len(s) <= 240 else s[:237] + '…'


def _field_ref(ref, FB):
    """Resolve {batch, collection, id?, path?} against a loaded field. Returns (ok, value)."""
    F = FB.get(ref.get('batch'))
    if F is None:
        return False, None
    try:
        return True, resolve_ref(F, dict(collection=ref['collection'], id=ref.get('id', 'batch'), path=ref.get('path')))
    except (KeyError, IndexError, TypeError, ValueError):
        return False, None


# ---------------------------------------------------------------- evidence classification
def transferability(t):
    """high: material and modality same/similar and no axis 'different'; low: material or modality 'different'; else partial."""
    t = t or {}
    if t.get('material') == 'different' or t.get('modality') == 'different':
        return 'low'
    if all(t.get(k) in ('same', 'similar') for k in ('material', 'modality')) and 'different' not in t.values():
        return 'high'
    return 'partial'


def relevance(directness, transfer):
    if directness == 'direct':
        return 'R1' if transfer != 'low' else 'R3'
    if directness == 'adjacent':
        return {'high': 'R2', 'partial': 'R3', 'low': 'R4'}[transfer]
    return 'R4'


def classify(a):
    """Derived, direction-free strength plus the display label. The underlying dimensions are kept beside them."""
    tr = transferability(a.get('transferability'))
    strength = STRENGTH[a['method_strength']][relevance(a['directness'], tr)]
    label = strength if a['direction'] == 'SUPPORTIVE' else a['direction']
    return dict(transferability_class=tr, strength=strength, label=label)


def literature_gate(rows):
    """rows: counted paper assessments for one target and one gate."""
    sup = [r for r in rows if r['direction'] == 'SUPPORTIVE' and RANK[r['strength']] >= 1]
    con = [r for r in rows if r['direction'] == 'CONTRADICTORY' and RANK[r['strength']] >= 2]
    best_s = max((RANK[r['strength']] for r in sup), default=-1)
    if con and max(RANK[r['strength']] for r in con) >= best_s:
        return 'contested'
    groups = {r['independence_group'] for r in sup if RANK[r['strength']] >= 2}
    if best_s >= 3 and len(groups) >= 2:
        return 'met'
    return 'partial' if sup else 'open'


def marker_status(G, review):
    s = {g: G[g]['state'] for g in G}
    if s['robustness'] == 'failed':
        return 'CONFOUNDED'
    if review == 'reject' or s['blindspot_closure'] == 'failed' or s['non_redundancy'] == 'failed':
        return 'REJECTED'
    if s['measurability'] == 'failed':
        return 'UNAVAILABLE'
    if s['admission'] == 'met':
        return 'ADMITTED'
    if s['scientific_relevance'] == 'met':
        return 'TRACKABLE' if s['measurability'] == 'met' else 'SUPPORTED'
    if any(s[g] in ('met', 'partial', 'contested') for g in EVIDENCE_GATES):
        return 'BUILDING'
    return 'CANDIDATE'


def why(status, G, review):
    """The specific rule that produced `status` (the generic STATUS_BASIS text stays in governance)."""
    s = {g: G[g]['state'] for g in G}
    if status == 'REJECTED':
        r = [t for c, t in ((s.get('blindspot_closure') == 'failed', 'tested: no decision value'),
                            (s.get('non_redundancy') == 'failed', 'tested: redundant with a tracked dimension'),
                            (s.get('non_substitutability') == 'failed', 'an existing capability substitutes'),
                            (review == 'reject', 'rejected by a recorded review')) if c]
        return '; '.join(r)
    if status == 'BUILDING':
        return 'partly supported: ' + ', '.join(g.replace('_', ' ') for g in EVIDENCE_GATES if s[g] in ('met', 'partial', 'contested')) + \
               '; scientific relevance not met'
    if status == 'BUILDING_CASE':
        return 'multiple credible marker needs' if s['marker_demand'] == 'met' else 'one marker need that closes a consequential blindspot'
    return STATUS_BASIS[status]


def capability_status(G, review):
    s = {g: G[g]['state'] for g in G}
    if review == 'reject' or s['non_substitutability'] == 'failed':
        return 'REJECTED'
    if review == 'integrated' and s['integration_case'] == 'met':
        return 'INTEGRATED'
    crit = all(s[g] == 'met' for g in ('marker_demand', 'literature_convergence', 'consequential_closure', 'non_substitutability'))
    if crit:
        return 'RECOMMENDED' if s['integration_case'] == 'met' else 'CRITICAL_MASS'
    if s['marker_demand'] == 'met' or (s['marker_demand'] == 'partial' and s['consequential_closure'] == 'met'):
        return 'BUILDING_CASE'
    return 'WATCHING'


def _vortex_id(ref):
    """Stable inquiry-vortex id for a resolved field limit or an explicit external vocabulary gap."""
    if ref.get('resolved'):
        return 'vortex:' + ref['key']
    if ref.get('external') and ref.get('general'):
        return 'vortex:general/' + ref['general']
    # Keep malformed input buildable so check() can report the actual unresolved-reference violation.
    return 'vortex:unresolved/' + ref.get('key', 'unknown')


def _observability(marker, test):
    """What is needed to instantiate this marker. This classifies availability; it does not judge scientific value."""
    if marker.get('current_capture_compatible') is False or marker.get('required_capabilities'):
        cls = 'requires_new_observability'
        basis = 'the marker names information or a capability absent from the current capture'
    elif test['status'] == 'requires_acquisition':
        cls = 'needs_targeted_capture'
        basis = 'the current modality can measure it, but the required capture is not in the loaded data'
    else:
        cls = 'computable_now'
        basis = 'the loaded data can support the defined test or implementation'
    return dict(cls=cls, label=OBSERVABILITY_LABEL[cls], basis=basis,
                required_modalities=marker.get('required_modalities', []),
                required_capabilities=marker.get('required_capabilities', []))


def _marker_factors(marker):
    factors = []
    if marker['closes_consequential']:
        factors.append('addresses a decision-consequential inquiry vortex')
    elif marker['vortex_refs']:
        factors.append('addresses a structured inquiry vortex')
    if any(r['resolved'] for r in marker['decision_refs']):
        factors.append('linked to a current decision')
    factors.append(marker['observability']['label'].lower())
    if marker['existing_data_test']['status'] == 'passed':
        factors.append('implemented test passed on current data')
    if marker['gates']['scientific_relevance']['state'] == 'open':
        factors.append('scientific literature basis remains open')
    if marker.get('implementation_burden'):
        factors.append(f"{marker['implementation_burden']} implementation burden")
    if marker['status'] in TERMINAL:
        factors.append('tested and set aside')
    return factors


def _opportunity_order(marker):
    """Attention order, not truth: live and consequential first, then observability, evidence, burden and stable id."""
    obs = {'computable_now': 0, 'needs_targeted_capture': 1, 'requires_new_observability': 2}
    burden = {'low': 0, 'medium': 1, 'high': 2, None: 3}
    tested = {'passed': 0, 'inconclusive': 1, 'not_run': 2, 'requires_acquisition': 3, 'not_observable': 4, 'failed': 5}
    return (marker['status'] in TERMINAL, marker['fixture'], 0 if marker['closes_consequential'] else 1,
            obs[marker['observability']['cls']], tested.get(marker['existing_data_test']['status'], 6),
            -len(marker['evidence']), burden.get(marker.get('implementation_burden'), 3), marker['id'])


def _attractor_order(capability):
    burden = {'low': 0, 'medium': 1, 'high': 2, None: 3}
    return (capability['status'] == 'REJECTED', capability['fixture'], -len(capability['closes_consequential']),
            -len(capability['marker_pool']), burden.get((capability.get('integration') or {}).get('burden'), 3), capability['id'])


def _vortices(blindspots, markers, capabilities):
    """Structured reasons to inquire, derived from field limits plus explicitly declared representation gaps."""
    out = []
    M, C = {m['id']: m for m in markers}, {c['id']: c for c in capabilities}
    for b in blindspots:
        refs = b.get('addressed_by', [])
        out.append(dict(
            id='vortex:' + b['key'], label=b['label'], kind=VORTEX_KIND.get(b['type'], 'structured_uncertainty'),
            statement=b['statement'], source='epistemic-field/1', instantiated=True,
            attention='decision_consequential' if b['consequential'] else 'structured_limit', consequential=b['consequential'],
            evidence_refs=[dict(batch=b['batch'], collection=b['collection'], id=b['id'])],
            marker_refs=sorted(x for x in refs if x in M), capability_refs=sorted(x for x in refs if x in C),
            current_actions=b['actions']))
    general = {}
    for marker in markers:
        for g in marker['general_gaps']:
            x = general.setdefault(g['general'], dict(label=g['label'], markers=set(), capabilities=set()))
            x['markers'].add(marker['id'])
    for capability in capabilities:
        for g in capability['general_gaps']:
            x = general.setdefault(g['general'], dict(label=g['label'], markers=set(), capabilities=set()))
            x['capabilities'].add(capability['id'])
    for key, g in sorted(general.items()):
        out.append(dict(id='vortex:general/' + key, label=g['label'], kind='representational_gap',
                        statement='A proposed vocabulary gap; no loaded field directly instantiates it.', source='research_bundle',
                        instantiated=False, attention='external_hypothesis', consequential=False, evidence_refs=[],
                        marker_refs=sorted(g['markers']), capability_refs=sorted(g['capabilities']), current_actions=[]))
    return out


# ---------------------------------------------------------------- build
def build(fields, bundles):
    """marker-frontier/1 from the loaded epistemic fields and research bundles. Deterministic."""
    for F in fields:
        if F.get('schema_version') != 'epistemic-field/1':
            raise ValueError('marker frontier expects epistemic-field/1 documents')
    fields = sorted(fields, key=lambda F: F['context']['batch'])
    FB = {F['context']['batch']: F for F in fields}
    I, conflicts = merge(bundles)
    idx = blindspot_index(fields)
    BI = {b['key']: b for b in idx}
    ignored = []
    for m in I['markers'].values():   # a capability a marker names but nobody has described yet: a visible stub
        for cid in m.get('required_capabilities', []):
            if cid not in I['capabilities']:
                I['capabilities'][cid] = dict(id=cid, name=cid.split(':', 1)[-1].replace('_', ' '), capability_type='unspecified',
                                              bundle=m['bundle'], fixture=m['fixture'], provenance=dict(kind='derived_stub', basis=f"named by {m['id']}"))

    papers, records = [], []
    for p in sorted(I['papers'].values(), key=lambda x: x['id']):
        url = p.get('url') or (f"https://doi.org/{p['doi']}" if p.get('doi') else None)
        rows = []
        for a in sorted(p.get('assessments', []), key=lambda a: (a['target'], a['gate'], a['direction'])):
            rows.append(dict(a, **classify(a), counts=not p['fixture']))
        papers.append(dict(id=p['id'], title=p['title'], authors=p.get('authors', []), year=p.get('year'), venue=p.get('venue'),
                           doi=p.get('doi'), url=url, fixture=p['fixture'], bundle=p['bundle'], independence_group=p.get('independence_group') or p['id'],
                           blindspot_refs=[_bs(r, BI) for r in p.get('blindspot_refs', [])], provenance=p.get('provenance', {}),
                           marker_refs=sorted({a['target'] for a in rows if a['target'].startswith('marker:')}),
                           capability_refs=sorted({a['target'] for a in rows if a['target'].startswith('capability:')}), assessments=rows))
    for r in sorted(I['records'].values(), key=lambda x: x['id']):
        out = dict(id=r['id'], kind=r['kind'], title=r['title'], fixture=r['fixture'], bundle=r['bundle'], provenance=r.get('provenance', {}),
                   source=r.get('source'), field_ref=r.get('field_ref'),
                   assessments=[dict(a, counts=not r['fixture']) for a in sorted(r.get('assessments', []), key=lambda a: (a['target'], a['gate']))])
        if r.get('field_ref'):
            ok, v = _field_ref(r['field_ref'], FB)
            out.update(resolved=ok, preview=_preview(v) if ok else None)
        records.append(out)
    PAP, REC = {p['id']: p for p in papers}, {r['id']: r for r in records}

    def rows_for(cid):
        rows = [dict(source='paper', id=p['id'], independence_group=p['independence_group'], fixture=p['fixture'], **a)
                for p in papers for a in p['assessments'] if a['target'] == cid]
        rows += [dict(source='record', id=r['id'], kind=r['kind'], fixture=r['fixture'], **a)
                 for r in records for a in r['assessments'] if a['target'] == cid]
        return rows

    def review_for(cid):
        rv = sorted([r for r in I['reviews'] if r['target'] == cid and not r['fixture']], key=lambda r: r.get('date') or '')
        return rv[-1] if rv else None

    def counted(basis):
        ok = []
        for x in basis or []:
            if isinstance(x, dict):
                if _field_ref(x, FB)[0]:
                    ok.append(x)
            elif x in REC and not REC[x]['fixture']:
                ok.append(x)
            elif x in PAP and not PAP[x]['fixture']:
                ok.append(x)
        return ok

    def gate(state, basis=(), excluded=()):
        return dict(state=state, basis=sorted(set(basis)), excluded_fixture=sorted(set(excluded)))

    def outcomes(rows, g):
        return {r['outcome'] for r in rows if r['source'] == 'record' and r['counts'] and r['gate'] == g}

    def ids(rows, g, src=None):
        return [r['id'] for r in rows if r['gate'] == g and r['counts'] and (src is None or r['source'] == src)]

    def fx_ids(rows, g):
        return [r['id'] for r in rows if r['gate'] == g and not r['counts']]

    def evidence_rows(rows):
        ev = [dict(source=r['source'], id=r['id'], gate=r['gate'], counts=r['counts'], claim=r.get('claim'), note=r.get('note'),
                   **({'direction': r['direction'], 'label': r['label'], 'strength': r['strength']} if r['source'] == 'paper' else
                      {'outcome': r['outcome'], 'kind': r['kind']})) for r in rows]
        return sorted(ev, key=lambda e: (e['source'], e['gate'], e['id']))

    # ---- markers
    markers = []
    for m in sorted(I['markers'].values(), key=lambda x: x['id']):
        rows = rows_for(m['id'])
        P = [r for r in rows if r['source'] == 'paper' and r['counts']]
        bs = [_bs(r, BI) for r in m.get('blindspot_refs', [])]
        dec = [dict(r, resolved=_field_ref(r, FB)[0]) for r in m.get('decision_refs', [])]
        G = {}
        g = literature_gate([r for r in P if r['gate'] == 'scientific_relevance'])
        if 'failed' in outcomes(rows, 'scientific_relevance'):
            g = 'contested'
        G['scientific_relevance'] = gate(g, ids(rows, 'scientific_relevance'), fx_ids(rows, 'scientific_relevance'))
        cc, o = m.get('current_capture_compatible'), outcomes(rows, 'measurability')
        g = 'failed' if cc is False or 'failed' in o else 'met' if 'passed' in o else 'partial' if cc is True or 'inconclusive' in o else 'open'
        G['measurability'] = gate(g, ids(rows, 'measurability'), fx_ids(rows, 'measurability'))
        o = outcomes(rows, 'robustness')
        conf = m.get('known_confounds', [])
        ctl = [c for c in conf if c.get('controlled') is True and counted(c.get('basis'))]
        contra = [r for r in P if r['gate'] == 'robustness' and r['direction'] == 'CONTRADICTORY' and RANK[r['strength']] >= 2]
        g = ('failed' if 'failed' in o else 'contested' if contra and 'passed' not in o else
             'met' if 'passed' in o and len(ctl) == len(conf) else 'partial' if o or ctl else 'open')
        G['robustness'] = gate(g, ids(rows, 'robustness') + [f"confound:{c['id']}" for c in ctl], fx_ids(rows, 'robustness'))
        o = outcomes(rows, 'decision_value')
        cons = [b for b in bs if b['resolved'] and b['consequential']]
        g = ('failed' if 'failed' in o else 'met' if cons or 'passed' in o else
             'partial' if any(b['resolved'] or b['external'] for b in bs) or any(d['resolved'] for d in dec) else 'open')
        G['blindspot_closure'] = gate(g, ids(rows, 'decision_value') + [b['key'] for b in cons], fx_ids(rows, 'decision_value'))
        o = outcomes(rows, 'non_redundancy')
        unacq = [b['key'] for b in bs if b.get('not_acquired')]
        g = 'failed' if 'failed' in o else 'met' if 'passed' in o or unacq else 'partial' if m.get('redundant_with') else 'open'
        G['non_redundancy'] = gate(g, ids(rows, 'non_redundancy') + unacq, fx_ids(rows, 'non_redundancy'))
        rv = review_for(m['id'])
        ready = all(G[x]['state'] == 'met' for x in ADMISSION_GATES)
        admit = bool(rv and rv['decision'] == 'admit')
        if admit and not ready:
            ignored.append(dict(target=m['id'], review=rv['decision'], reason='admission review ignored: evidence gates not all met'))
        G['admission'] = gate('met' if ready and admit else 'partial' if ready else 'open', [f"review:{rv['by']}:{rv.get('date')}"] if ready and admit else [])
        status = marker_status(G, rv['decision'] if rv else None)
        o, declared = outcomes(rows, 'measurability'), (m.get('existing_data_test') or {}).get('status')
        test = ('not_observable' if cc is False else next((x for x in ('failed', 'passed') if x in o), None)
                or ('requires_acquisition' if declared == 'requires_acquisition' else 'inconclusive' if 'inconclusive' in o else 'not_run'))
        req_acts = [dict(batch=b['batch'], **a) for b in bs if b['resolved'] for a in BI[b['key']]['actions']] if test == 'requires_acquisition' else []
        ev = evidence_rows(rows)
        existing_test = dict(m.get('existing_data_test') or {}, status=test, requires_actions=req_acts)
        representation = m.get('representation') or FAMILY_REPRESENTATION.get(m['family'], 'other')
        marker_kind = m.get('marker_kind') or ('qualitative' if representation in QUALITATIVE_REPRESENTATIONS else 'quantitative')
        marker = dict(
            {k: m.get(k) for k in ('id', 'name', 'family', 'proposition', 'scientific_definition', 'measurement_definition', 'why_relevant',
                                   'decision_relevance', 'capture_requirements', 'current_capture_compatible', 'implementation_burden')},
            marker_kind=marker_kind, representation=representation, observable=m.get('observable') or m['proposition'],
            scientific_question=m.get('scientific_question'),
            required_modalities=m.get('required_modalities', []), required_capabilities=m.get('required_capabilities', []),
            known_confounds=conf, known_failure_modes=m.get('known_failure_modes', []), redundant_with=m.get('redundant_with', []),
            existing_data_test=existing_test,
            blindspot_refs=bs, decision_refs=dec, closes=[b['key'] for b in bs if b['resolved']], closes_consequential=[b['key'] for b in cons],
            general_gaps=[dict(general=b['general'], label=b['label']) for b in bs if b['external']],
            vortex_refs=[_vortex_id(b) for b in bs],
            status=status, status_basis=why(status, G, rv['decision'] if rv else None), review=rv,
            lane='new_capability' if G['measurability']['state'] == 'failed' and m.get('required_capabilities') else 'current_capture',
            gates=G, rail=[dict(gate=x, state=G[x]['state']) for x, _ in MARKER_RAIL],
            next=[dict(gate=x, text=MISSING[x][G[x]['state']]) for x in MARKER_GATES if G[x]['state'] != 'met' and G[x]['state'] in MISSING[x]],
            qualifiers=_qualifiers(status, cons, G['scientific_relevance']['state'], m['fixture']),
            evidence=[e for e in ev if e.get('direction') != 'CONTRADICTORY'],
            contradictory_evidence=[e for e in ev if e.get('direction') == 'CONTRADICTORY'],
            counts=_counts(rows), fixture=m['fixture'], bundle=m['bundle'], extended_by=m.get('extended_by', []), provenance=m.get('provenance', {}))
        marker['observability'] = _observability(m, existing_test)
        marker['investigation_state'] = INVESTIGATION_STATE[status]
        marker['ranking_factors'] = _marker_factors(marker)
        markers.append(marker)
    MK = {m['id']: m for m in markers}

    # ---- capabilities (demand accumulates across marker cases)
    caps = []
    for c in sorted(I['capabilities'].values(), key=lambda x: x['id']):
        rows = rows_for(c['id'])
        P = [r for r in rows if r['source'] == 'paper' and r['counts']]
        demanding = [m for m in markers if c['id'] in m['required_capabilities']]
        active = [m for m in demanding if m['status'] not in TERMINAL and not m['fixture']]
        credible = [m for m in active if m['gates']['scientific_relevance']['state'] == 'met']
        G = {}
        G['marker_demand'] = gate('met' if len(credible) >= 2 else 'partial' if active else 'open', [m['id'] for m in active])
        G['literature_convergence'] = gate(literature_gate([r for r in P if r['gate'] == 'literature_convergence']),
                                           ids(rows, 'literature_convergence'), fx_ids(rows, 'literature_convergence'))
        own = [_bs(r, BI) for r in c.get('blindspot_refs', [])]
        seen, bs = set(), []
        for b in own + [b for m in active for b in m['blindspot_refs']]:
            k = b.get('key') or 'general:' + b['general']
            if k not in seen:
                seen.add(k)
                bs.append(b)
        cons = [b for b in bs if b['resolved'] and b['consequential']]
        G['consequential_closure'] = gate('met' if cons else 'partial' if any(b['resolved'] or b['external'] for b in bs) else 'open',
                                          [b['key'] for b in cons])
        subs = c.get('existing_capability_substitutes', [])
        out_ = [s for s in subs if s.get('ruled_out') is True and counted(s.get('basis'))]
        adequate = [s for s in subs if s.get('ruled_out') is False and counted(s.get('basis'))]
        G['non_substitutability'] = gate('failed' if adequate else 'met' if subs and len(out_) == len(subs) else 'partial' if out_ else 'open',
                                         [f"substitute:{s['id']}" for s in out_ + adequate])
        integ = c.get('integration') or {}
        rv = review_for(c['id'])
        rec = bool(rv and rv['decision'] in ('recommend', 'integrated'))
        G['integration_case'] = gate('met' if integ.get('acceptable') is True and rec else 'partial' if integ.get('burden') else 'open',
                                     [f"review:{rv['by']}:{rv.get('date')}"] if integ.get('acceptable') is True and rec else [])
        status = capability_status(G, rv['decision'] if rv else None)
        if rv and rv['decision'] in ('recommend', 'integrated') and status not in ('RECOMMENDED', 'INTEGRATED'):
            ignored.append(dict(target=c['id'], review=rv['decision'], reason='review ignored: critical mass or accepted integration case missing'))
        dec_refs = [dict(r, resolved=_field_ref(r, FB)[0]) for r in c.get('decision_refs', [])]
        acts = sorted({(b['batch'], a['id']) for b in cons for a in BI[b['key']]['actions']})
        ev = evidence_rows(rows)
        capability = dict(
            {k: c.get(k) for k in ('id', 'name', 'capability_type', 'why_current_workflow_cannot_resolve', 'non_substitutability_evidence')},
            existing_capability_substitutes=subs, integration=c.get('integration'),
            blindspot_refs=own, closes=[b['key'] for b in bs if b['resolved']], closes_consequential=[b['key'] for b in cons],
            general_gaps=[dict(general=b['general'], label=b['label']) for b in bs if b['external']],
            vortex_refs=[_vortex_id(b) for b in bs],
            markers_unlocked=[m['id'] for m in demanding], marker_demands=[m['id'] for m in active], credible_demands=[m['id'] for m in credible],
            marker_pool=[m['id'] for m in active], required_information=[m['observable'] for m in active],
            decision_refs=dec_refs, decisions_affected=[dict(batch=b, action=a) for b, a in acts],
            status=status, status_basis=why(status, G, rv['decision'] if rv else None), review=rv,
            gates=G, rail=[dict(gate=x, state=G[x]['state']) for x, _ in CAPABILITY_RAIL],
            next=[dict(gate=x, text=MISSING[x][G[x]['state']]) for x, _ in CAPABILITY_RAIL if G[x]['state'] != 'met' and G[x]['state'] in MISSING[x]],
            qualifiers=_qualifiers(status, cons, G['literature_convergence']['state'], c['fixture']),
            evidence=[e for e in ev if e.get('direction') != 'CONTRADICTORY'],
            contradictory_evidence=[e for e in ev if e.get('direction') == 'CONTRADICTORY'],
            counts=dict(_counts(rows), marker_demands=len(active), credible_demands=len(credible),
                        markers_unlocked=len(demanding), markers_unlocked_fixture=sum(m['fixture'] for m in demanding),
                        integration_burden=integ.get('burden')),
            fixture=c['fixture'], bundle=c['bundle'], extended_by=c.get('extended_by', []), provenance=c.get('provenance', {}))
        capability['attractor_state'] = ATTRACTOR_STATE[status]
        capability['ranking_factors'] = ([f"unlocks {len(active)} active marker opportunit{'y' if len(active) == 1 else 'ies'}"] if active else []) + \
            (['addresses a decision-consequential inquiry vortex'] if cons else ['no decision-consequential vortex linked']) + \
            ([f"{integ.get('burden')} integration burden"] if integ.get('burden') else ['integration burden unassessed'])
        caps.append(capability)

    addressed = {}
    for case in markers + caps:
        for k in case['closes']:
            addressed.setdefault(k, []).append(case['id'])
    for b in idx:
        b['addressed_by'] = sorted(addressed.get(b['key'], []))
    live = {x['id'] for x in markers + caps if x['status'] not in TERMINAL and not x['fixture']}
    opportunity_markers = sorted([m for m in markers if m['status'] not in TERMINAL and not m['fixture']], key=_opportunity_order)
    current_frontier = [m['id'] for m in opportunity_markers[:3]]
    for rank, marker in enumerate(opportunity_markers, 1):
        marker['opportunity_rank'] = rank
        marker['priority_band'] = 'current_frontier' if marker['id'] in current_frontier else 'investigate'
    for marker in markers:
        if marker['status'] in TERMINAL:
            marker['opportunity_rank'] = None
            marker['priority_band'] = 'set_aside'
        elif marker['fixture']:
            marker['opportunity_rank'] = None
            marker['priority_band'] = 'fixture'
    # A capability becomes an attractor only through an active marker payload. A bare capability case remains
    # inspectable in the contract but is not surfaced as a tooling opportunity or roadmap recommendation.
    attractors = sorted([c for c in caps if c['status'] != 'REJECTED' and not c['fixture'] and c['marker_pool']], key=_attractor_order)
    for rank, capability in enumerate(attractors, 1):
        capability['attractor_rank'] = rank
    for capability in caps:
        if capability not in attractors:
            capability['attractor_rank'] = None
    vortices = _vortices(idx, markers, caps)
    candidate_markers = {
        cls: [m['id'] for m in opportunity_markers if m['observability']['cls'] == cls]
        for cls in ('computable_now', 'needs_targeted_capture', 'requires_new_observability')
    }
    candidate_markers['set_aside'] = [m['id'] for m in sorted([m for m in markers if m['status'] in TERMINAL], key=_marker_order)]
    roadmap = [
        dict(id='test_current_data', label='TEST CURRENT DATA',
             purpose='Implement or validate marker protocols supported by the loaded data.',
             marker_refs=candidate_markers['computable_now']),
        dict(id='capture_same_modality', label='TARGETED CAPTURE',
             purpose='Use an existing modality at the scale or sampling pattern the marker requires.',
             marker_refs=candidate_markers['needs_targeted_capture']),
        dict(id='expand_observability', label='EXPAND OBSERVABILITY',
             purpose='Evaluate capability payloads that unlock otherwise inaccessible marker families.',
             capability_refs=[c['id'] for c in attractors]),
        dict(id='reobserve', label='RE-OBSERVE',
             purpose='Feed validated markers and newly acquired information back through the local Examiner loop.',
             depends_on=['test_current_data', 'capture_same_modality', 'expand_observability']),
    ] if markers or attractors else []
    lanes = dict(current_capture=[m['id'] for m in sorted([m for m in markers if m['lane'] == 'current_capture'], key=_marker_order)],
                 new_capability=[c['id'] for c in sorted(caps, key=_cap_order)])
    doc = dict(
        schema_version=SCHEMA_VERSION,
        context=dict(fields=[dict(batch=F['context']['batch'], reference=F['context']['reference'], verdict=F['decision']['verdict']) for F in fields],
                     bundles=I['bundles'], literature_present=any(not p['fixture'] for p in papers),
                     fixture_present=any(b['kind'] == 'fixture' for b in I['bundles']),
                     research_agent_present=any(b['kind'] == 'research_agent' for b in I['bundles'])),
        rails=dict(marker=[dict(gate=g, label=l) for g, l in MARKER_RAIL], capability=[dict(gate=g, label=l) for g, l in CAPABILITY_RAIL]),
        blindspots=idx,
        vortices=vortices,
        open_blindspots=[b['key'] for b in idx if b['consequential'] and not set(b['addressed_by']) & live],
        opportunity_map=dict(
            question='What additional useful ways of perceiving the current dataset should be investigated?',
            local_loop='NEXT CAPTURE resolves the current decision; this map searches for better representations and future observability.',
            current_frontier=current_frontier, candidate_markers=candidate_markers,
            tooling_attractors=[c['id'] for c in attractors], roadmap=roadmap,
            ranking_policy=['decision-consequential inquiry first', 'then current-data testability',
                            'then existing evidence and implementation burden', 'stable id breaks remaining ties']),
        lanes=lanes, markers=markers, capabilities=caps, papers=papers, records=records,
        reviews=sorted(I['reviews'], key=lambda r: (r['target'], r.get('date') or '', r['bundle'])),
        governance=dict(rules=GOVERNANCE_RULES, status_basis=STATUS_BASIS, conflicts=conflicts, ignored=ignored))
    return doc


def _qualifiers(status, cons, lit_state, fixture):
    q = []
    if cons:
        q.append('OPEN CONSEQUENTIAL BLINDSPOT')
    if lit_state == 'open' and status not in TERMINAL:
        q.append('RESEARCH CASE OPEN')
    if fixture:
        q.append('FIXTURE')
    return q


def _counts(rows):
    pap = [r for r in rows if r['source'] == 'paper']
    n = lambda f: len({r['id'] for r in pap if f(r)})
    return dict(papers=n(lambda r: True), supporting=n(lambda r: r['counts'] and r['direction'] == 'SUPPORTIVE' and RANK[r['strength']] >= 2),
                strong_direct=n(lambda r: r['counts'] and r['label'] == 'STRONG DIRECT'),
                contradictory=n(lambda r: r['counts'] and r['direction'] == 'CONTRADICTORY'),
                fixture_papers=n(lambda r: not r['counts']), records=len({r['id'] for r in rows if r['source'] == 'record' and r['counts']}))


def _marker_order(m):
    return (MARKER_STATES.index(m['status']), m['fixture'], -len(m['closes_consequential']), m['id'])


def _cap_order(c):
    return (CAPABILITY_STATES.index(c['status']), c['fixture'], -len(c['closes_consequential']), c['id'])


# ---------------------------------------------------------------- coherence
def check(doc, fields=None, bundles=None, root=ROOT):
    """Violations of marker-frontier/1 (empty list = coherent). With fields and bundles, also verifies that the document
    is exactly what the rules derive from them (no hand-edited state)."""
    bad = []
    if doc.get('schema_version') != SCHEMA_VERSION:
        bad.append('schema_version')
    M, C = {m['id']: m for m in doc['markers']}, {c['id']: c for c in doc['capabilities']}
    V = {v['id']: v for v in doc.get('vortices', [])}
    P, R = {p['id']: p for p in doc['papers']}, {r['id']: r for r in doc['records']}
    for name, coll in (('markers', doc['markers']), ('capabilities', doc['capabilities']), ('papers', doc['papers']), ('records', doc['records'])):
        if len({x['id'] for x in coll}) != len(coll):
            bad.append(f'{name}: duplicate ids')
    for src in doc['papers'] + doc['records']:
        for a in src['assessments']:
            if a['target'] not in M and a['target'] not in C:
                bad.append(f"{src['id']}: assessment target {a['target']} resolves to no case")
    for p in doc['papers']:
        if not p['fixture'] and not (p['url'] or '').startswith('https://'):
            bad.append(f"{p['id']}: a non-fixture paper needs a canonical https link or DOI")
        for a in p['assessments']:
            if a['direction'] == 'CONTRADICTORY':
                case = M.get(a['target']) or C.get(a['target'])
                if case and not any(e['id'] == p['id'] and e['gate'] == a['gate'] for e in case['contradictory_evidence']):
                    bad.append(f"{p['id']}: contradictory assessment missing from {a['target']}")
            if a['counts'] == p['fixture']:
                bad.append(f"{p['id']}: fixture evidence must not count (and real evidence must)")
    for r in doc['records']:
        if r.get('field_ref') and not r.get('resolved'):
            bad.append(f"{r['id']}: field reference does not resolve")
        src = r.get('source') or {}
        if src.get('path') and root:
            p = os.path.join(root, src['path'])
            if not os.path.exists(p) or (src.get('locator') and src['locator'] not in open(p, encoding='utf-8').read()):
                bad.append(f"{r['id']}: source {src['path']} / locator {src.get('locator')!r} not found")
        if not r.get('field_ref') and not src.get('path') and not r['fixture']:
            bad.append(f"{r['id']}: a non-fixture record needs a field reference or a source path")
    fixture_ids = {x['id'] for x in doc['papers'] + doc['records'] if x['fixture']}
    for case in doc['markers'] + doc['capabilities']:
        cid = case['id']
        for b in case['blindspot_refs']:
            if not (b['resolved'] or b['external']):
                bad.append(f"{cid}: blindspot {b.get('key')} does not resolve and is not marked general")
        for g, v in case['gates'].items():
            if v['state'] not in GATE_STATES:
                bad.append(f'{cid}: gate {g} has unknown state {v["state"]}')
            if set(v['basis']) & fixture_ids:
                bad.append(f'{cid}: gate {g} rests on fixture evidence')
        if set(case['closes_consequential']) - set(case['closes']):
            bad.append(f'{cid}: consequential closure outside its closures')
    for m in doc['markers']:
        G = {g: v['state'] for g, v in m['gates'].items()}
        if marker_status(m['gates'], (m['review'] or {}).get('decision')) != m['status']:
            bad.append(f"{m['id']}: status {m['status']} does not follow from its gates")
        if m['status'] == 'ADMITTED' and not (all(G[g] == 'met' for g in ADMISSION_GATES) and m['review'] and m['review']['decision'] == 'admit'
                                              and not m['review'].get('fixture')):
            bad.append(f"{m['id']}: ADMITTED without measurability / robustness / blindspot value / non-redundancy / review")
        for cid in m['required_capabilities']:
            if cid not in C:
                bad.append(f"{m['id']}: required capability {cid} has no case")
        if m['current_capture_compatible'] is False and not m['required_capabilities']:
            bad.append(f"{m['id']}: current capture cannot observe it, but it names no capability that could")
        expected_obs = _observability(m, m['existing_data_test'])['cls']
        if m.get('observability', {}).get('cls') != expected_obs:
            bad.append(f"{m['id']}: observability class does not follow from capture compatibility and test state")
        if m.get('marker_kind') not in ('quantitative', 'qualitative', 'hybrid'):
            bad.append(f"{m['id']}: marker kind is not quantitative, qualitative or hybrid")
        if not m.get('representation') or not m.get('observable'):
            bad.append(f"{m['id']}: marker protocol lacks a representation or observable")
        for vid in m.get('vortex_refs', []):
            if vid not in V:
                bad.append(f"{m['id']}: inquiry vortex {vid} does not resolve")
    for c in doc['capabilities']:
        G = {g: v['state'] for g, v in c['gates'].items()}
        if capability_status(c['gates'], (c['review'] or {}).get('decision')) != c['status']:
            bad.append(f"{c['id']}: status {c['status']} does not follow from its gates")
        for mid in c['markers_unlocked']:
            if mid not in M or c['id'] not in M[mid]['required_capabilities']:
                bad.append(f"{c['id']}: unlocked marker {mid} does not resolve")
        if c['status'] in ('CRITICAL_MASS', 'RECOMMENDED') and not (
                G['marker_demand'] == 'met' and G['consequential_closure'] == 'met' and G['non_substitutability'] == 'met'
                and G['literature_convergence'] == 'met' and len(c['credible_demands']) >= 2 and c['closes_consequential']):
            bad.append(f"{c['id']}: {c['status']} without convergent marker demand / consequential blindspot / non-substitutability")
        if any(M[m]['fixture'] for m in c['marker_demands'] if m in M):
            bad.append(f"{c['id']}: a fixture marker counts as demand")
        expected_pool = [m['id'] for m in doc['markers'] if c['id'] in m['required_capabilities'] and m['status'] not in TERMINAL and not m['fixture']]
        if c.get('marker_pool') != expected_pool:
            bad.append(f"{c['id']}: tooling-attractor marker pool does not match active inaccessible markers")
        for vid in c.get('vortex_refs', []):
            if vid not in V:
                bad.append(f"{c['id']}: inquiry vortex {vid} does not resolve")
    for v in V.values():
        for mid in v['marker_refs']:
            if mid not in M or v['id'] not in M[mid]['vortex_refs']:
                bad.append(f"{v['id']}: marker link {mid} is not reciprocal")
        for cid in v['capability_refs']:
            if cid not in C or v['id'] not in C[cid]['vortex_refs']:
                bad.append(f"{v['id']}: capability link {cid} is not reciprocal")
    if doc['lanes']['current_capture'] != [m['id'] for m in sorted([m for m in doc['markers'] if m['lane'] == 'current_capture'], key=_marker_order)]:
        bad.append('lanes.current_capture not in rule order')
    if doc['lanes']['new_capability'] != [c['id'] for c in sorted(doc['capabilities'], key=_cap_order)]:
        bad.append('lanes.new_capability not in rule order')
    O = doc.get('opportunity_map') or {}
    active = sorted([m for m in doc['markers'] if m['status'] not in TERMINAL and not m['fixture']], key=_opportunity_order)
    expected_frontier = [m['id'] for m in active[:3]]
    if O.get('current_frontier') != expected_frontier:
        bad.append('opportunity_map.current_frontier not in deterministic attention order')
    groups = O.get('candidate_markers') or {}
    for cls in ('computable_now', 'needs_targeted_capture', 'requires_new_observability'):
        expected = [m['id'] for m in active if m['observability']['cls'] == cls]
        if groups.get(cls) != expected:
            bad.append(f'opportunity_map.candidate_markers.{cls} is incoherent')
    expected_attractors = [c['id'] for c in sorted([c for c in doc['capabilities']
                                                   if c['status'] != 'REJECTED' and not c['fixture'] and c['marker_pool']],
                                                  key=_attractor_order)]
    if O.get('tooling_attractors') != expected_attractors:
        bad.append('opportunity_map.tooling_attractors not in deterministic payload order')
    roadmap_refs = {x for step in O.get('roadmap', []) for x in step.get('marker_refs', [])}
    roadmap_caps = {x for step in O.get('roadmap', []) for x in step.get('capability_refs', [])}
    roadmap_ids = {step.get('id') for step in O.get('roadmap', [])}
    roadmap_deps = {x for step in O.get('roadmap', []) for x in step.get('depends_on', [])}
    if roadmap_refs - set(M):
        bad.append('opportunity roadmap contains an unknown marker')
    if roadmap_caps - set(C):
        bad.append('opportunity roadmap contains an unknown capability')
    if roadmap_deps - roadmap_ids:
        bad.append('opportunity roadmap contains an unknown dependency')

    def keys(o, path=''):
        if isinstance(o, dict):
            for k, v in o.items():
                yield path + '.' + k
                yield from keys(v, path + '.' + k)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v, path)
    for k in keys(doc):
        if OPAQUE_KEYS.search(k.rsplit('.', 1)[-1]):
            bad.append(f'opaque score-like key {k}')
    if fields is not None and bundles is not None:
        if json.dumps(build(fields, bundles), sort_keys=True) != json.dumps(doc, sort_keys=True):
            bad.append('document differs from what the rules derive from its fields and bundles')
    return bad


# ---------------------------------------------------------------- host / IO
def inject(html, doc):
    """Add the frontier as its own payload tag; the renderer reads it next to the evidence payload (no change to the host)."""
    tag = '<script id="frontier-payload" type="application/json">' + json.dumps(doc, separators=(',', ':')).replace('</', '<\\/') + '</script>'
    i = html.rfind('</body>')
    return html[:i] + tag + html[i:] if i >= 0 else html + tag


def from_paths(field_paths, bundle_dir=None):
    fields = [json.load(open(p, encoding='utf-8')) for p in sorted(field_paths)]
    fields = [F for F in fields if F.get('schema_version') == 'epistemic-field/1']
    return build(fields, load_bundles(bundle_dir))


def for_reports(reports_dir, bundle_dir=None):
    """Lab-level frontier over every assessed batch (reports/<batch>/field.json) and the research inbox."""
    return from_paths(glob.glob(os.path.join(reports_dir, '*', 'field.json')), bundle_dir)


def attach(html, reports_dir, bundle_dir=None):
    """Host hook: the instrument page plus the lab-level frontier. A broken research bundle must never take the
    decision surface down, so any failure returns the page unchanged (the error is printed, not hidden)."""
    try:
        return inject(html, for_reports(reports_dir, bundle_dir))
    except Exception as e:   # noqa: BLE001 - deliberate: the frontier is an optional layer under the decision
        print(f'marker frontier not attached: {type(e).__name__}: {e}')
        return html


def signature(reports_dir, bundle_dir=None):
    """Cache key for hosts that memoise the rendered page: every input file of the frontier with its mtime."""
    paths = glob.glob(os.path.join(reports_dir, '*', 'field.json')) + glob.glob(os.path.join(bundle_dir or RESEARCH_DIR, '*.json'))
    return tuple(sorted((p, os.path.getmtime(p)) for p in paths))


def write(doc, path):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    return path


FIXTURE_FIELDS = [os.path.join(ROOT, 'fixtures', f'epistemic_field.{b}.json') for b in ('Batch_2', 'Batch_3')]
EXAMPLE_BUNDLE = os.path.join(ROOT, 'fixtures', 'frontier', 'example.qte77.json')


def fixture_inputs(example=False):
    fields = [json.load(open(p, encoding='utf-8')) for p in FIXTURE_FIELDS]
    paths = sorted(glob.glob(os.path.join(ROOT, 'research', '*.json'))) + ([EXAMPLE_BUNDLE] if example else [])
    return fields, load_bundles(paths)


def main():
    ap = argparse.ArgumentParser(prog='python -m qc.frontier')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('fixtures', help='rebuild fixtures/marker_frontier.json (research/ only) and .example.json (+ FIXTURE bundle)')
    b = sub.add_parser('build')
    b.add_argument('--fields', nargs='+', required=True)
    b.add_argument('--bundles', default=None, help='directory of marker-research/1 bundles (default: research/)')
    b.add_argument('--out', required=True)
    args = ap.parse_args()
    if args.cmd == 'fixtures':
        for example, name in ((False, 'marker_frontier.json'), (True, 'marker_frontier.example.json')):
            fields, bundles = fixture_inputs(example)
            doc = build(fields, bundles)
            bad = check(doc, fields, bundles)
            print(write(doc, os.path.join(ROOT, 'fixtures', name)), 'coherent' if not bad else f'{len(bad)} violations: ' + '; '.join(bad[:5]))
        return
    fields = [json.load(open(p, encoding='utf-8')) for p in args.fields]
    bundles = load_bundles(args.bundles)
    doc = build(fields, bundles)
    bad = check(doc, fields, bundles)
    print(write(doc, args.out), 'coherent' if not bad else f'{len(bad)} violations: ' + '; '.join(bad[:5]))


if __name__ == '__main__':
    main()
