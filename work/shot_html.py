"""Screenshot standalone plotly HTML files (visual QA of charts)."""
import sys
import time

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1300, 'height': 700})
    for f in sys.argv[1:]:
        pg.goto('file:///' + f.replace('\\', '/'))
        time.sleep(2)
        pg.screenshot(path=f.replace('.html', '.png'), full_page=True)
    b.close()
