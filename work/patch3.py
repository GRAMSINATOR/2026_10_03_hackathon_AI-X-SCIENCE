p = 'qc/pipeline.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""    ref = stats.build_reference(mgs, os.path.basename(os.path.normpath(baseline_dir)), sw)
    json.dump(_clean(ref), open(REF_PATH, 'w'), indent=1)""", """    ref = stats.build_reference(mgs, os.path.basename(os.path.normpath(baseline_dir)), sw)
    from .io import discover
    from . import robustness
    fields = [f for f in discover(baseline_dir) if 'BSE' in f['channels']][:3]
    with Pool(min(12, (os.cpu_count() or 4) - 2)) as P:
        ref['robustness'] = robustness.card([f['channels']['BSE'] for f in fields], P)
    json.dump(_clean(ref), open(REF_PATH, 'w'), indent=1)""")
s = s.replace("""    ref = ref or json.load(open(REF_PATH))
    recs = process_folder(batch_dir, workers)
    batch = recs[0]['batch']""", """    ref = ref or json.load(open(REF_PATH))
    recs = process_folder(batch_dir, workers)
    batch = recs[0]['batch']
    is_ref = batch == ref['name']""")
s = s.replace("""    decision = stats.decide(mgs, ref)""", """    decision = stats.decide(mgs, ref)
    if is_ref:
        decision.update(verdict='REFERENCE', reasons=['approved baseline: self-audit (leave-one-micrograph-out) shown per micrograph.']
                        + [f"{a['parent']}: {a['status']} (max |t| {a['max_t']:.1f}) {'; '.join(a['gate_reasons'])}" for a in ref['self_audit']])""")
open(p, 'w', encoding='utf-8').write(s)
