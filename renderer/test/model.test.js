// Semantic tests of the renderer's representation layer (no WebGL): contract -> view state.
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { buildModel, keyVisual, STAGES, interpretation } from '../src/model/adapter.js';
import { HUE, CATEGORY, chromaFromExceedance, mix } from '../src/model/palette.js';
import { explainKey, explainStage, explainAction, actionPresentation, legendFor } from '../src/model/explain.js';
import { populationSchedule, keyPhase } from '../src/model/wave.js';
import { stackLayers, registration, layerForKey, prospective } from '../src/model/stack.js';

const load = b => JSON.parse(readFileSync(new URL(`../../fixtures/epistemic_field.${b}.json`, import.meta.url), 'utf8'));
const F3 = load('Batch_3'), F2 = load('Batch_2');
const M3 = buildModel(F3), M2 = buildModel(F2);
const key = (M, id) => M.keys.find(k => k.id === id);
const vis = (M, id, s, sel = {}) => keyVisual(M, key(M, id), s, sel);
const assetsFor = F => Object.fromEntries(Object.entries(F.assets).map(([id, a]) => [id, { bse: a.image, seg: a.segmentation && a.segmentation.image }]));
const idx = (M, verb, entity) => M.actions.findIndex(a => a.verb === verb && (!entity || a.targets.entities.includes(entity)));

describe('adapter structure', () => {
  it('rejects other contract versions', () => { expect(() => buildModel({ ...F3, schema_version: 'x' })).toThrow(); });
  it('one key per entity x dimension; composition is a missing socket, not a measurement', () => {
    expect(M3.keys.length).toBe(F3.entities.length * F3.dimensions.length);
    const miss = M3.keys.filter(k => k.kind === 'missing');
    expect(miss.length).toBe(F3.entities.length);
    miss.forEach(k => { expect(k.dimension).toBe('composition'); expect(k.obs).toBeUndefined(); });
  });
  it('independent entities come before reference-linked ones (presentation order only)', () => {
    const linked = M2.rows.map(r => r.refLinked);
    expect(linked).toEqual([...linked].sort((a, b) => a - b));
  });
  it('works on both fixtures', () => { expect(M2.meta.verdict).toBe('ACCEPT'); expect(M3.meta.verdict).toBe('REJECT'); });
});

describe('five-stage projection', () => {
  it('SIGNAL: decisive deviation is rich and glows; in-family keys stay ceramic', () => {
    const v = vis(M3, 'M2060:additive_density', 0);
    expect(v.hue).toBe(HUE.above); expect(v.chroma).toBeGreaterThan(0.6); expect(v.emissive).toBeGreaterThan(0);
    expect(vis(M3, 'M1612:porosity', 0).chroma).toBeLessThan(0.15);
    expect(vis(M3, 'M2068:additive_d50_um', 0).emissive).toBe(0);           // deviant but not exceptional: no glow
  });
  it('glow is reserved for exceptional evidence', () => {
    for (const s of [0, 1]) {
      const glowing = M3.keys.filter(k => keyVisual(M3, k, s).emissive > 0).map(k => k.id);
      const out = F3.observations.filter(o => o.reference_relation.status === 'out').map(o => o.id);
      expect(glowing.every(id => out.includes(id))).toBe(true);
    }
  });
  it('SCRUTINY: failures take the hue of their cause; acquisition concern is matte; reference-linked is ghosted provenance', () => {
    const acq = vis(M3, 'M2088:porosity', 1), inc = vis(M3, 'M2068:additive_d50_um', 1), surv = vis(M3, 'M2060:additive_density', 1);
    expect(acq.category).toBe('acquisition'); expect(acq.hue).toBe(HUE.acquisition); expect(acq.finish).toBe('matte');
    expect(inc.category).toBe('survives'); expect(inc.hue).toBe(HUE.above); expect(inc.finish).toBe('gloss');
    expect(surv.category).toBe('survives'); expect(surv.finish).toBe('gloss'); expect(surv.hue).toBe(HUE.above);
    expect(surv.chroma).toBeCloseTo(vis(M3, 'M2060:additive_density', 0).chroma);
    const ref = vis(M3, 'M2080:porosity', 1); expect(ref.ghost).toBe(true); expect(ref.category).toBe('provenance');
  });
  it('FIELD: hue names the largest envelope component; chroma grows with its share; never emissive', () => {
    const hueOf = { spatial_sampling: HUE.spatial, baseline_support: HUE.population, material_spread: HUE.material };
    let lo = null, hi = null;
    for (const o of F3.observations.filter(o => o.variance_shares)) {
      const v = vis(M3, o.id, 2), vs = o.variance_shares;
      const top = [['spatial_sampling', vs.spatial_sampling], ['baseline_support', vs.baseline_support], ['material_spread', vs.approved_material]].sort((a, b) => b[1] - a[1])[0];
      expect(v.category).toBe(top[0]); expect(v.hue).toBe(hueOf[top[0]]); expect(v.emissive).toBe(0);
      if (top[0] === 'spatial_sampling') { if (!lo || top[1] < lo[0]) lo = [top[1], v.chroma]; if (!hi || top[1] > hi[0]) hi = [top[1], v.chroma]; }
    }
    expect(hi[1]).toBeGreaterThan(lo[1]);
  });
  it('OUTER RIM: only rimmed evidence is lit; consequential limits are stronger; missing composition only rings where it matters', () => {
    const d = vis(M3, 'M2060:additive_density', 3), p = vis(M3, 'M2088:porosity', 3);
    expect(d.quiet).toBe(false); expect(d.hue).toBe(HUE.scale); expect(d.chroma).toBeGreaterThan(p.chroma);
    expect(p.hue).toBe(HUE.spatial);
    expect(vis(M3, 'M1612:porosity', 3).quiet).toBe(true);
    expect(vis(M3, 'M2060:composition', 3).ring).toBe(HUE.composition);
    expect(vis(M3, 'M1612:composition', 3).ring).toBeNull();
    expect(vis(M3, 'M2060:composition', 0).ring).toBeNull();
  });
  it('NEXT CAPTURE: the field shows exactly the reach of the selected action', () => {
    const ext = idx(M3, 'EXTEND', 'M2088'), eds = idx(M3, 'EDS');
    const lit = M3.keys.filter(k => !keyVisual(M3, k, 4, { action: ext }).quiet).map(k => k.id);
    expect(lit).toEqual(['M2088:porosity']);
    expect(vis(M3, 'M2060:composition', 4, { action: eds }).ring).toBe(HUE.composition);
    expect(vis(M3, 'M2060:composition', 4, { action: ext }).ring).toBeNull();
  });
  it('interpretation lines are data-derived', () => {
    expect(interpretation(M3, 1)).toContain('2 of 4');
    expect(interpretation(M2, 0)).toMatch(/No observation/);
  });
});

describe('action reach', () => {
  it('targets and causes resolve to field elements', () => {
    for (const a of M3.actions) a.reach.keys.forEach(id => expect(key(M3, id)).toBeTruthy());
    const eds = M3.actions[idx(M3, 'EDS')], sec = M3.actions[idx(M3, 'SECTIONS')], base = M3.actions[idx(M3, 'BASELINE')];
    expect(eds.reach.sockets).toContain('M2060:composition');
    expect(sec.reach.batch).toBe(true);
    expect(base.reach.cols.sort()).toEqual([...base.targets.dimensions].sort());
  });
});

describe('population wave', () => {
  const keys = M3.keys.map(k => ({ id: k.id, row: k.row, col: k.col }));
  it('is deterministic, directional and short', () => {
    const a = populationSchedule(keys), b = populationSchedule(keys);
    expect(a).toEqual(b);
    const meanStart = c => { const xs = keys.filter(k => k.col === c).map(k => a.starts[k.id]); return xs.reduce((p, q) => p + q, 0) / xs.length; };
    expect(meanStart(0)).toBeLessThan(meanStart(6));
    expect(a.total).toBeGreaterThan(500); expect(a.total).toBeLessThanOrEqual(900);
    expect(populationSchedule(keys, { seed: 'other' })).not.toEqual(a);
  });
  it('resolves in order and honours reduced motion', () => {
    const early = keyPhase(60, 0, 300), late = keyPhase(299, 0, 300);
    expect(early.material).toBeGreaterThan(early.text);
    expect(late.text).toBeGreaterThan(0.99);
    expect(keyPhase(0, 500, 300, true)).toMatchObject({ p: 1, text: 1, material: 1, colour: 1 });
  });
});

describe('evidence stack', () => {
  const A3 = assetsFor(F3);
  it('every layer is registered to the same specimen frame', () => {
    const reg = registration(M3, 'M2060');
    expect(reg.runs.length).toBe(1); expect(Math.round(reg.totalUm)).toBe(698);
    const { layers } = stackLayers(M3, 'M2060', 2, { assets: A3 });
    for (const L of layers.filter(l => l.kind === 'profile')) {
      const cells = L.cells[0].cells;
      expect(cells[0].x0Um).toBeGreaterThanOrEqual(-1e-6);
      expect(cells[cells.length - 1].x0Um + cells[cells.length - 1].widthUm).toBeLessThanOrEqual(reg.totalUm + 1e-6);
    }
  });
  it('unconnected runs keep unknown separation', () => {
    const reg = registration(M3, 'M2088');
    expect(reg.runs.length).toBe(1); expect(reg.separationKnown).toBe(true); expect(reg.totalUm).toBeGreaterThan(0);
  });
  it('detection layers exist only with segmentation assets; missing composition has no content', () => {
    const withA = stackLayers(M3, 'M2060', 3, { assets: A3 }).layers, noA = stackLayers(M3, 'M2060', 3, { assets: {} }).layers;
    expect(withA.find(l => l.id === 'mask_highz').available).toBe(true);
    expect(noA.find(l => l.id === 'mask_highz').available).toBe(false);
    const miss = withA.find(l => l.kind === 'missing');
    expect(miss.available).toBe(false); expect(miss.cells).toBeUndefined(); expect(miss.regions).toBeUndefined();
    expect(miss.consequential).toBe(true);
  });
  it('stage gating: masks from SCRUTINY, extent from OUTER RIM, prospective only in NEXT CAPTURE', () => {
    const vis = s => stackLayers(M3, 'M2088', s, { assets: A3, action: s === 4 ? idx(M3, 'EXTEND', 'M2088') : null }).layers.filter(l => l.visible).map(l => l.id);
    expect(vis(0)).not.toContain('mask_highz'); expect(vis(1)).toContain('mask_highz');
    expect(vis(2)).not.toContain('extent'); expect(vis(3)).toContain('extent');
    expect(vis(3)).not.toContain('prospective'); expect(vis(4)).toContain('prospective');
  });
  it('prospective geometry only where the evidence defines a footprint', () => {
    const reg = registration(M3, 'M2088');
    const ext = prospective(M3, 'M2088', reg, idx(M3, 'EXTEND', 'M2088'));
    expect(ext.regions).toHaveLength(1); expect(ext.regions[0].side).toBe('end');
    expect(ext.regions[0].x0Um).toBeCloseTo(reg.totalUm);                         // abuts the open edge
    expect(prospective(M3, 'M2088', reg, idx(M3, 'ZOOM'))).toBeNull();
    expect(prospective(M3, 'M2088', reg, idx(M3, 'EDS'))).toBeNull();
    expect(prospective(M3, 'M2088', reg, idx(M3, 'SECTIONS'))).toBeNull();
    const note = stackLayers(M3, 'M2088', 4, { assets: A3, action: idx(M3, 'EDS') }).note;
    expect(note).toBe('EDS does not act on M2088.');
  });
  it('field <-> stack linkage uses only real data relations', () => {
    expect(layerForKey(key(M3, 'M2060:additive_density'))).toBe('profile:additive_density');
    expect(layerForKey(key(M3, 'M2060:additive_d50_um'))).toBe('mask_highz');
    expect(layerForKey(key(M3, 'M2060:composition'))).toBe('missing:composition');
    const { layers } = stackLayers(M3, 'M2088', 3, { assets: A3 });
    for (const L of layers) for (const id of L.linkedKeys) expect(key(M3, id)).toBeTruthy();
    expect(layers.find(l => l.id === 'extent').linkedKeys).toEqual(['M2088:porosity']);
  });
  it('profile cells use the approved band and direction hues', () => {
    const L = stackLayers(M3, 'M2060', 2, { assets: A3 }).layers.find(l => l.id === 'profile:additive_density');
    const above = L.cells[0].cells.filter(c => c.state === 'above');
    expect(above.length).toBeGreaterThan(L.cells[0].cells.length / 2);
    above.forEach(c => expect(c.hue).toBe(HUE.above));
  });
});

describe('palette', () => {
  it('chroma is monotonic in exceedance', () => {
    const xs = [0, 0.3, 0.8, 1.0, 1.5, 2.5, 4];
    xs.slice(1).forEach((x, i) => expect(chromaFromExceedance(x)).toBeGreaterThanOrEqual(chromaFromExceedance(xs[i])));
  });
  it('stages are the five epistemic stages', () => { expect(STAGES).toEqual(['SIGNAL', 'SCRUTINY', 'FIELD', 'OUTER RIM', 'NEXT CAPTURE']); });
});

describe('explanation panel is linked to the keys', () => {
  it('leads with the key category, in the key hue, and reorders by stage', () => {
    for (const st of [0, 1, 2, 3]) {
      const v = vis(M3, 'M2060:additive_density', st), ex = explainKey(M3, 'M2060:additive_density', st, {});
      expect(ex.sections[0].id).toBe('category'); expect(ex.sections[0].hue).toBe(v.hue);
      expect(ex.sections[0].title).toBe(CATEGORY[v.category].label);
    }
    expect(explainKey(M3, 'M2060:additive_density', 2, {}).sections[1].id).toBe('envelope');
    expect(explainKey(M3, 'M2060:additive_density', 3, {}).sections[1].id).toBe('limits');
    // off-stage sections carry no accent, so colour in the panel always means the same thing as on the grid
    expect(explainKey(M3, 'M2060:additive_density', 2, {}).sections.find(x => x.id === 'measurement').hue).toBe(null);
  });
  it('legend lists exactly the non-quiet categories on the grid, with their hues', () => {
    for (const st of [0, 1, 2, 3]) {
      const lg = legendFor(M3, st, {}), cats = new Set(M3.keys.map(k => vis(M3, k.id, st).category));
      const onGrid = M3.keys.map(k => vis(M3, k.id, st)).map(v => `${CATEGORY[v.category].label}|${CATEGORY[v.category].hue || v.hue}`);
      lg.forEach(l => expect(onGrid).toContain(`${l.label}|${l.hue}`));
      expect(lg.length).toBe([...cats].filter(c => c !== 'settled' && c !== 'in_family').length);
    }
  });
  it('stage overview and selected action are explained from the contract', () => {
    expect(explainStage(M3, 3, null).sections.some(s => s.id === 'limits')).toBe(true);
    const ext = explainAction(M3, idx(M3, 'EXTEND', 'M2088'));
    expect(ext.hue).toBe(M3.actions[idx(M3, 'EXTEND', 'M2088')].reach.hue);
    expect(ext.rows.find(r => r[0] === 'expected effect')[1]).toMatch(/698 µm.*end/);
  });
  it('compresses selected actions without changing their contract semantics', () => {
    const repeat = actionPresentation(M3, idx(M3, 'REPEAT', 'M2060'));
    expect(repeat.listLabel).toBe('M2060 · reference-frame acquisition settings');
    expect(repeat.why).toBe('Tests whether the decision-driving deviation in M2060 is acquisition-driven.');
    expect(repeat.resolves).toBe('Acquisition vs material change');
    expect(repeat).toMatchObject({ tier: 'T1', grounding: 'GROUNDED', cost: 'LOW COST' });
    expect(repeat.leverage).toBe('DECISION-DRIVING — verdict changes to ACCEPT without M2060.');
    expect(actionPresentation(M3, idx(M3, 'EDS')).grounding).toBe('PROSPECTIVE');
    const accept = actionPresentation(M2, idx(M2, 'SECTIONS'));
    expect(accept.why).toBe('Measures how widely the result extends across the lot.');
    expect(accept.resolves).toBe('Lot prevalence');
  });
  it('pads carry a stage-specific second line', () => {
    expect(vis(M3, 'M2060:additive_density', 0).sub).toBe('z +6.9');
    expect(vis(M3, 'M2088:porosity', 1).sub).toBe('acq. could explain');
    expect(vis(M3, 'M2060:additive_density', 2).sub).toMatch(/^spatial \d+%$/);
    expect(vis(M3, 'M2060:additive_density', 3).sub).toBe('scale');
    expect(vis(M3, 'M1612:porosity', 3).sub).toBe('');
  });
  it('colour mixing is perceptual and exact at the ends', () => {
    expect(mix('#ece6d8', '#e2761f', 0)).toBe('#ece6d8'); expect(mix('#ece6d8', '#e2761f', 1)).toBe('#e2761f');
  });
});

describe('stage colour models and physical selection', () => {
  it('selection is depth only: colour semantics are identical whether or not a key is selected', () => {
    for (const st of [0, 1, 2, 3, 4]) for (const k of M3.keys) {
      const a = vis(M3, k.id, st, { action: st === 4 ? 3 : null }), b = vis(M3, k.id, st, { key: k.id, action: st === 4 ? 3 : null });
      expect(b.selected).toBe(true); expect(a.selected).toBe(false);
      for (const f of ['category', 'hue', 'chroma', 'emissive', 'finish', 'ink', 'sub']) expect(b[f]).toEqual(a[f]);
    }
  });
  it('a selected key is seated deeper, as a latched state', async () => {
    const { keyElevation, KEY } = await import('../src/scene/resources.js');
    expect(keyElevation(true)).toBe(KEY.pressed); expect(keyElevation(false)).toBe(KEY.up);
    expect(KEY.up - KEY.pressed).toBeGreaterThan(0.2 * KEY.up);
  });
  it('SIGNAL is quantitative and two-family; in-family values stay near white', () => {
    const hues = new Set(M3.keys.filter(k => k.kind === 'observation').map(k => vis(M3, k.id, 0)).filter(v => v.chroma > 0.05).map(v => v.hue));
    hues.forEach(h => expect([HUE.above, HUE.below]).toContain(h));
    expect(vis(M3, 'M1612:porosity', 0).chroma).toBeLessThan(0.05);
    expect(vis(M3, 'M2060:additive_density', 0).chroma).toBeGreaterThan(0.85);
  });
  it('OUTER RIM: settled keys recede to white with soft ink; consequential limits are rich; non-consequential pastel', () => {
    const settled = M3.keys.filter(k => k.kind === 'observation').map(k => vis(M3, k.id, 3)).filter(v => v.category === 'settled');
    expect(settled.length).toBeGreaterThan(30); settled.forEach(v => { expect(v.chroma).toBe(0); expect(v.ink).toBe('soft'); });
    expect(vis(M3, 'M2060:additive_density', 3).chroma).toBeGreaterThan(0.8);
    expect(vis(M3, 'M2088:porosity', 3).chroma).toBeLessThan(0.3);
  });
  it('emission is the extreme tail only: at most one key per stage', () => {
    for (const st of [0, 1, 2, 3, 4]) expect(M3.keys.filter(k => vis(M3, k.id, st, { action: 3 }).emissive > 0).length).toBeLessThanOrEqual(1);
    for (const st of [0, 1, 2, 3, 4]) expect(M2.keys.filter(k => vis(M2, k.id, st, { action: 0 }).emissive > 0).length).toBe(0);
  });
  it('FIELD chroma follows dominance and proximity to the threshold, not dominance alone', () => {
    const far = vis(M3, 'M2272:additive_d50_um', 2), near = vis(M3, 'M2068:additive_d50_um', 2);
    expect(far.category).toBe('spatial_sampling'); expect(near.category).toBe('spatial_sampling');
    expect(near.chroma).toBeGreaterThan(far.chroma);
  });
});

describe('decision brief click-through (proof refs drive navigation)', () => {
  const briefOf = b => JSON.parse(readFileSync(new URL(`../../fixtures/decision_brief.${b}.json`, import.meta.url), 'utf8'));
  for (const [b, M, F] of [['Batch_3', M3, F3], ['Batch_2', M2, F2]]) {
    it(`${b}: every hero claim has a resolvable focus, proof refs and an existing examiner target`, async () => {
      const { navTarget, resolveRef } = await import('../src/model/brief.js');
      const B = briefOf(b), C = Object.fromEntries(B.claims.map(c => [c.id, c]));
      const ids = Object.values(B.hero).flatMap(h => h.claims).concat([B.hero.decision.footer]);
      for (const id of ids) {
        const c = C[id];
        expect(c).toBeTruthy(); expect(c.proof_refs.length).toBeGreaterThan(0);
        c.proof_refs.forEach(r => expect(resolveRef(F, r)).not.toBeUndefined());
        const t = navTarget(M, c.focus);
        expect([0, 1, 2, 3, 4]).toContain(t.stage);
        if (t.key) expect(M.keys.some(k => k.id === t.key)).toBe(true);
        if (t.action != null) expect(M.actions[t.action]).toBeTruthy();
        c.action_refs.forEach(a => expect(M.actions.some(x => x.id === a)).toBe(true));
      }
    });
  }
  it('Batch 3: evidence -> scrutiny on M2060, composition -> its socket, verify -> REPEAT, extent -> spatial view', async () => {
    const { navTarget } = await import('../src/model/brief.js');
    const C = Object.fromEntries(briefOf('Batch_3').claims.map(c => [c.id, c]));
    expect(navTarget(M3, C['evidence.M2060:additive_density'].focus)).toMatchObject({ stage: 1, key: 'M2060:additive_density' });
    expect(navTarget(M3, C['limit.composition:M2060'].focus)).toMatchObject({ stage: 3, key: 'M2060:composition' });
    expect(navTarget(M3, C['limit.scale:M2060'].focus)).toMatchObject({ stage: 3, key: 'M2060:additive_density' });
    const v = navTarget(M3, C['action.repeat:1'].focus);
    expect(v.stage).toBe(4); expect(M3.actions[v.action].verb).toBe('REPEAT'); expect(v.key).toBe('M2060:additive_density');
    expect(C['limit.spatial:M2060:additive_density']).toBeUndefined();
  });
});
