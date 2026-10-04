"""Generate CURRENT vs CANDIDATE spatial-statistics QA figures and an auditable JSON summary."""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


ROOT = os.path.dirname(os.path.dirname(__file__))
OUT = os.path.join(ROOT, 'work', 'viz')


def read(path):
    return json.load(open(os.path.join(ROOT, path), encoding='utf-8'))


def scale_rows(ref, marker):
    return ref['spatial'][marker]['scale_dependent_heterogeneity']


def profile(field, pid):
    return next(p for p in field['spatial_profiles'] if p['id'] == pid)


def main():
    os.makedirs(OUT, exist_ok=True)
    ref, b2, b3 = read('cache/reference.json'), read('fixtures/epistemic_field.Batch_2.json'), read('fixtures/epistemic_field.Batch_3.json')

    fig, ax = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    for marker, title, panel in (
        ('porosity', 'Porosity · phase-fraction heterogeneity', ax[0, 0]),
        ('additive_area_frac', 'High-Z area · phase-fraction heterogeneity', ax[0, 1]),
    ):
        rows = scale_rows(ref, marker)
        x = np.array([r['window_um'] for r in rows])
        panel.loglog(x, [r['raw_variance']['current_equal_field'] for r in rows], 'o-', label='CURRENT · equal-field raw variance')
        panel.loglog(x, [r['raw_variance']['parent_equal'] for r in rows], 's--', label='CANDIDATE · parent-equal raw variance')
        twin = panel.twinx()
        twin.semilogx(x, [r['normalized_fluctuation']['parent_equal'] for r in rows], 'D-', color='#e07a22', label='CANDIDATE · variance / p(1−p)')
        panel.set_title(title); panel.set_xlabel('square-window side (µm)'); panel.set_ylabel('raw variance')
        panel.set_xticks(x, [str(int(v)) for v in x]); panel.minorticks_off()
        twin.set_ylabel('normalised fluctuation', color='#e07a22')
        panel.grid(alpha=.2); panel.legend(loc='lower left', fontsize=8); twin.legend(loc='upper right', fontsize=8)
        for r in rows:
            panel.annotate(f"{r['n_windows']}w/{r['n_parents']}p", (r['window_um'], r['raw_variance']['parent_equal']), fontsize=7)

    rows = scale_rows(ref, 'additive_density'); x = np.array([r['window_um'] for r in rows])
    panel = ax[1, 0]
    panel.loglog(x, [r['number_variance']['current_equal_field'] for r in rows], 'o-', label='CURRENT · density variance converted to counts')
    panel.loglog(x, [r['number_variance']['parent_equal'] for r in rows], 's--', label='CANDIDATE · parent-equal number variance')
    twin = panel.twinx(); twin.semilogx(x, [r['fano'] for r in rows], 'D-', color='#e07a22', label='CANDIDATE · Fano')
    twin.axhline(1, color='#777', lw=1, ls=':', label='Poisson comparator')
    panel.set_title('High-Z density · spatial count heterogeneity'); panel.set_xlabel('square-window side (µm)')
    panel.set_xticks(x, [str(int(v)) for v in x]); panel.minorticks_off()
    panel.set_ylabel('number variance'); twin.set_ylabel('Fano', color='#e07a22'); panel.grid(alpha=.2)
    panel.legend(loc='upper left', fontsize=8); twin.legend(loc='lower right', fontsize=8)

    panel = ax[1, 1]
    markers = ['porosity', 'additive_area_frac', 'additive_density']
    current = [ref['spatial'][m]['scale_model_sensitivity']['operational_unweighted_beta'] for m in markers]
    weighted = [ref['spatial'][m]['scale_model_sensitivity']['support_weighted_beta'] for m in markers]
    parent = [ref['spatial'][m]['scale_model_sensitivity']['parent_bootstrap']['median'] for m in markers]
    xx = np.arange(len(markers)); w = .25
    panel.bar(xx - w, current, w, label='CURRENT · unweighted')
    panel.bar(xx, weighted, w, label='CANDIDATE · support-weighted')
    panel.bar(xx + w, parent, w, label='CANDIDATE · parent bootstrap')
    for i, m in enumerate(markers):
        lo, hi = ref['spatial'][m]['scale_model_sensitivity']['parent_bootstrap']['interval95']
        panel.plot([xx[i] + w] * 2, [lo, hi], color='#222', lw=1.4)
    panel.set_xticks(xx, ['porosity', 'high-Z area', 'high-Z count']); panel.set_ylabel('β in Var ~ Area^β')
    panel.set_title('Scale-model sensitivity (descriptor only)'); panel.grid(axis='y', alpha=.2); panel.legend(fontsize=8)
    fig.savefig(os.path.join(OUT, 'spatial_upgrade_current_candidate.png'), dpi=180)
    plt.close(fig)

    cases = [('M2060:additive_density', 'M2060 · high-Z particle density'), ('M2088:porosity', 'M2088 · porosity')]
    fig, axes = plt.subplots(len(cases), 1, figsize=(12, 7), constrained_layout=True)
    extremes = []
    for panel, (pid, title) in zip(axes, cases):
        p, offset = profile(b3, pid), 0
        band = p['reference_band']
        panel.axhspan(band['audit_population_spread']['lo'], band['audit_population_spread']['hi'], color='#aaa', alpha=.16,
                      label='CURRENT · flattened mean ± 1.96 window SD')
        panel.axhspan(band['lo'], band['hi'], color='#7057c7', alpha=.18,
                      label=f"CANDIDATE · parent-bootstrap envelope ({band['n_parents']} parents; descriptive)")
        for i, run in enumerate(p['runs']):
            if i: offset += 60
            cx = np.asarray(run['column_centres_um']) + offset
            wx = np.asarray(run['window_centres_um']) + offset
            panel.scatter(cx, run['column_values'], s=12, color='#777', alpha=.55, label='25 µm columns · context' if i == 0 else None)
            panel.plot(wx, run['window_means'], lw=2.2, color='#e07022', label='100 µm local means · compared' if i == 0 else None)
            offset += run['length_um']
        w = p['whole_profile_excursion']
        panel.set_title(f"{title} · max excursion {w['max_standardized_excursion']:.2f} vs length-matched reference {w['approved_parent_maximum']:.2f}")
        panel.set_xlabel('registered captured distance (µm; gaps shown as 60 µm display spaces)'); panel.grid(alpha=.2)
        panel.legend(fontsize=8, loc='upper right')
        extremes.append(dict(profile=pid, column_um=p['column_um'], compared_window_um=p['window_um'],
                             n_reference_parents=band['n_parents'], envelope=[band['lo'], band['hi']],
                             old_population_spread=[band['audit_population_spread']['lo'], band['audit_population_spread']['hi']],
                             whole_profile=w))
    fig.savefig(os.path.join(OUT, 'spatial_extreme_profiles.png'), dpi=180)
    plt.close(fig)

    audit = dict(
        semantics=dict(raw_columns='25-um full-height columns, context only', compared_trace='unsmoothed 100-um moving local means',
                       reference='descriptive parent-cluster bootstrap quantile envelope', decision_driving=False),
        verdicts={'Batch_2': b2['decision']['verdict'], 'Batch_3': b3['decision']['verdict']},
        bands={k: {x: v[x] for x in ('kind', 'statistic', 'window_um', 'n_windows', 'n_fields', 'n_parents', 'calibrated', 'small_parent_support')}
               for k, v in ref['band'].items()},
        beta_sensitivity={k: ref['spatial'][k]['scale_model_sensitivity'] for k in ref['spatial']},
        extreme_profiles=extremes,
        figures=['spatial_upgrade_current_candidate.png', 'spatial_extreme_profiles.png'])
    json.dump(audit, open(os.path.join(OUT, 'spatial_upgrade_audit.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
