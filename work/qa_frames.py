"""Render-on-demand check: frames rendered during idle and per stage change (flat instrument)."""
import json, os, sys, time, pathlib
sys.path.insert(0, os.getcwd())
from playwright.sync_api import sync_playwright
out = pathlib.Path('work/instrument_Batch_3.html').resolve().as_uri()
F = 'window.__gl.field.render.frame'
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader']); pg = b.new_page(viewport={'width': 1920, 'height': 1080})
    pg.goto(out); pg.wait_for_function('window.__qa !== undefined && window.__gl && window.__gl.field', timeout=60000); time.sleep(5)
    a = pg.evaluate(F); time.sleep(3); bb = pg.evaluate(F); print('idle 3 s frames:', bb - a)
    pg.evaluate('__qa.setStage(3)'); time.sleep(3); c = pg.evaluate(F); time.sleep(3); d = pg.evaluate(F)
    print('stage change frames:', c - bb, '| idle after:', d - c)
    pg.evaluate("__qa.selectKey('M1612:porosity')"); time.sleep(2.5); e = pg.evaluate(F); print('key press frames:', e - d); b.close()
