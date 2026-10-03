p = 'qc/pipeline.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""    open(os.path.join(REPORTS, batch, 'evidence_field.html'), 'w', encoding='utf-8').write(hero.render(_clean(res['field']), ref['name']))""",
"""    # representation boundary: the contract is written first; the V1 renderer reads only that JSON
    fpath = os.path.join(REPORTS, batch, 'field.json')
    json.dump(_clean(res['field']), open(fpath, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    open(os.path.join(REPORTS, batch, 'evidence_field.html'), 'w', encoding='utf-8').write(
        hero.render(json.load(open(fpath, encoding='utf-8'))))""")
open(p, 'w', encoding='utf-8').write(s)
p = 'qc/__main__.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""    b = sub.add_parser('assess')""", """    c = sub.add_parser('fixture')
    c.add_argument('report_dir')
    c.add_argument('--out', default='fixtures')
    b = sub.add_parser('assess')""")
s = s.replace("""    for p in (a, b):
        p.add_argument('--workers', type=int, default=None)
    args = ap.parse_args()""", """    for p in (a, b):
        p.add_argument('--workers', type=int, default=None)
    args = ap.parse_args()
    if args.cmd == 'fixture':
        from . import contract
        path = contract.export_fixture(args.report_dir, args.out)
        bad = contract.check(json.load(open(path, encoding='utf-8')))
        print(path, 'coherent' if not bad else f'{len(bad)} violations: ' + '; '.join(bad[:5]))
        return""")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
