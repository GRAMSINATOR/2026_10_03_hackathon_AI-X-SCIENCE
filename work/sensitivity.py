"""Verdict sensitivity: does the Batch 2 / Batch 3 decision survive analysis choices?
Each variant runs in an isolated cache (fields, reference, reports)."""
import json
import os
import subprocess
import sys

PY = sys.executable
VARIANTS = {
    'noise_from_B1B2_only': (dict(), ['data/Batch_2']),
    'f_bright_0.4': (dict(QC_FBRIGHT='0.4'), ['data/Batch_2', 'data/Batch_3']),
    'f_bright_0.6': (dict(QC_FBRIGHT='0.6'), ['data/Batch_2', 'data/Batch_3']),
    'f_pore_0.4': (dict(QC_FPORE='0.4'), ['data/Batch_2', 'data/Batch_3']),
    'f_pore_0.6': (dict(QC_FPORE='0.6'), ['data/Batch_2', 'data/Batch_3']),
}
rows = {}
for name, (extra, noise) in VARIANTS.items():
    root = f'cache/sens/{name}'
    env = dict(os.environ, QC_CACHE=f'{root}/fields', QC_REF=f'{root}/reference.json', QC_REPORTS=f'{root}/reports', **extra)
    subprocess.run([PY, '-m', 'qc', 'reference', 'data/Batch_1', '--noise-from', *noise], env=env, capture_output=True, text=True, check=True)
    subprocess.run([PY, '-m', 'qc', 'assess', 'data/Batch_2', 'data/Batch_3'], env=env, capture_output=True, text=True, check=True)
    out = {}
    for b in ('Batch_2', 'Batch_3'):
        r = json.load(open(f'{root}/reports/{b}/result.json'))
        d = r['decision']
        flagged = {m['parent']: m['status'] for m in r['micrographs'] if m['status'] in ('deviant', 'out')}
        out[b] = dict(verdict=d['verdict'], p=round(d['p_batch'], 4), d99=d['d99'], d95=d['d95'], flagged=flagged)
    rows[name] = out
    print(name, json.dumps(out), flush=True)
json.dump(rows, open('cache/sens/summary.json', 'w'), indent=1)
