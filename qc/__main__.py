"""CLI.  python -m qc reference data/Batch_1      (build approved-baseline reference)
        python -m qc assess data/Batch_3 [...]     (verdict + report for incoming batches)"""
import argparse
import json
import os

from . import pipeline


def show(res):
    d = res['decision']
    if d['verdict'] == 'REFERENCE':   # a role, not a verdict
        print(f"\n=== {res['batch']}: REFERENCE self-audit (no QC verdict; {d['n_micrographs']} parent micrographs, each against the other "
              f"{d['n_micrographs'] - 1}; {res['n_fields']} fields)")
    else:
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
    rf = sub.add_parser('references', help='build and cache explicit candidate reference frames')
    rf.add_argument('batches', nargs='+')
    rf.add_argument('--activate', default=None)
    rf.add_argument('--workers', type=int, default=None)
    c = sub.add_parser('fixture')
    c.add_argument('report_dir')
    c.add_argument('--out', default='fixtures')
    b = sub.add_parser('assess')
    b.add_argument('batches', nargs='+')
    b.add_argument('--reference', default=None, help='cached frame name or reference artifact path')
    cr = sub.add_parser('compare-references', help='evaluate one unchanged target across eligible reference frames')
    cr.add_argument('batch')
    cr.add_argument('--references', nargs='*', default=None)
    cr.add_argument('--active', default=None)
    cr.add_argument('--workers', type=int, default=None)
    for p in (a, b):
        p.add_argument('--workers', type=int, default=None)
    pv = sub.add_parser('provenance', help='export the tile -> parent micrograph map (derived numbers only)')
    pv.add_argument('--out', default=pipeline.REPORTS)
    bu = sub.add_parser('bundle', help='export an image-free derived bundle for public hosting')
    bu.add_argument('out')
    bu.add_argument('--batches', nargs='*', default=None)
    args = ap.parse_args()
    if args.cmd == 'references':
        doc = pipeline.build_reference_frames(args.batches, args.workers, args.activate)
        for f in doc['frames']:
            print(f"{f['id']}: {'ELIGIBLE' if f['eligible'] else 'UNAVAILABLE'} · {f['support_quality']} · "
                  f"{f['support']['n_parent_micrographs']} parents"
                  + ('' if f['eligible'] else ' · ' + '; '.join(f['unavailable_reasons'])))
        return
    if args.cmd == 'compare-references':
        s = pipeline.compare_references(args.batch, args.references, args.workers, args.active)
        print(f"{os.path.basename(os.path.normpath(args.batch))}: {s['conclusion']} across {', '.join(s['frames_evaluated'])}; "
              f"{len(s['frame_dependent_findings'])} frame-dependent findings")
        return
    if args.cmd == 'provenance':
        from . import provmap
        doc = provmap.export(args.out)
        linked = [p for p, v in doc['parents'].items() if v['in_approved_reference']]
        print(f"{doc['n_tiles']} tiles -> {doc['n_parents']} parent micrographs ({len(linked)} approved) -> "
              f"{os.path.join(args.out, 'provenance_map.csv')} / .json")
        return
    if args.cmd == 'bundle':
        from . import bundle
        r = bundle.export(args.out, args.batches)
        print(f"image-free bundle: {r['out']} ({', '.join(r['batches'])}); check passed")
        return
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
            show(pipeline.assess(bd, args.workers, ref=args.reference))


if __name__ == '__main__':
    main()
