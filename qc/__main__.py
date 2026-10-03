"""CLI.  python -m qc reference data/Batch_1      (build approved-baseline reference)
        python -m qc assess data/Batch_3 [...]     (verdict + report for incoming batches)"""
import argparse
import json

from . import pipeline


def show(res):
    d = res['decision']
    print(f"\n=== {res['batch']}: {d['verdict']}  (batch p = {d['p_batch']:.3f}; {d['n_micrographs']} micrographs from {res['n_fields']} fields)")
    for r in d['reasons']:
        print('  -', r)
    for t in res['explanations']:
        if t['status'] in ('deviant', 'out') or t['gate']:
            print(f"  * {t['headline']}  [{t['status']}]  linked batches: {', '.join(t['links']) or '-'}")
            for f in t['findings']:
                print('      ', f)
            for i in t['interpretation']:
                print('       => ', i)
            for g in t['gate']:
                print('       gate:', g)
            if t['acquisition']:
                print('       acquisition differs:', '; '.join(t['acquisition']))


def main():
    ap = argparse.ArgumentParser(prog='qc')
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('reference')
    a.add_argument('baseline')
    a.add_argument('--noise-from', nargs='*', default=[])
    c = sub.add_parser('fixture')
    c.add_argument('report_dir')
    c.add_argument('--out', default='fixtures')
    b = sub.add_parser('assess')
    b.add_argument('batches', nargs='+')
    for p in (a, b):
        p.add_argument('--workers', type=int, default=None)
    args = ap.parse_args()
    if args.cmd == 'fixture':
        from . import contract
        path = contract.export_fixture(args.report_dir, args.out)
        bad = contract.check(json.load(open(path, encoding='utf-8')))
        print(path, 'coherent' if not bad else f'{len(bad)} violations: ' + '; '.join(bad[:5]))
        return
    if args.cmd == 'reference':
        ref = pipeline.build_reference(args.baseline, args.noise_from, args.workers)
        print(f"reference '{ref['name']}': {len(ref['micrographs'])} micrographs")
        for k, v in ref['kpi'].items():
            print(f"  {k:20s} mean {v['mean']:.4g} sd_between {v['sd_between']:.3g} sd_tile {v['sd_within_tile']:.3g} n {v['n']} "
                  f"95% PI(3 tiles) {v['pi95_m3'][0]:.4g}-{v['pi95_m3'][1]:.4g} excl {v['excluded']}")
        for s in ref['self_audit']:
            print(f"  self-audit {s['parent']}: {s['status']} (max|t| {s['max_t']:.2f}) {'; '.join(s['gate_reasons'])}")
    else:
        for bd in args.batches:
            show(pipeline.assess(bd, args.workers))


if __name__ == '__main__':
    main()
