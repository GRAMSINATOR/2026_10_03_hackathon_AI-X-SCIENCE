"""1920x1080 visual QA of the flat instrument. usage: qa_flat.py [scenario ...]"""
import json, os, sys, time, pathlib
sys.path.insert(0, os.getcwd())
from qc import brief, instrument
from playwright.sync_api import sync_playwright
SCEN = {'b3_signal': ('Batch_3', ['__qa.setStage(0)']), 'b3_scrutiny': ('Batch_3', ['__qa.setStage(1)']), 'b3_field': ('Batch_3', ['__qa.setStage(2)']),
        'b3_rim': ('Batch_3', ['__qa.setStage(3)']), 'b3_next': ('Batch_3', ['__qa.setStage(4)', '__qa.setSelAction(3)']),
        'b3_next_eds': ('Batch_3', ['__qa.setStage(4)', '__qa.setSelAction(2)']),
        'b3_scrutiny_m2088': ('Batch_3', ['__qa.setStage(1)', "__qa.selectKey('M2088:porosity')"]),
        'b2_signal': ('Batch_2', ['__qa.setStage(0)']), 'b2_rim': ('Batch_2', ['__qa.setStage(3)']),
        'b3_sel_pale': ('Batch_3', ['__qa.setStage(0)', "__qa.selectKey('M1612:porosity')"]),
        'b3_sel_switch': ('Batch_3', ['__qa.setStage(0)', "__qa.selectKey('M2068:additive_d50_um')", "__qa.selectKey('M1904:pore_size_um')"]),
        'b3_missing': ('Batch_3', ['__qa.setStage(3)', "__qa.selectKey('M2060:composition')"]),
        'b3_pores': ('Batch_3', ['__qa.setStage(1)', "__qa.selectKey('M2088:porosity')"]),
        'b3_kbd': ('Batch_3', ['__qa.setStage(0)', "document.querySelector('.instrument').focus()",
                   "['ArrowDown','ArrowDown','ArrowRight','ArrowRight'].forEach(k => document.querySelector('.instrument').dispatchEvent(new KeyboardEvent('keydown', {key: k, bubbles: true})))"]),
        'b2_field': ('Batch_2', ['__qa.setStage(2)']),
        'hero_b3': ('Batch_3', []), 'hero_b2': ('Batch_2', []), 'hero_b3_laptop': ('Batch_3', []),
        'tr_evidence': ('Batch_3', ["__qa.trace('evidence.M2060:additive_density')"]),
        'tr_scale': ('Batch_3', ["__qa.trace('limit.scale:M2060')"]),
        'tr_comp': ('Batch_3', ["__qa.trace('limit.composition:M2060')"]),
        'tr_support': ('Batch_3', ["__qa.trace('support.qc')"]),
        'tr_verify': ('Batch_3', ["__qa.trace('action.repeat:1')"]),
        'tr_extent': ('Batch_3', ["__qa.trace('limit.spatial:M2060:additive_density')"])}
names = sys.argv[1:] or list(SCEN); built = {}
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    for n in names:
        batch, steps = SCEN[n]
        if batch not in built:
            f = json.load(open(f'fixtures/epistemic_field.{batch}.json', encoding='utf-8')); out = f'work/instrument_{batch}.html'
            open(out, 'w', encoding='utf-8').write(instrument.render(f, asset_dir='fixtures/assets', brief=brief.build(f))); built[batch] = out
        vw, vh = (1440, 900) if n.endswith('_laptop') else (1920, 1080)
        pg = b.new_page(viewport={'width': vw, 'height': vh}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.goto(pathlib.Path(built[batch]).resolve().as_uri()); pg.wait_for_function('window.__qa !== undefined', timeout=60000); time.sleep(2)
        for s in steps: pg.evaluate(s); time.sleep(0.8)
        if n == 'b3_sel_switch':   # press must not animate: ~1 frame after the click vs 1.5 s later must be identical
            from PIL import Image, ImageChops; import io
            pg.evaluate("__qa.selectKey('M2088:pore_size_um')"); pg.evaluate('new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
            A = Image.open(io.BytesIO(pg.screenshot(clip=dict(x=40, y=60, width=1300, height=620)))).convert('RGB'); time.sleep(1.5)
            B = Image.open(io.BytesIO(pg.screenshot(clip=dict(x=40, y=60, width=1300, height=620)))).convert('RGB')
            d = ImageChops.difference(A, B).getbbox(); print('press animation check: changed region after first frame =', d)
        time.sleep(1.5); pg.screenshot(path=f'work/viz/flat_{n}.png', full_page=bool(os.environ.get('FULL'))); pg.close(); print(n, 'errors:', errs[:3])
    b.close()
