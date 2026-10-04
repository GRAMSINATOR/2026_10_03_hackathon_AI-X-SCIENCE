// Payload: injected by qc/instrument.py ({field, assets, imagery, brief}) or, in dev, a fixture served from ../fixtures.
export async function loadPayload() {
  const el = document.getElementById('evidence-payload');
  let p = null;
  try { p = JSON.parse(el ? el.textContent : 'null'); } catch { p = null; }
  if (p && typeof p === 'object' && p.field) return p;
  const name = new URLSearchParams(location.search).get('fixture') || 'epistemic_field.Batch_3.json';
  const field = await (await fetch('/' + name)).json();
  const assets = {};
  for (const [id, a] of Object.entries(field.assets || {})) {
    assets[id] = { bse: '/' + a.image, seg: a.segmentation ? '/' + a.segmentation.image : null,
                   width_um: a.width_um, height_um: a.height_um, image_px_um: a.image_px_um };
  }
  let brief = null;   // the governed decision brief built from the same fixture (python -m qc fixture)
  try { brief = await (await fetch(`/decision_brief.${field.context.batch}.json`)).json(); } catch { brief = null; }
  return { field, assets, brief };
}
