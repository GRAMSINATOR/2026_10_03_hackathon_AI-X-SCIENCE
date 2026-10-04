// Marker Frontier presentation layer (marker-frontier/1 -> view state). States are derived in Python; these tests check
// that the view never invents precision, keeps contradictions, and works before any research has arrived.
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import MarkerFrontier from '../src/ui/MarkerFrontier.jsx';
import {
  railSegments, lanes, blindspotChips, decisionValue, markerCounts, capabilityCounts, papersFor, recordsFor, researchState,
  openPull, briefClaimFor, casesById, opportunityView, vorticesFor, representationWord,
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
    expect(L.active.map(m => m.id)).toEqual([
      'marker:fines_subfloor_size', 'marker:count_overdispersion_curve', 'marker:high_z_nearest_neighbour',
      'marker:high_z_pair_correlation', 'marker:minkowski_phase_morphology', 'marker:open_edge_persistence',
      'marker:phase_boundary_morphology', 'marker:phase_chord_distribution',
      'marker:phase_fraction_heterogeneity_curve', 'marker:phase_lineal_path', 'marker:spatial_correlation_length',
    ]);
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

describe('opportunity map', () => {
  it('renders a deterministic shortlist without converting categorical factors into a score', () => {
    const O = opportunityView(SEED);
    expect(O.currentFrontier.map(m => [m.opportunity_rank, m.id])).toEqual([
      [1, 'marker:fines_subfloor_size'],
      [2, 'marker:high_z_composition'],
      [3, 'marker:phase_conditioned_fines_distribution'],
    ]);
    expect(O.computableNow.map(m => m.id)).toEqual([
      'marker:open_edge_persistence', 'marker:phase_fraction_heterogeneity_curve', 'marker:spatial_correlation_length',
      'marker:count_overdispersion_curve', 'marker:high_z_pair_correlation', 'marker:phase_chord_distribution',
      'marker:high_z_nearest_neighbour', 'marker:minkowski_phase_morphology', 'marker:phase_boundary_morphology',
      'marker:phase_lineal_path',
    ]);
    expect(O.needsCapture.map(m => m.id)).toEqual(['marker:fines_subfloor_size']);
    expect(O.observabilityGaps.map(m => m.id)).toContain('marker:phase_conditioned_fines_distribution');
    expect(O.rankingPolicy).toEqual(expect.arrayContaining([
      'decision-consequential inquiry first', 'then current-data testability',
    ]));
    for (const m of SEED.markers) expect(m).not.toHaveProperty('opportunity_score');
  });

  it('supports qualitative observation protocols and reciprocal inquiry-vortex links', () => {
    const m = M(SEED, 'marker:open_edge_persistence');
    expect(m).toMatchObject({ marker_kind: 'qualitative', representation: 'categorical_state' });
    expect(representationWord(m.representation)).toBe('categorical state');
    expect(vorticesFor(SEED, m).length).toBeGreaterThan(0);
    for (const v of vorticesFor(SEED, m)) expect(v.marker_refs).toContain(m.id);
  });

  it('pools multiple inaccessible markers under one observability attractor', () => {
    const O = opportunityView(SEED), eds = C(SEED, 'capability:eds');
    expect(O.attractors[0].id).toBe('capability:eds');
    expect(eds.marker_pool).toEqual(expect.arrayContaining([
      'marker:high_z_composition', 'marker:phase_conditioned_fines_distribution',
    ]));
    expect(eds.required_information.length).toBeGreaterThan(0);
    for (const mid of eds.marker_pool) expect(M(SEED, mid).required_capabilities).toContain(eds.id);
  });

  it('degrades to an honest sparse state when cases are absent', () => {
    const O = opportunityView(EMPTY);
    expect(O.currentFrontier).toEqual([]);
    expect(O.computableNow).toEqual([]);
    expect(O.observabilityGaps).toEqual([]);
    expect(O.attractors).toEqual([]);
  });

  it('renders both populated and sparse opportunity surfaces', () => {
    const populated = renderToStaticMarkup(createElement(MarkerFrontier, { frontier: SEED }));
    expect(populated).toContain('AGENTIC MARKER FRONTIER');
    expect(populated).toContain('Open-edge deviation phenotype');
    expect(populated).toContain('Composition-sensitive mapping (EDS)');
    const sparse = renderToStaticMarkup(createElement(MarkerFrontier, { frontier: EMPTY }));
    expect(sparse).toContain('No grounded marker opportunity yet');
    expect(sparse).toContain('No observability attractor yet');
  });
});

describe('papers and records', () => {
  it('shows primary method papers only on the candidate protocols they assess', () => {
    expect(papersFor(SEED, 'marker:count_overdispersion_curve').map(p => p.id)).toEqual(['paper:zachary2011_local_fluctuations']);
    expect(papersFor(SEED, 'marker:high_z_nearest_neighbour').map(p => p.id)).toEqual(['paper:leggoe2005_nearest_neighbour']);
    expect(papersFor(SEED, 'marker:fines_subfloor_size')).toEqual([]);
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
