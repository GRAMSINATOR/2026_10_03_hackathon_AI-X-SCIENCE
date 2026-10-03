"""Headless screenshots of the Streamlit app (each tab) for visual QA."""
import sys
import time

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8501'
tabs = sys.argv[2].split(',') if len(sys.argv) > 2 else ['Why: evidence']
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1500, 'height': 2600})
    for i in range(60):
        try:
            pg.goto(url, wait_until='networkidle', timeout=15000)
            break
        except Exception:
            time.sleep(1)
    pg.wait_for_selector('text=Batch to assess', timeout=120000)
    time.sleep(6)
    for t in tabs:
        if t != 'Why: evidence':
            pg.get_by_role('tab', name=t).click()
            time.sleep(5)
        pg.screenshot(path=f"work/viz/app_{t.split(':')[0].replace(' ', '_').replace('&', 'and')}.png", full_page=True)
    b.close()
print('done')
