p = 'qc/field.py'; s = open(p, encoding='utf-8').read()
# 1) profile: valid windows only
s = s.replace("""        rv = np.array(rv)
        sm = np.convolve(rv, np.ones(BAND_COLS) / BAND_COLS, mode='same') if len(rv) >= BAND_COLS else rv
        outside = (sm > band['hi']) if direction > 0 else (sm < band['lo'])
        out_runs.append(dict(x=rx, v=rv.tolist(), smooth=sm.tolist(), open_left=bool(len(sm) and outside[min(1, len(sm) - 1)]),
                             open_right=bool(len(sm) and outside[max(len(sm) - 2, 0)]), frac_outside=float(outside.mean()) if len(sm) else 0.0))""",
"""        rv, rx = np.array(rv), np.array(rx)
        if len(rv) >= BAND_COLS:   # 100-um windows fully inside the captured section (no padding at the edges)
            sm = np.convolve(rv, np.ones(BAND_COLS) / BAND_COLS, mode='valid')
            sx = np.convolve(rx, np.ones(BAND_COLS) / BAND_COLS, mode='valid')
        else:
            sm, sx = rv, rx
        outside = (sm > band['hi']) if direction > 0 else (sm < band['lo'])
        out_runs.append(dict(x=rx.tolist(), v=rv.tolist(), sx=sx.tolist(), smooth=sm.tolist(),
                             open_left=bool(len(sm) and outside[0]), open_right=bool(len(sm) and outside[-1]),
                             frac_outside=float(outside.mean()) if len(sm) else 0.0))""")
# 2) acquisition: differs (approved envelope) vs untested (outside tested range)
s = s.replace("""        acq = acquisition_notes(m, ref)
        lev = m.get('leverage')""", """        acq = acquisition_notes(m, ref)                                      # differs from approved micrographs
        untested = acquisition_notes(m, ref, 'acq_tested', 'tested') if 'acq_tested' in ref else acq   # beyond what was measured
        lev = m.get('leverage')""")
s = s.replace("""                   leverage=lev, pivotal=bool(lev and lev['flips']), gate=m['gate_reasons'], acq_outside=acq,""",
              """                   leverage=lev, pivotal=bool(lev and lev['flips']), gate=m['gate_reasons'], acq_outside=acq, acq_untested=untested,""")
s = s.replace("""                c['survives'] = not fails
                c['rules'] += ([f'survives: robust KPI, tile-consistent, acquisition explains {100 * (acq_share or 0):.0f}%'] if not fails
                               else ['fails scrutiny: ' + '; '.join(fails)])""", """                c['survives'] = not fails
                c['conditional'] = bool(not fails and untested)
                c['rules'] += ([f'survives: robust KPI, tile-consistent, tested acquisition changes explain {100 * (acq_share or 0):.0f}%'
                                + (' - conditional: this micrograph was acquired outside the tested acquisition range' if untested else '')]
                               if not fails else ['fails scrutiny: ' + '; '.join(fails)])""")
s = s.replace("""            c['acq_sensitive'] = bool(acq and (rr >= SENSITIVE_RATIO or (deviating and acq_share is not None and acq_share >= ACQ_SHARE_MAX)))
            if c['acq_sensitive']:
                c['rules'].append(f'acquisition outside approved envelope ({len(acq)} metrics) and KPI moves {rr:.1f} tile-SD under tested acquisition changes')""",
"""            explained = bool(deviating and acq_share is not None and acq_share >= ACQ_SHARE_MAX)
            c['acq_sensitive'] = bool(untested) or explained
            if untested:
                c['rules'].append('acquisition outside the range whose effect was tested: ' + '; '.join(untested))
            if explained:
                c['rules'].append(f'tested acquisition changes could explain {100 * acq_share:.0f}% of this deviation')""")
s = s.replace("""        if acq:
            rims.append(dict(type='acquisition', scope='micrograph', target=pid, consequential=row['pivotal'],
                             text='acquisition outside approved envelope: ' + '; '.join(acq)))""", """        if untested:
            rims.append(dict(type='acquisition', scope='micrograph', target=pid, consequential=row['pivotal'],
                             text='acquired outside the tested acquisition range (sensitivity bounds do not apply): ' + '; '.join(untested)))""")
# 3) baseline effect: KPIs that matter for current evidence first
s = s.replace("""    worst = sorted([c for c in cols if c.get('measured')], key=lambda c: -c['mdc95'] / max(abs(ref['kpi'][c['kpi']]['mean']), 1e-12))[:3]""",
"""    hot = [k for r in rows for k in KPIS if cells[r['parent']][k].get('deviating')]
    worst = sorted([c for c in cols if c.get('measured')], key=lambda c: (c['kpi'] not in hot, c['cls'] != 'robust'))[:3]""")
open(p, 'w', encoding='utf-8').write(s)
print('ok', s.count('untested'))
