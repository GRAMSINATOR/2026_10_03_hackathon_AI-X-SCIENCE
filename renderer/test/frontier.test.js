// Marker Frontier presentation layer (marker-frontier/1 -> view state). States are derived in Python; these tests check
// that the view never invents precision, keeps contradictions, and works before any research has arrived.
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import {
  railSegments, lanes, blindspotChips, decisionValue, markerCounts, capabilityCounts, papersFor, recordsFor, researchState,
  openPull, briefClaimFor, casesById,
} from '../src/model/frontier.js';

const load = n => JSON.parse(readFileSync(new URL(`../../fixtures/${n}`, import.meta.url), 'utf8'));
const SEED = load('marker_frontier.json'), EX = load('marker_frontier.example.json'), B3 = load('decision_brief.Batch_3.json');
const EMPTY = { ...SEED, markers: [], capabilities: [], papers: [], records: [], reviews: [], lanes: { current_capture: [], new_capability: [] },
  open_blindspots: SEED.blindspots.filter(b => b.consequential).map(b => b.key), context: { ...SEED.context, bundles: [], literature_present: false,
  research_agent_present: false, fixture_present: false } };
const C = (doc, id) => casesById(doc).C[id], M = (doc, id) => casesById(doc).M[id];

describe('evidence rail', () => {
  it('one categorical segment per gate, in document order; no fractions', () => {
    for (const doc of [SEED, EX]) {
      for (const m of doc.markers) {
        const s = railSegments(doc, 'marker', m);
        expect(s.map(x => x.gate)).toEqual(doc.rails.marker.map(r => r.gate));
        for (const x of s) expect(['met', 'partial', 'contested', 'failed', 'open']).toContain(x.state);
        expect(Object.keys(s[0]).sort()).toEqual(['gate', 'label', 'short', 'state', 'word']);
      }
      for (const c of doc.capabilities) expect(railSegments(doc, 'capability', c).map(x => x.gate)).toEqual(doc.rails.capability.map(r => r.gate));
    }
  });
  it('a failed measurability gate reads as blocked (routes to a capability)', () => {
    const s = railSegments(SEED, 'marker', M(SEED, 'marker:high_z_composition'));
    expect(s.find(x => x.gate === 'measurability').word).toBe('blocked');
  });
  it('fixture evidence never fills a segment', () => {
    for (const m of SEED.markers) expect(railSegments(EX, 'marker', M(EX, m.id))).toEqual(railSegments(SEED, 'marker', m));
    for (const c of SEED.capabilities) expect(railSegments(EX, 'capability', C(EX, c.id))).toEqual(railSegments(SEED, 'capability', c));
  });
});

describe('lanes and cases', () => {
  it('keeps rule order; tested-and-set-aside markers are split off; unobservable markers live under their capability', () => {
    const L = lanes(SEED);
    expect(L.active.map(m => m.id)).toEqual(['marker:fines_subfloor_size']);
    expect(L.setAside.map(m => m.status)).toEqual(['CONFOUNDED', 'REJECTED']);
    expect(L.capabilities.map(c => c.id)).toEqual(['capability:eds', 'capability:tomography_3d']);
    expect([...L.active, ...L.setAside].some(m => m.status === 'UNAVAILABLE')).toBe(false);
    expect(C(SEED, 'capability:eds').markers_unlocked).toContain('marker:high_z_composition');
  });
  it('blindspot chips: consequential first, one chip per limit, current batch flagged, general gaps explicit', () => {
    const eds = blindspotChips(SEED, C(SEED, 'capability:eds'), 'Batch_3');
    expect(eds).toHaveLength(1);
    expect(eds[0]).toMatchObject({ consequential: true, current: true });
    expect(blindspotChips(SEED, C(SEED, 'capability:eds'), 'Batch_2')[0].current).toBe(false);
    const gen = blindspotChips(SEED, C(SEED, 'capability:tomography_3d'), 'Batch_3');
    expect(gen.every(x => x.external && x.label.length > 10)).toBe(true);
  });
  it('decision value only for cases that close a consequential blindspot', () => {
    expect(decisionValue(SEED, M(SEED, 'marker:fines_subfloor_size'), 'Batch_3')).toMatchObject({ current: true, actions: ['ZOOM'] });
    expect(decisionValue(SEED, M(SEED, 'marker:latent_progression'), 'Batch_3')).toBeNull();
  });
  it('counts are the document counts, fixture shown separately', () => {
    const k = capabilityCounts(C(EX, 'capability:eds'));
    expect(k.find(x => x.fixture).v).toBe(2);
    expect(k.find(x => x.k === 'contradictory').v).toBe(0);           // the contradictory source is a fixture: not counted
    expect(markerCounts(M(SEED, 'marker:fines_subfloor_size')).find(x => x.k === 'current data').v).toBe('needs acquisition');
  });
});

describe('papers and records', () => {
  it('renders with zero papers', () => {
    for (const c of [...SEED.markers, ...SEED.capabilities]) expect(papersFor(SEED, c.id)).toEqual([]);
  });
  it('contradictory papers stay listed, after the supportive ones', () => {
    const ps = papersFor(EX, 'capability:eds');
    expect(ps.map(p => p.rows[0].direction)).toEqual(['SUPPORTIVE', 'CONTRADICTORY']);
    expect(ps[1].rows[0].label).toBe('CONTRADICTORY');
    for (const p of ps) expect(p.rows.every(a => a.target === 'capability:eds')).toBe(true);
  });
  it('records include substitute and confound basis', () => {
    const r = recordsFor(SEED, C(SEED, 'capability:eds'));
    expect(r.find(x => x.id === 'record:rl11').asBasis).toBe(true);
    expect(recordsFor(SEED, M(SEED, 'marker:latent_progression')).map(x => x.id)).toEqual(expect.arrayContaining(['record:rl4', 'record:rl5', 'record:rl6']));
  });
});

describe('before any research', () => {
  it('empty lanes, open blindspots carry the pull, research state says so', () => {
    const L = lanes(EMPTY);
    expect(L.active).toEqual([]); expect(L.capabilities).toEqual([]);
    expect(openPull(EMPTY, 'Batch_3').length).toBe(EMPTY.open_blindspots.length);
    expect(openPull(EMPTY, 'Batch_3')[0].current).toBe(true);
    expect(researchState(EMPTY)).toContain('no research bundle loaded');
    expect(researchState(EX).some(t => t.startsWith('FIXTURE'))).toBe(true);
  });
});

describe('link into the Examiner Matrix', () => {
  it('only through a claim the decision brief already makes, in the same batch', () => {
    const chip = blindspotChips(SEED, C(SEED, 'capability:eds'), 'Batch_3')[0];
    expect(briefClaimFor(B3, chip).id).toBe('limit.composition:M2060');
    const scale = blindspotChips(SEED, M(SEED, 'marker:fines_subfloor_size'), 'Batch_3')[0];
    expect(briefClaimFor(B3, scale).id).toBe('limit.scale:M2060');
    expect(briefClaimFor({ ...B3, source: { ...B3.source, batch: 'Batch_2' } }, chip)).toBeNull();
    expect(briefClaimFor(null, chip)).toBeNull();
  });
});
