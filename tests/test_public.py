"""Public hosting (issues #3, #4): image-free renderer payload, image-free bundle, tile -> parent map, and the dashboard
running from a derived bundle with no data/, no engine cache imagery and no pipeline run."""
import csv
import json
import os
import subprocess
import sys
import textwrap

import pytest

from qc import bundle, instrument

ROOT = os.path.dirname(os.path.dirname(__file__))
FIXTURE = os.path.join(ROOT, 'fixtures', 'epistemic_field.Batch_3.json')
HAVE_ENGINE = os.path.exists(os.path.join(ROOT, 'cache', 'reference.json')) and os.path.isdir(os.path.join(ROOT, 'reports'))
needs_engine = pytest.mark.skipif(not HAVE_ENGINE, reason='needs the local engine cache and reports')


@pytest.mark.skipif(not os.path.exists(instrument.DIST), reason='renderer not built')
def test_instrument_without_images_embeds_no_imagery_and_reads_no_assets(tmp_path):
    f = json.load(open(FIXTURE, encoding='utf-8'))
    html = instrument.render(f, asset_dir=str(tmp_path / 'does_not_exist'), images=False)
    assert bundle.foreign_images(html) == 0          # only the exact brand mark may be embedded
    assert '"imagery":false' in html and '"assets":{}' in html
    with_images = instrument.render(f, asset_dir=os.path.join(ROOT, 'fixtures', 'assets'))
    assert bundle.foreign_images(with_images) > 0 and '"imagery":true' in with_images


def test_bundle_check_rejects_image_bearing_content(tmp_path):
    (tmp_path / 'ok.json').write_text('{"a": 1}')
    assert bundle.check(tmp_path)
    (tmp_path / 'leak.html').write_text('<img src="data:image/png;base64,AAAA">')
    with pytest.raises(RuntimeError):
        bundle.check(tmp_path)
    (tmp_path / 'leak.html').unlink()
    (tmp_path / 'edges.npy').write_bytes(b'\x93NUMPY')
    with pytest.raises(RuntimeError):
        bundle.check(tmp_path)


@pytest.fixture(scope='module')
def public_bundle(tmp_path_factory):
    if not HAVE_ENGINE:
        pytest.skip('needs the local engine cache and reports')
    out = tmp_path_factory.mktemp('bundle') / 'b'
    bundle.export(str(out))
    return out


def test_bundle_is_image_free_and_complete(public_bundle):
    bundle.check(public_bundle)
    assert (public_bundle / 'reference.json').exists()
    for b in ('Batch_2', 'Batch_3'):
        for f in ('result.json', 'field.json'):
            assert (public_bundle / 'reports' / b / f).exists()
    assert not any(p.suffix.lower() in bundle.IMAGE_EXT for p in public_bundle.rglob('*'))


def test_provenance_map_units(public_bundle):
    rows = list(csv.DictReader(open(public_bundle / 'reports' / 'provenance_map.csv', encoding='utf-8')))
    doc = json.load(open(public_bundle / 'reports' / 'provenance_map.json', encoding='utf-8'))
    assert doc['schema'] == 'tile-parent-map/1' and doc['statistical_unit'] == 'parent_micrograph'
    assert len(rows) == doc['n_tiles'] and len({r['tile'] for r in rows}) == len(rows)          # every tile exactly once
    assert {r['parent_micrograph'] for r in rows} == set(doc['parents'])
    for pid, p in doc['parents'].items():                                                       # runs are contiguous
        for i, run in enumerate(p['runs']):
            pos = sorted(int(r['position_in_run']) for r in rows if r['parent_micrograph'] == pid and int(r['run']) == i)
            assert pos == list(range(len(run)))
    ref = json.load(open(public_bundle / 'reference.json'))
    approved = {m['parent'] for m in ref['micrographs']}
    assert {p for p, v in doc['parents'].items() if v['in_approved_reference']} == approved
    assert any(len(v['batches']) > 1 for v in doc['parents'].values())                          # parents span batches


# Runs app.py headlessly and reports every rendered image element and the embedded instrument page (iframe srcdoc).
# Streamlit renders all tab bodies, so the proof tabs are covered too.
APP_RUN = textwrap.dedent('''
    import json
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("app.py", default_timeout=180).run()
    def walk(n):
        yield n
        kids = getattr(n, "children", None)
        for c in (kids.values() if isinstance(kids, dict) else []):
            yield from walk(c)
    nodes = list(walk(at._tree))
    frames = [n.proto.srcdoc for n in nodes if type(n).__name__ == "UnknownElement" and n.type == "iframe"]
    print(json.dumps(dict(exception=[str(e.value) for e in at.exception], errors=[e.value for e in at.error],
                          images=sum(type(n).__name__ == "Image" for n in nodes), frames=frames)))
''')


def _run_app(env):
    p = subprocess.run([sys.executable, '-c', APP_RUN], cwd=ROOT, env=dict(os.environ, **env), capture_output=True, text=True, timeout=400)
    assert p.returncode == 0, p.stderr[-3000:]
    return json.loads(p.stdout.strip().splitlines()[-1])


def test_dashboard_runs_from_bundle_without_data_or_images(public_bundle, tmp_path):
    # positive control: the same probes do see imagery in local mode, so the public assertions below are not vacuous
    local = _run_app({})
    assert local['images'] > 0 and any(bundle.foreign_images(f) > 0 for f in local['frames'])
    out = _run_app(dict(QC_PUBLIC='1', QC_REF=str(public_bundle / 'reference.json'), QC_REPORTS=str(public_bundle / 'reports'),
                        QC_CACHE=str(public_bundle / 'cache' / 'fields'), QC_DATA=str(tmp_path / 'no_data')))
    assert out['exception'] == [] and out['errors'] == []
    assert out['images'] == 0
    assert out['frames'] and all(bundle.foreign_images(f) == 0 and '"imagery":false' in f for f in out['frames'])


def test_only_the_exact_brand_mark_is_allowed(tmp_path):
    import base64
    logo = open(bundle.BRAND_ASSETS[0], 'rb').read()
    ok = '<img src="data:image/png;base64,' + base64.b64encode(logo).decode() + '">'
    assert bundle.foreign_images(ok) == 0
    tampered = '<img src="data:image/png;base64,' + base64.b64encode(logo[:-1] + b'x').decode() + '">'
    assert bundle.foreign_images(tampered) == 1 and bundle.foreign_images(ok + tampered) == 1
    (tmp_path / 'page.html').write_text(ok)
    assert bundle.check(tmp_path)

