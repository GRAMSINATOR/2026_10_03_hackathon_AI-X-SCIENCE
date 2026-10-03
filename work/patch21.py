p = 'qc/explain.py'; s = open(p, encoding='utf-8').read()
old = s[s.index("def acquisition_notes(m, ref, envelope='acq_envelope', label='baseline'):"):s.index("def micrograph_text(")]
new = '''def acquisition_deviations(m, ref, envelope='acq_envelope'):
    """Structured: acquisition metrics of micrograph m outside an envelope (approved micrographs, or the tested range)."""
    out = []
    for a in ACQ:
        if a not in ref.get(envelope, {}):
            continue
        lo, hi = ref[envelope][a]
        v = m['acq'][a]
        tol = max(ACQ_TOL.get(a, 0.0), 0.15 * (hi - lo))
        if v < lo - tol or v > hi + tol:
            out.append(dict(metric=a, label=ACQ_LABEL[a], value=float(v), lo=float(lo), hi=float(hi), tolerance=float(tol)))
    return out


def acquisition_notes(m, ref, envelope='acq_envelope', label='baseline'):
    """Human-readable form of acquisition_deviations."""
    return [f"{d['label']} {d['value']:.3g} ({label} {d['lo']:.3g}–{d['hi']:.3g})" for d in acquisition_deviations(m, ref, envelope)]


'''
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
