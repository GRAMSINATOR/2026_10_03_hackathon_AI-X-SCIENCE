import { describe, expect, it } from 'vitest';
import { comparisonRows } from '../src/ui/ReferenceComparison.jsx';

const sensitivity = {
  complete: true,
  frames_evaluated: ['Frame_A', 'Frame_B'],
  sensitive_dimensions: ['density'],
  frames: {
    Frame_A: { dimensions: { density: { outside: 1, measurable: 3, max_abs_z: 3.2 }, porosity: { outside: 0, measurable: 3, max_abs_z: .7 } } },
    Frame_B: { dimensions: { density: { outside: 0, measurable: 3, max_abs_z: 1.1 }, porosity: { outside: 0, measurable: 3, max_abs_z: .9 } } },
  },
};

describe('reference comparison readout', () => {
  it('uses serialized cross-frame findings without classifying the target itself', () => {
    const rows = comparisonRows(sensitivity);
    expect(rows.find(x => x.dimension === 'density').stable).toBe(false);
    expect(rows.find(x => x.dimension === 'porosity').stable).toBe(true);
    expect(rows.find(x => x.dimension === 'density').cells.map(x => x.outside)).toEqual([1, 0]);
  });
  it('does not imply completeness when eligible frames are missing', () => {
    expect(comparisonRows({ ...sensitivity, complete: false })).toEqual([]);
  });
});
