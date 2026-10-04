"""Agentic Marker Frontier visual QA. usage: qa_frontier.py [base_url] [scenario ...]
Standalone preview needs `npm run dev -- --port 5199` in renderer/. Scenario 'integrated' renders the built instrument
(renderer/dist) with the frontier injected exactly as the host does (qc.frontier.inject)."""
import copy, json, os, sys, time, pathlib
sys.path.insert(0, os.getcwd())
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith('http') else 'http://127.0.0.1:5199'
ARGS = [a for a in sys.argv[1:] if not a.startswith('http')]
OUT = 'work/viz'
# name: (query, viewport width, steps, clip selector)
SCEN = {
    'overview': ('', 1600, [], '.mf'),
    'current_frontier': ('', 1600, [], '.mf-frontier'),
    'current_data': ('', 1600, [], '.mf-candidates'),
    'attractors': ('', 1600, [], '.mf-observe'),
    'overview_example': ('?frontier=marker_frontier.example.json', 1600, [], '.mf'),
    'tray_qualitative': ('', 1600, ["__frontier.open('marker', 'marker:open_edge_persistence')"], None),
    'tray_quantitative': ('', 1600, ["__frontier.open('marker', 'marker:spatial_correlation_length')"], None),
    'tray_new_observability': ('', 1600, ["__frontier.open('marker', 'marker:phase_conditioned_fines_distribution')"], None),
    'tray_capability': ('', 1600, ["__frontier.open('capability', 'capability:eds')"], None),
    'tray_capability_example': ('?frontier=marker_frontier.example.json', 1600, ["__frontier.open('capability', 'capability:eds')"], None),
    'tray_deprioritized': ('', 1600, ["__frontier.open('marker', 'marker:latent_progression')"], None),
    'sparse': ('?frontier=marker_frontier.sparse.json', 1600, [], '.mf'),
    'narrow': ('', 820, [], '.mf'),
    'batch2': ('?fixture=epistemic_field.Batch_2.json', 1600, [], '.mf'),
}
names = [a for a in ARGS if a in SCEN or a == 'integrated'] or list(SCEN)
os.makedirs(OUT, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    for n in names:
        if n == 'integrated':
            from qc import brief, frontier, instrument
            F = json.load(open('fixtures/epistemic_field.Batch_3.json', encoding='utf-8'))
            doc = json.load(open('fixtures/marker_frontier.json', encoding='utf-8'))
            html = frontier.inject(instrument.render(F, asset_dir='fixtures/assets', brief=brief.build(F)), doc)
            path = pathlib.Path('work/instrument_frontier_Batch_3.html'); path.write_text(html, encoding='utf-8')
            pg = b.new_page(viewport={'width': 1920, 'height': 1080}); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            pg.goto(path.resolve().as_uri()); pg.wait_for_selector('.mf', timeout=60000); time.sleep(2)
            pg.locator('.mf').screenshot(path=f'{OUT}/frontier_integrated.png')
            chip = pg.locator('.mf-bs.go').first
            if chip.count():
                chip.click(); time.sleep(1.2)
                pg.screenshot(path=f'{OUT}/frontier_integrated_trace.png')
                print('trace chip ->', pg.evaluate("document.querySelector('.px-trace .tr-claim')?.textContent"))
            print(n, 'errors:', errs[:3]); pg.close(); continue
        q, w, steps, sel = SCEN[n]
        pg = b.new_page(viewport={'width': w, 'height': 1000}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        if n == 'sparse':
            sparse = copy.deepcopy(json.load(open('fixtures/marker_frontier.json', encoding='utf-8')))
            sparse.update(markers=[], capabilities=[], papers=[], records=[], reviews=[],
                          lanes={'current_capture': [], 'new_capability': []})
            sparse['opportunity_map'].update(current_frontier=[], tooling_attractors=[])
            sparse['opportunity_map']['candidate_markers'] = {
                'computable_now': [], 'needs_targeted_capture': [], 'requires_new_observability': [], 'set_aside': []}
            for step in sparse['opportunity_map']['roadmap']:
                step['marker_refs'] = []
                step['capability_refs'] = []
            sparse['opportunity_map']['roadmap'] = []
            pg.route('**/marker_frontier.sparse.json', lambda route: route.fulfill(
                status=200, content_type='application/json', body=json.dumps(sparse)))
        pg.emulate_media(reduced_motion='reduce')     # deterministic frames (the sheen is decorative)
        pg.goto(BASE + '/frontier.html' + q); pg.wait_for_selector('.mf', timeout=30000); time.sleep(0.8)
        for s in steps:
            pg.evaluate(s); time.sleep(0.6)
        if sel:
            pg.locator(sel).first.screenshot(path=f'{OUT}/frontier_{n}.png')
        else:
            pg.screenshot(path=f'{OUT}/frontier_{n}.png')
        print(n, 'errors:', errs[:3]); pg.close()
    b.close()
