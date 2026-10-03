"""Screenshot the standalone Evidence Field at each step (visual QA). usage: shot_hero.py <html> <prefix> [steps]"""
import sys
import time

from playwright.sync_api import sync_playwright

path, prefix = sys.argv[1], sys.argv[2]
steps = [int(s) for s in sys.argv[3].split(',')] if len(sys.argv) > 3 else [0, 1, 2, 3, 4]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1440, 'height': 1100})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto('file:///' + path.replace('\\', '/'))
    time.sleep(1)
    for i in steps:
        pg.evaluate(f'go({i})')
        time.sleep(0.6)
        pg.screenshot(path=f'{prefix}_step{i}.png', full_page=True)
    b.close()
print('errors:', errs[:5])
