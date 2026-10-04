"""Governed decision brief (decision-brief/1): the human decision layer above epistemic-field/1.

The brief contains no science of its own. It selects, groups and words facts that already exist in the field:
  * every claim carries proof_refs ({collection, id, path}, the same addressing the field uses for trigger_facts);
  * every number in a claim is a value copied from a referenced field location; the text is rendered from a fixed
    template, so prose cannot introduce a number (check() re-renders and compares);
  * every state is chosen by a deterministic rule from explicit engine flags (verdict, leverage cause, rim
    consequentiality, scrutiny outcome, action tier); the template is chosen by the state, so wording cannot strengthen it;
  * governance selects a small non-redundant set: one content claim per redundancy group; pointer claims only refer to
    another block and carry no numbers.
Data sufficiency is judged separately for the QC decision, material attribution, lot prevalence and the tested
spatial / scale / acquisition regime. "No expansion justified at tested scales" means nothing currently observed
justifies more acquisition of that kind for the stated decision, not that nothing unknown exists.

An optional compositor (e.g. an LLM) may later rephrase approved claims through `compose()`; its output must still pass
check(): same states, same values, same proof refs. It may not decide, infer or choose a different action policy.
"""
import copy
import json
import re

SCHEMA_VERSION = 'decision-brief/1'

# state vocabularies (the status is the meaning; labels are default wording a renderer may restyle)
SUPPORT = {'sufficient': 'SUFFICIENT', 'at_minimum': 'SUFFICIENT AT MINIMUM', 'partial': 'PARTIAL',
           'expansion_needed': 'EXPANSION NEEDED', 'change_modality': 'CHANGE MODALITY', 'reacquire': 'REACQUIRE / INVALID',
           'not_applicable': 'NOT APPLICABLE', 'no_expansion_justified': 'NO EXPANSION JUSTIFIED AT TESTED SCALES'}
SUPPORT_ORDER = ['reacquire', 'change_modality', 'expansion_needed', 'partial', 'at_minimum', 'no_expansion_justified',
                 'sufficient', 'not_applicable']   # worst first; an explicit stop statement outranks plain sufficiency                     # worst first
POLICY = {'verify_first': 'VERIFY FIRST', 'change_modality': 'CHANGE MODALITY', 'extend': 'EXTEND THE CAPTURE',
          'expand_sampling': 'EXPAND SAMPLING', 'stop': 'STOP'}
EVIDENCE = {'survives': 'SURVIVES SCRUTINY', 'fails': 'DID NOT SURVIVE', 'none': 'NONE'}
VERDICTS = ('ACCEPT', 'INVESTIGATE', 'REJECT', 'REFERENCE')
MODE_OF_ADDRESS = {'acquisition': 'verify_first', 'validity': 'verify_first', 'scale': 'change_modality',
                   'composition': 'change_modality', 'spatial_extent': 'extend', 'spatial_sampling': 'expand_sampling',
                   'population': 'expand_sampling'}
STEP_OF_VERB = {'REPEAT': 'repeat {e}', 'ZOOM': 'resolve scale', 'EDS': 'chemistry', 'EXTEND': 'extent', 'SECTIONS': 'independent sections',
                'SPACE': 'spaced fields', 'BASELINE': 'expand the reference'}
LIMIT_ORDER = ['scale', 'composition', 'spatial', 'acquisition', 'validity', 'population']
LIMIT_LABEL = {'scale': 'SCALE', 'composition': 'COMPOSITION', 'spatial': 'EXTENT', 'population': 'PREVALENCE',
               'acquisition': 'ACQUISITION', 'validity': 'VALIDITY'}
FAILURE_WORDS = [('acquisition_could_explain', 'acquisition could explain it'), ('spatially_inconsistent', 'inconsistent across fields'),
                 ('moderate_robustness_dimension', 'acquisition-sensitive KPI')]
# words that would overstate what the engine computes (checked in every rendered text)
FORBIDDEN = ('prove', 'proven', 'proves', 'certain', 'certainly', 'impossible', 'guarantee', 'guaranteed', 'validated', 'causes',
             'caused by', 'chemical identity', 'universal', 'universally', 'always', 'hidden variance', 'definitely', 'confirms')
# definitional names of envelope levels may appear in templates; every other digit must come from a referenced value
DEFINITIONAL = ('95% CI', '95%', '99%', 'q95', 'q99')
MAX_SURVIVING, MAX_LIMITS, MAX_STEPS = 2, 5, 5


# ---------------------------------------------------------------- references and values
def ref(collection, id='batch', path=None):
    return {'collection': collection, 'id': id, 'path': path}


def resolve(F, r):
    """Value at a reference, or KeyError. Singletons (decision/context/summary) use id 'batch'."""
    node = F[r['collection']]
    if isinstance(node, list):
        node = next((x for x in node if x.get('id') == r['id']), None)
        if node is None:
            raise KeyError(f"{r['collection']}:{r['id']}")
    for part in (r.get('path') or '').split('.'):
        if part:
            node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def _dim(F, did):
    return next(d for d in F['dimensions'] if d['id'] == did)


def fmt(v, kind):
    if kind == 'str':
        return str(v)
    if kind == 'list':
        return ', '.join(map(str, v))
    if kind == 'int':
        return str(int(round(v)))
    if kind == 'p':
        return f'{v:.3f}'
    if kind == 'g':
        return f'{v:g}'
    if kind == 'f1':
        return f'{v:.1f}'
    if kind == 'f2':
        return f'{v:.2f}'
    if kind == 'z':
        return f'{v:+.1f}'.replace('-', '−')
    if kind == 'pct':
        return f'{100 * v:.0f}%'
    if kind.startswith('kpi:'):
        return f"{v * kind_factor[kind[4:]]:.3g}"
    if kind == 'failure':
        return dict(FAILURE_WORDS)[v]
    raise ValueError(kind)


kind_factor = {}          # dimension id -> display factor, filled per field in build() / check()


def _render(template, values):
    return template.format(*[fmt(v['value'], v['fmt']) for v in values]) if template else None


def _val(F, r, kind):
    return {'ref': r, 'value': resolve(F, r), 'fmt': kind}


# ---------------------------------------------------------------- build
def build(F):
    """decision-brief/1 from one epistemic-field/1 document. Deterministic: same field -> same brief."""
    if F.get('schema_version') != 'epistemic-field/1':
        raise ValueError('decision brief expects epistemic-field/1')
    kind_factor.clear()
    kind_factor.update({d['id']: (d.get('display') or {}).get('factor', 1) for d in F['dimensions']})
    C, D, S = F['context'], F['decision'], F['summary']
    OBS = {o['id']: o for o in F['observations']}
    ENT = {e['id']: e for e in F['entities']}
    RIMS = F['rims']
    ACTS = sorted(F['actions'], key=lambda a: a['rank'])
    claims, suppressed = [], []

    def add(**c):
        c.setdefault('values', [])
        c.setdefault('fact_values', [])
        c.setdefault('details', [])
        c.setdefault('action_refs', [])
        c.setdefault('role', 'content')
        c.setdefault('fact_template', None)
        c['text'] = _render(c['template'], c['values'])
        c['fact'] = _render(c['fact_template'], c['fact_values'])
        for d in c['details']:
            d['text'] = _render(d['template'], d['values'])
        c.setdefault('focus', c['proof_refs'][0])
        if c['kind'] == 'support':
            c['state_label'] = SUPPORT[c['status']]
        claims.append(c)
        return c['id']

    def acts_for(rim_id):
        return [a['id'] for a in ACTS if rim_id in a['triggered_by']]

    batch = ref('context', path='batch')
    verdict = D['verdict']
    pop = next((r for r in RIMS if r['type'] == 'population'), None)

    # ---- DECISION
    tmpl = {'REJECT': '{0} crosses the QC rejection rule.', 'ACCEPT': '{0} stays inside the approved envelope.',
            'INVESTIGATE': '{0}: the rule cannot settle this batch; investigate.', 'REFERENCE': '{0} is the approved reference.'}[verdict]
    add(id='decision.verdict', kind='decision', block='decision', scope=C['batch'], status=verdict, label=verdict,
        template=tmpl, values=[_val(F, batch, 'str')],
        fact_template='batch p = {0} against α = {1}', fact_values=[_val(F, ref('decision', path='p_batch'), 'p'),
                                                                     _val(F, ref('decision', path='thresholds.alpha_reject'), 'g')],
        details=[dict(template='severity test p = {0} · count test p = {1} ({2})',
                      values=[_val(F, ref('decision', path='tests.severity_p'), 'p'), _val(F, ref('decision', path='tests.count_p'), 'p'),
                              _val(F, ref('decision', path='tests.combination'), 'str')])],
        priority=0, group='decision',
        proof_refs=[ref('decision', path='verdict'), ref('decision', path='p_batch'), ref('decision', path='tests'), ref('decision', path='reasons')],
        focus=ref('decision', path='p_batch'))
    scope_vals = [_val(F, ref('context', path='reference'), 'str')]
    scope_t = 'Decision under this dataset only: approved reference {0}'
    if pop:
        scope_vals += [_val(F, ref('rims', pop['id'], 'basis.n_reference_min'), 'int'), _val(F, ref('rims', pop['id'], 'basis.n_reference_max'), 'int')]
        scope_t += ' ({1}–{2} micrographs)'
    scope_vals.append(_val(F, ref('context', path='model'), 'str'))
    add(id='decision.scope', kind='scope', block='decision', scope=C['batch'], status='dataset_scope', label='SCOPE',
        template=scope_t + '; ' + '{%d}.' % (len(scope_vals) - 1), values=scope_vals, priority=9, group='scope',
        proof_refs=[ref('context', path='reference'), ref('context', path='model')] + ([ref('rims', pop['id'], 'basis')] if pop else []))

    # ---- SURVIVING EVIDENCE (decision-consequential evidence; its scrutiny and leverage are merged, not repeated)
    surviving = sorted(S['surviving'], key=lambda o: -OBS[o]['reference_relation']['exceedance_ratio'])
    ev_ids = []
    if S['deviating']:
        ev_ids.append(add(id='evidence.summary', kind='evidence_summary', block='surviving_evidence', scope=C['batch'],
                          status='survives' if surviving else 'fails', label='EVIDENCE', template='{0} of {1} deviations survive scrutiny.',
                          values=[_val(F, ref('summary', path='n_surviving'), 'int'), _val(F, ref('summary', path='n_deviating'), 'int')],
                          priority=1, group='evidence:summary', proof_refs=[ref('summary', path='surviving'), ref('summary', path='deviating')]))
    for k, oid in enumerate(surviving):
        o, e = OBS[oid], ENT[OBS[oid]['entity']]
        d = _dim(F, o['dimension'])
        if k >= MAX_SURVIVING:
            suppressed.append(dict(candidate=f'evidence.{oid}', reason='surviving-evidence cap', cap=MAX_SURVIVING))
            continue
        O = lambda p: ref('observations', oid, p)
        lev = e.get('leverage') or {}
        fact_t, fact_v = '{0} vs approved {1} {2}', [_val(F, O('value'), 'kpi:' + d['id']), _val(F, O('reference_relation.approved_mean'), 'kpi:' + d['id']),
                                                     _val(F, ref('dimensions', d['id'], 'unit'), 'str')]
        if lev.get('flips'):
            fact_t += ' · without {3}: {4} (p = {5})'
            fact_v += [_val(F, ref('entities', e['id'], 'id'), 'str'), _val(F, ref('entities', e['id'], 'leverage.verdict_without'), 'str'),
                       _val(F, ref('entities', e['id'], 'leverage.p_without'), 'p')]
        direction = 'above' if o['reference_relation']['direction'] > 0 else 'below'
        ev_ids.append(add(
            id=f'evidence.{oid}', kind='surviving_evidence', block='surviving_evidence', scope=oid, status='survives',
            label=f"{o['entity']} · {d['short_label']}".upper(),
            template='{0} in {1} is ' + direction + ' the approved envelope and survives scrutiny.',
            values=[_val(F, ref('dimensions', d['id'], 'label'), 'str'), _val(F, O('entity'), 'str')],
            fact_template=fact_t, fact_values=fact_v,
            details=[dict(template='z = {0} against q99 = {1} (status {2})', values=[_val(F, O('reference_relation.z'), 'z'),
                          _val(F, O('reference_relation.q99'), 'f2'), _val(F, O('reference_relation.status'), 'str')]),
                     dict(template='{0} of {1} fields beyond the 95% envelope', values=[_val(F, O('scrutiny.fields_beyond_95'), 'int'), _val(F, O('scrutiny.n_fields'), 'int')]),
                     dict(template='tested acquisition changes explain {0} of the deviation (limit {1})',
                          values=[_val(F, O('scrutiny.acquisition_share'), 'pct'), _val(F, O('scrutiny.acquisition_share_max'), 'pct')]),
                     dict(template='KPI robustness class: {0}', values=[_val(F, ref('dimensions', d['id'], 'robustness.cls'), 'str')])],
            priority=1 if lev.get('flips') else 2, group=f'evidence:{oid}',
            proof_refs=[O('reference_relation'), O('scrutiny'), ref('entities', e['id'], 'leverage'), ref('dimensions', d['id'], 'robustness')],
            focus=O('scrutiny'), action_refs=[a['id'] for a in ACTS if oid in a['targets']['observations'] and a['tier'] == 1]))
        for merged in ('reference_relation', 'scrutiny', 'leverage', 'robustness'):
            suppressed.append(dict(candidate=f'{oid}:{merged}', reason='merged', into=f'evidence.{oid}'))
    failed = [o for o in S['deviating'] if o not in S['surviving']]
    if failed:
        parts, vals = [], []
        for oid in failed:
            o = OBS[oid]
            code = next(c for c, _ in FAILURE_WORDS if c in o['scrutiny']['failed'])
            idx = o['scrutiny']['failed'].index(code)
            vals += [_val(F, ref('observations', oid, 'entity'), 'str'), _val(F, ref('dimensions', o['dimension'], 'short_label'), 'str'),
                     _val(F, ref('observations', oid, f'scrutiny.failed.{idx}'), 'failure')]
            n = len(vals)
            parts.append('{%d} {%d} ({%d})' % (n - 3, n - 2, n - 1))
        ev_ids.append(add(id='evidence.non_surviving', kind='context', block='surviving_evidence', scope=C['batch'], status='fails',
                          label='DID NOT SURVIVE', template='Did not survive: ' + ', '.join(parts) + '.', values=vals, priority=6,
                          group='evidence:non_surviving', proof_refs=[ref('observations', o, 'scrutiny') for o in failed]))
    if not S['deviating']:
        ev_ids.append(add(id='evidence.none', kind='evidence_summary', block='surviving_evidence', scope=C['batch'], status='none', label='NONE',
                          template='{0} of {1} independent micrographs leave the 95% envelope.',
                          values=[_val(F, ref('decision', path='d95'), 'int'), _val(F, ref('decision', path='n_independent'), 'int')],
                          priority=3, group='evidence:summary', proof_refs=[ref('decision', path='d95'), ref('summary', path='deviating')]))

    # ---- LIMITS (consequential rims only; each rim is one group)
    cons = sorted([r for r in RIMS if r['consequential']], key=lambda r: (LIMIT_ORDER.index(r['type']) if r['type'] in LIMIT_ORDER else 99, r['id']))
    for r in RIMS:
        if not r['consequential']:
            suppressed.append(dict(candidate=f"limit.{r['id']}", reason='not consequential (examiner only)'))
    lim_ids = []
    for r in cons[:MAX_LIMITS]:
        R = lambda p: ref('rims', r['id'], p)
        t, v, prf = None, [], [R('statement'), R('basis')]
        if r['type'] == 'scale':
            t, v = 'Excess fine objects peak at the {0} µm detection floor ({1}× approved).', [_val(F, R('basis.detection_floor_um'), 'g'), _val(F, R('basis.peak_ratio_at_floor'), 'f1')]
        elif r['type'] == 'composition':
            t = 'Chemistry of the deviating high-Z phase is not measured; BSE alone cannot identify it.'
            md = f"{r['target']}:{r['basis']['missing_dimension']}"
            prf.append(ref('missing_dimensions', md, 'basis'))
        elif r['type'] == 'spatial' and r['scope'] == 'observation':
            t, v = 'Still outside the approved band at the {0} edge of the {1} µm captured section: extent not bounded.', [_val(F, R('basis.open_edges.0'), 'str'), _val(F, R('basis.captured_length_um'), 'int')]
            prf.append(ref('spatial_profiles', r['target'], 'runs'))
        elif r['type'] == 'population':
            P = 'basis.prevalence.'
            t, v = 'Out-of-family prevalence {0} of {1} independent micrographs (95% CI {2}–{3}).', [
                _val(F, R(P + 'out_of_family'), 'int'), _val(F, R(P + 'n'), 'int'), _val(F, R(P + 'ci95.0'), 'pct'), _val(F, R(P + 'ci95.1'), 'pct')]
        else:
            t, v = '{0}', [_val(F, R('statement'), 'str')]                 # engine statement verbatim
        focus = {'composition': ref('missing_dimensions', f"{r['target']}:composition", 'basis'),
                 'spatial': ref('spatial_profiles', r['target'], 'runs') if r['scope'] == 'observation' else R('basis')}.get(r['type'], R('basis'))
        lim_ids.append(add(id=f"limit.{r['id']}", kind='limit', block='limits', scope=r['target'], status='consequential',
                           label=LIMIT_LABEL.get(r['type'], r['type'].upper()), template=t, values=v, priority=2 + LIMIT_ORDER.index(r['type']) / 10 if r['type'] in LIMIT_ORDER else 3,
                           group=f"rim:{r['id']}", proof_refs=prf, focus=focus, action_refs=acts_for(r['id'])))
    for r in cons[MAX_LIMITS:]:
        suppressed.append(dict(candidate=f"limit.{r['id']}", reason='limits cap', cap=MAX_LIMITS))

    # ---- DATA SUPPORT (sufficiency per question; attribution / prevalence / regime point to Limits, no numbers)
    piv = D['pivotal']
    causes = {ENT[p]['leverage']['cause'] for p in piv if ENT[p].get('leverage')}
    if verdict == 'REFERENCE':
        qc = 'not_applicable'
    elif D['validity_failed']:
        qc = 'reacquire'
    elif verdict == 'INVESTIGATE':
        qc = 'partial'
    elif piv and causes == {'min_independent_count'}:
        qc = 'at_minimum'
    else:
        qc = 'sufficient'
    if qc == 'at_minimum':
        t, v = ("{0} independent incoming micrographs, the rule's minimum: without any one of them the decision becomes {1}.",
                [_val(F, ref('decision', path='n_independent'), 'int'), _val(F, ref('entities', piv[0], 'leverage.verdict_without'), 'str')])
    elif qc == 'reacquire':
        t, v = 'Validity gate failed for {0}.', [_val(F, ref('decision', path='validity_failed'), 'list')]
    elif verdict == 'REJECT':
        t, v = '{0} independent incoming micrographs; outside the 99% envelope and consistent across fields: {1}.', [
            _val(F, ref('decision', path='n_independent'), 'int'), _val(F, ref('decision', path='consistent_out'), 'list')]
    else:
        t, v = '{0} independent incoming micrographs; {1} outside the 95% envelope.', [_val(F, ref('decision', path='n_independent'), 'int'),
                                                                                     _val(F, ref('decision', path='d95'), 'int')]
    sup = [add(id='support.qc', kind='support', block='data_support', scope=C['batch'], status=qc, label='QC DECISION', template=t, values=v,
               priority=1, group='support:qc', proof_refs=[ref('decision', path='n_independent'), ref('decision', path='consistent_out'), ref('decision', path='pivotal'),
                                                         ref('decision', path='reference_linked')] + [ref('entities', p, 'leverage') for p in piv],
               focus=ref('rims', pop['id'], 'basis') if pop else ref('decision', path='n_independent'))]
    surv_ents = {OBS[o]['entity'] for o in surviving}
    attr_rims = [r for r in cons if r['type'] in ('composition', 'scale') and (r['target'] in surv_ents or r['target'] in surviving)]
    if not surviving:
        attr, t = 'not_applicable', 'No surviving deviation to attribute.'
    elif attr_rims:
        attr, t = 'change_modality', 'Attributing the surviving deviation needs a different measurement; see Limits.'
    else:
        attr, t = 'partial', 'Attribution rests on BSE morphology only; see Limits.'
    sup.append(add(id='support.attribution', kind='support', block='data_support', scope=C['batch'], status=attr, label='ATTRIBUTION', template=t,
                   role='pointer', priority=4, group='support:attribution', points_to=[f"limit.{r['id']}" for r in attr_rims],
                   proof_refs=[ref('rims', r['id'], 'consequential') for r in attr_rims] or [ref('summary', path='surviving')]))
    prev = 'expansion_needed' if pop and pop['consequential'] else 'sufficient'
    sup.append(add(id='support.prevalence', kind='support', block='data_support', scope=C['batch'], status=prev, label='LOT PREVALENCE',
                   template='Too few independent sections to estimate lot prevalence usefully; see Limits.' if prev == 'expansion_needed'
                   else 'Population support is not a consequential limit for this decision.', role='pointer', priority=5,
                   group='support:prevalence', points_to=[f"limit.{pop['id']}"] if prev == 'expansion_needed' else [],
                   proof_refs=[ref('rims', pop['id'], 'consequential')] if pop else [ref('decision', path='n_independent')]))
    surv_set = set(surviving)
    sub = {'spatial': 'expansion_needed' if any(r['type'] == 'spatial' and r['scope'] == 'observation' and r['target'] in surv_set for r in cons) else 'no_expansion_justified',
           'scale': 'change_modality' if any(r['type'] == 'scale' and r['target'] in surv_ents for r in cons) else 'no_expansion_justified',
           'acquisition': ('reacquire' if any(ENT[e]['acquisition']['outside_tested_range'] for e in ENT if not ENT[e]['independence']['reference_linked'])
                           else 'partial' if any(a['verb'] == 'REPEAT' and a['tier'] == 1 for a in ACTS) else 'sufficient')}
    words = {'spatial': 'extent', 'scale': 'scale', 'acquisition': 'acquisition'}
    regime = min(sub.values(), key=SUPPORT_ORDER.index)
    sup.append(add(id='support.regime', kind='support', block='data_support', scope=C['batch'], status=regime, label='TESTED REGIME',
                   template=' · '.join(f"{words[k]}: {SUPPORT[s].lower()}" for k, s in sub.items()) + '.', role='pointer', priority=6,
                   group='support:regime', substates=sub,
                   proof_refs=[ref('rims', r['id'], 'consequential') for r in cons if r['type'] in ('spatial', 'scale')] +
                              [ref('entities', e, 'acquisition') for e in sorted(ENT) if not ENT[e]['independence']['reference_linked']],
                   points_to=[f"limit.{r['id']}" for r in cons if r['type'] in ('spatial', 'scale')]))
    support_state = {'reacquire': 'REACQUIRE / INVALID', 'partial': 'PARTIAL FOR QC', 'not_applicable': 'NOT APPLICABLE'}.get(qc, 'SUFFICIENT FOR QC')
    qual = (['AT THE MINIMUM'] if qc == 'at_minimum' else []) + \
           (['NOT FOR ' + ' OR '.join(x for x, s in (('ATTRIBUTION', attr), ('PREVALENCE', prev)) if s not in ('sufficient', 'not_applicable'))]
            if any(s not in ('sufficient', 'not_applicable') for s in (attr, prev)) else [])

    # ---- ACQUISITION POLICY (tier-1 actions in rank order; STOP when nothing justifies more acquisition)
    t1 = [a for a in ACTS if a['tier'] == 1][:MAX_STEPS]
    for a in ACTS:
        if a['tier'] != 1 or a not in t1:
            suppressed.append(dict(candidate=f"action.{a['id']}", reason=f"tier {a['tier']} (examiner only)" if a['tier'] != 1 else 'steps cap'))
    mode = MODE_OF_ADDRESS.get(t1[0]['addresses'], 'expand_sampling') if t1 else ('expand_sampling' if ACTS else 'stop')
    pol = []
    for a in t1:
        A = lambda p: ref('actions', a['id'], p)
        pol.append(add(id=f"action.{a['id']}", kind='action', block='acquisition_policy', scope=','.join(a['targets']['entities']) or C['batch'],
                       status=a['status'], label=a['verb'], template='{0}', values=[_val(F, A('title'), 'str')],
                       step=STEP_OF_VERB.get(a['verb'], a['verb'].lower()).format(e=(a['targets']['entities'] or [''])[0]) + (' (future)' if a['status'] == 'future' else ''),
                       priority=10 + a['rank'], group=f"action:{a['id']}", action_refs=[a['id']],
                       proof_refs=[A('rationale')] + [ref('rims', t, 'basis') for t in a['triggered_by']] + [dict(f) for f in a['trigger_facts']],
                       focus=A('title')))
    if mode == 'stop':
        pol.append(add(id='action.stop', kind='action', block='acquisition_policy', scope=C['batch'], status='no_expansion_justified', label='STOP',
                       template='No current observation justifies more acquisition of this kind for this decision.', priority=10,
                       group='action:stop', proof_refs=[ref('summary', path='consequential_rims')], focus=ref('summary', path='consequential_rims')))
    sequence = ' → '.join(next(c['step'] for c in claims if c['id'] == i) for i in pol) if mode != 'stop' else None
    if sequence:
        sequence = sequence[0].upper() + sequence[1:]

    hero = {
        'decision': dict(state=verdict, claims=['decision.verdict'], footer='decision.scope'),
        'data_support': dict(state=support_state, qualifier=' · '.join(qual) or None, claims=sup),
        'surviving_evidence': dict(state=(claims[[c['id'] for c in claims].index(ev_ids[1])]['label'] if surviving else
                                          'NONE SURVIVES' if S['deviating'] else 'NO DEVIATION'), claims=ev_ids),
        'limits': dict(state=' · '.join(next(c['label'] for c in claims if c['id'] == i) for i in lim_ids) or 'NONE CONSEQUENTIAL', claims=lim_ids),
        'acquisition_policy': dict(state=POLICY[mode], mode=mode, sequence=sequence, claims=pol,
                                   later=[dict(action=a['id'], step=STEP_OF_VERB.get(a['verb'], a['verb'].lower()).format(e=(a['targets']['entities'] or [''])[0]),
                                               tier=a['tier']) for a in ACTS if a not in t1]),
    }
    return dict(schema_version=SCHEMA_VERSION,
                source=dict(schema_version=F['schema_version'], batch=C['batch'], reference=C['reference']),
                hero=hero, claims=claims,
                governance=dict(rules=GOVERNANCE_RULES, suppressed=suppressed))


GOVERNANCE_RULES = [
    'one content claim per redundancy group; pointer claims refer to another block and carry no numbers',
    'decision-consequential evidence first (surviving deviations, ordered by exceedance; scrutiny, leverage and '
    'robustness facts are merged into the evidence claim)',
    'limits = consequential rims only, ordered scale, composition, spatial, acquisition, validity, population',
    'acquisition policy = tier-1 actions in rank order; lower tiers listed, not narrated; STOP when no action exists',
    'states come from explicit engine flags; the wording template is chosen by the state',
]


def compose(brief, compositor=None):
    """Seam for an optional phrasing compositor. Without one, the deterministic brief is returned unchanged. A
    compositor may only rewrite `text` of content claims; the result is accepted only if check() still passes."""
    if compositor is None:
        return brief
    out = compositor(copy.deepcopy(brief))
    return out


# ---------------------------------------------------------------- coherence
def check(brief, F):
    """Violations of the decision-brief contract against its source field (empty list = coherent)."""
    bad = []
    kind_factor.clear()
    kind_factor.update({d['id']: (d.get('display') or {}).get('factor', 1) for d in F['dimensions']})
    if brief.get('schema_version') != SCHEMA_VERSION:
        bad.append('schema_version')
    if brief['source']['batch'] != F['context']['batch']:
        bad.append('brief and field describe different batches')
    by_id = {c['id']: c for c in brief['claims']}
    action_ids = {a['id'] for a in F['actions']}

    def ok_ref(r, where):
        try:
            resolve(F, r)
            return True
        except (KeyError, IndexError, TypeError, ValueError):
            bad.append(f'{where}: unresolved ref {r}')
            return False

    for c in brief['claims']:
        cid = c['id']
        if not c['proof_refs']:
            bad.append(f'{cid}: no proof_refs')
        for r in c['proof_refs']:
            ok_ref(r, cid)
        ok_ref(c['focus'], cid + ' focus')
        for a in c['action_refs']:
            if a not in action_ids:
                bad.append(f'{cid}: unknown action {a}')
        for part, tmpl, vals in [('text', c['template'], c['values']), ('fact', c['fact_template'], c['fact_values'])] + \
                                [(f'detail{i}', d['template'], d['values']) for i, d in enumerate(c['details'])]:
            for v in vals:
                if ok_ref(v['ref'], cid) and not _same(resolve(F, v['ref']), v['value']):
                    bad.append(f'{cid}.{part}: value differs from the field at {v["ref"]}')
            rendered = _render(tmpl, vals)
            current = c[part] if part in ('text', 'fact') else c['details'][int(part[6:])]['text']
            if rendered != current:
                bad.append(f'{cid}.{part}: text is not the rendering of its template and field values')
            bare = re.sub(r'\{\d+\}', '', tmpl or '')
            for tok in DEFINITIONAL:
                bare = bare.replace(tok, '')
            if re.search(r'\d', bare):
                bad.append(f'{cid}.{part}: number written into the template instead of referenced')
        if c['role'] == 'pointer' and (any(isinstance(v['value'], (int, float)) for v in c['values']) or re.search(r'\d', c['text'])):
            bad.append(f'{cid}: pointer claim carries a number')
        low = ' '.join(x for x in [c['text'], c.get('fact') or ''] + [d['text'] for d in c['details']]).lower()
        for w in FORBIDDEN:
            if re.search(r'\b' + re.escape(w) + r'\b', low):
                bad.append(f'{cid}: overstating word "{w}"')
        if c['kind'] == 'support' and c['status'] not in SUPPORT:
            bad.append(f'{cid}: unknown support status {c["status"]}')
        if c['kind'] == 'surviving_evidence':
            o = next((x for x in F['observations'] if x['id'] == c['scope']), None)
            if not o or o['scrutiny']['outcome'] != 'survives' or c['scope'] not in F['summary']['surviving']:
                bad.append(f'{cid}: claims survival that the field does not record')
        if c['kind'] == 'limit':
            rim = next((r for r in F['rims'] if f"limit.{r['id']}" == cid), None)
            if not rim or not rim['consequential']:
                bad.append(f'{cid}: limit is not a consequential rim')
        for p in c.get('points_to', []):
            if p not in by_id:
                bad.append(f'{cid}: points to missing claim {p}')
    hero = brief['hero']
    seen = {}
    for block, h in hero.items():
        if not h['claims']:
            bad.append(f'hero.{block}: empty')
        for cid in h['claims'] + ([h['footer']] if h.get('footer') else []):
            if cid not in by_id:
                bad.append(f'hero.{block}: orphan claim {cid}')
                continue
            c = by_id[cid]
            if c['role'] == 'content':
                if c['group'] in seen:
                    bad.append(f'hero: redundancy group {c["group"]} selected twice ({seen[c["group"]]}, {cid})')
                seen[c['group']] = cid
    if hero['decision']['state'] != F['decision']['verdict']:
        bad.append('hero decision state differs from the field verdict')
    if by_id.get('decision.verdict', {}).get('status') != F['decision']['verdict']:
        bad.append('decision claim status differs from the field verdict')
    return bad


def _same(a, b):
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) <= 1e-9 * max(1, abs(a))
    return a == b


def write(F, path):
    b = build(F)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(b, fh, indent=1, ensure_ascii=False)
    return b
