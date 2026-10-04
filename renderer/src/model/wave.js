// Deterministic directional population wave:  t_i = directional_position_i + small seeded variation_i
// Keys resolve dark -> edge catches light -> ceramic -> semantic colour -> printed value.

export function hashString(s) {          // FNV-1a 32-bit
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); }
  return h >>> 0;
}
export function rand01(seed) {            // mulberry32, one draw
  let t = (seed + 0x6d2b79f5) >>> 0;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

// keys: [{id, row, col}] ; returns {starts: {id: ms}, duration: ms per key, total: ms}
export function populationSchedule(keys, { seed = 'evidence-field', spanMs = 520, jitterMs = 70, durationMs = 300,
  direction = [0.8, 0.6] } = {}) {
  if (!keys.length) return { starts: {}, duration: durationMs, total: 0 };
  const [dx, dy] = direction;
  const pos = keys.map(k => k.col * dx + k.row * dy);
  const lo = Math.min(...pos), hi = Math.max(...pos), span = hi - lo || 1;
  const s0 = hashString(seed);
  const starts = {};
  keys.forEach((k, i) => {
    const jitter = (rand01(s0 ^ hashString(k.id)) - 0.5) * 2 * jitterMs;
    starts[k.id] = Math.max(0, ((pos[i] - lo) / span) * spanMs + jitter);
  });
  const total = Math.max(...Object.values(starts)) + durationMs;
  return { starts, duration: durationMs, total };
}

const smooth = (a, b, x) => { const t = Math.max(0, Math.min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

// phase envelope for one key at time t since appearance (reduced motion -> resolved immediately)
export function keyPhase(t, start, duration, reduced = false) {
  if (reduced) return { p: 1, edge: 0, material: 1, colour: 1, text: 1, lift: 0 };
  const p = Math.max(0, Math.min(1, (t - start) / duration));
  return {
    p,
    edge: smooth(0.0, 0.25, p) * (1 - smooth(0.35, 0.7, p)),   // brief specular edge catch
    material: smooth(0.15, 0.55, p),                           // dark -> ceramic
    colour: smooth(0.45, 0.85, p),                             // semantic colour settles
    text: smooth(0.75, 1.0, p),                                // value resolves last
    lift: 1 - smooth(0.0, 0.8, p),                             // tiny depth emergence (fraction of max)
  };
}
