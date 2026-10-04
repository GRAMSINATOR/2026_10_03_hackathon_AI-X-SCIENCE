// Shared, memoised three.js resources: key and plate geometry, contact-shadow / cavity textures, studio environment, text.
import * as THREE from 'three';

// One manufactured key, used by every cell. Footprint w x d (rounded-rect plan, corner r), flat top, a modest rolled
// top-edge bevel and vertical walls. H is the full body height; only `up` (or `pressed`) of it stands above the plate,
// the rest sits inside the socket, so selection seats the key deeper without changing its geometry.
export const KEY = { w: 1.28, d: 0.52, r: 0.14, bevel: 0.05, H: 0.7, up: 0.32, pressed: 0.04, gap: 0.15, seam: 0.04 };
export const PLATE = { t: 0.34, cornerR: 0.3, edgeBevel: 0.025 };
// selection is depth only: the selected key stands lower in its socket, as a latched state (never interpolated)
export const keyElevation = selected => (selected ? KEY.pressed : KEY.up);

// rounded-rect outline in (x, z) with outward normals; corners walked (+x,-z) -> (+x,+z) -> (-x,+z) -> (-x,-z)
function roundedRectPoints(a, b, R, nc) {
  const pts = [], corners = [[a - R, -(b - R), -Math.PI / 2], [a - R, b - R, 0], [-(a - R), b - R, Math.PI / 2], [-(a - R), -(b - R), Math.PI]];
  for (const [cx, cz, a0] of corners) for (let i = 0; i <= nc; i++) {
    const t = a0 + (i / nc) * (Math.PI / 2), nx = Math.cos(t), nz = Math.sin(t);
    pts.push({ x: cx + R * nx, z: cz + R * nz, nx, nz });
  }
  return pts;
}

let keyGeo = null;
export function keyGeometry() {
  if (keyGeo) return keyGeo;
  const { w, d, r, bevel: rho, H } = KEY, ring = roundedRectPoints(w / 2, d / 2, r, 8), n = ring.length;
  const prof = [], nb = 6;                          // [offset from wall, y, normal-up, normal-out]
  for (let j = 0; j <= nb; j++) { const th = (j / nb) * Math.PI / 2; prof.push([-rho + rho * Math.sin(th), -rho + rho * Math.cos(th), Math.cos(th), Math.sin(th)]); }
  prof.push([0, -H, 0, 1]);
  const pos = [0, 0, 0], nor = [0, 1, 0], idx = [];
  for (const [o, y, up, out] of prof) for (const p of ring) { pos.push(p.x + p.nx * o, y, p.z + p.nz * o); nor.push(p.nx * out, up, p.nz * out); }
  const at = (j, i) => 1 + j * n + (i % n);
  const cap0 = pos.length / 3;                      // flat cap: its own ring with pure up normals (no gradient across the face)
  for (const p of ring) { pos.push(p.x - p.nx * rho, 0, p.z - p.nz * rho); nor.push(0, 1, 0); }
  for (let i = 0; i < n; i++) idx.push(0, cap0 + ((i + 1) % n), cap0 + i);
  for (let j = 0; j < prof.length - 1; j++) for (let i = 0; i < n; i++) idx.push(at(j, i), at(j, i + 1), at(j + 1, i), at(j, i + 1), at(j + 1, i + 1), at(j + 1, i));
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3)); g.setIndex(idx);
  orientOutward(g); return (keyGeo = g);
}
// make the triangle winding agree with the analytic normals (front faces point outward)
function orientOutward(g) {
  const P = g.attributes.position, N = g.attributes.normal, I = g.index.array;
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), m = new THREE.Vector3(), t = new THREE.Vector3();
  for (let k = 0; k < I.length; k += 3) {
    a.fromBufferAttribute(P, I[k]); b.fromBufferAttribute(P, I[k + 1]).sub(a); c.fromBufferAttribute(P, I[k + 2]).sub(a);
    m.fromBufferAttribute(N, I[k]).add(t.fromBufferAttribute(N, I[k + 1])).add(t.fromBufferAttribute(N, I[k + 2]));
    if (b.cross(c).dot(m) < 0) { const s = I[k + 1]; I[k + 1] = I[k + 2]; I[k + 2] = s; }
  }
  g.index.needsUpdate = true;
}

function rrPath(p, cx, cy, W, D, R) {               // rounded rectangle in the shape's (x, y) plane, centred
  const x0 = cx - W / 2, y0 = cy - D / 2;
  p.moveTo(x0 + R, y0); p.lineTo(x0 + W - R, y0); p.quadraticCurveTo(x0 + W, y0, x0 + W, y0 + R);
  p.lineTo(x0 + W, y0 + D - R); p.quadraticCurveTo(x0 + W, y0 + D, x0 + W - R, y0 + D); p.lineTo(x0 + R, y0 + D);
  p.quadraticCurveTo(x0, y0 + D, x0, y0 + D - R); p.lineTo(x0, y0 + R); p.quadraticCurveTo(x0, y0, x0 + R, y0);
}
// face plate with one socket per cell (missing dimensions keep their socket); top surface at y = 0
export function plateGeometry(L) {
  const s = new THREE.Shape(), m = KEY.seam, e = PLATE.edgeBevel;
  rrPath(s, 0, 0, L.bodyW - 2 * e, L.bodyD - 2 * e, PLATE.cornerR);
  for (let r = 0; r < L.rows; r++) for (let c = 0; c < L.cols; c++) {
    const [x, z] = L.pos(r, c), h = new THREE.Path();
    rrPath(h, x, -z, KEY.w + 2 * m + 2 * e, KEY.d + 2 * m + 2 * e, KEY.r + m + e); s.holes.push(h);
  }
  const g = new THREE.ExtrudeGeometry(s, { depth: PLATE.t - 2 * e, bevelEnabled: true, bevelThickness: e, bevelSize: e, bevelSegments: 3, curveSegments: 10 });
  g.rotateX(-Math.PI / 2); g.translate(0, -(PLATE.t - e), 0); g.computeVertexNormals();
  return g;
}

// rounded-rectangle outline (ring) lying in the x-z plane
export function roundedRectRing(w, d, r, t) {
  const s = new THREE.Shape(), h = new THREE.Path();
  rrPath(s, 0, 0, w + t, d + t, r + t / 2); rrPath(h, 0, 0, w, d, r); s.holes.push(h);
  const g = new THREE.ShapeGeometry(s, 8); g.rotateX(-Math.PI / 2); return g;
}

// soft contact shadow: one shared texture, placed under each key and offset away from the top-right light
let shadowTex = null;
export function contactShadowTexture() {
  if (shadowTex) return shadowTex;
  const W = 320, Hh = 160, c = document.createElement('canvas'); c.width = W; c.height = Hh;
  const g = c.getContext('2d'); g.filter = 'blur(13px)'; g.fillStyle = '#000';
  const p = new Path2D(); p.roundRect(46, 40, W - 92, Hh - 80, 22); g.fill(p);
  shadowTex = new THREE.CanvasTexture(c); shadowTex.colorSpace = THREE.NoColorSpace; return shadowTex;
}
// recessed cavity of an empty socket: occlusion darkest at the walls, softer towards the floor centre (alpha = darkness)
let cavityTex = null;
export function cavityTexture() {
  if (cavityTex) return cavityTex;
  const W = 320, Hh = 140, c = document.createElement('canvas'); c.width = W; c.height = Hh;
  const g = c.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0, 0, W, Hh);
  g.globalCompositeOperation = 'destination-out'; g.filter = 'blur(14px)';
  const p = new Path2D(); p.roundRect(30, 26, W - 60, Hh - 52, 18); g.fill(p);
  cavityTex = new THREE.CanvasTexture(c); cavityTex.colorSpace = THREE.NoColorSpace; return cavityTex;
}

// studio environment: one large diffuse softbox to the upper right (key light), a weak broad fill from the lower left,
// a neutral grey room. Key tops face the camera and do not mirror the softbox (no glare over the data colour); the
// rolled bevels catch it, which is what reads as lacquer.
const envCache = new WeakMap();
export function useStudioEnvironment(gl, scene) {
  if (envCache.has(scene)) return;
  const room = new THREE.Scene();
  room.add(new THREE.Mesh(new THREE.BoxGeometry(30, 30, 30), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.3, 0.3, 0.3), side: THREE.BackSide })));
  const panel = (w, h, p, k) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(k, k, k), side: THREE.DoubleSide }));
    m.position.set(...p); m.lookAt(0, 0, 0); room.add(m);
  };
  panel(12, 12, [9, 8, -8], 5.0);     // key softbox, upper right
  panel(16, 8, [-7, 3, 10], 2.2);     // broad fill from the front-left: key walls read as the key colour, darker
  const pm = new THREE.PMREMGenerator(gl), env = pm.fromScene(room, 0.06).texture;
  scene.environment = env; envCache.set(scene, env); pm.dispose();
}

const textCache = new Map();
export function textTexture(lines, { size = 44, weight = 600, color = '#33302b', align = 'center', width = 512, height = 128, sub = 0.62 } = {}) {
  const key = JSON.stringify([lines, size, weight, color, align, width, height, sub]);
  if (textCache.has(key)) return textCache.get(key);
  const c = document.createElement('canvas'); c.width = width; c.height = height;
  const g = c.getContext('2d'); g.clearRect(0, 0, width, height); g.fillStyle = color; g.textBaseline = 'middle';
  g.textAlign = align; const x = align === 'center' ? width / 2 : align === 'left' ? 6 : width - 6;
  const L = Array.isArray(lines) ? lines : [lines];
  const sizes = L.map((_, i) => (i === 0 ? size : size * sub));
  const total = sizes.reduce((a, b) => a + b * 1.18, 0);
  let y = height / 2 - total / 2;
  L.forEach((t, i) => { g.font = `${i === 0 ? weight : 500} ${sizes[i]}px Inter, system-ui, sans-serif`; g.globalAlpha = i === 0 ? 1 : 0.82;
    y += sizes[i] * 0.59; g.fillText(t, x, y); y += sizes[i] * 0.59; });
  const tex = new THREE.CanvasTexture(c); tex.anisotropy = 4; tex.colorSpace = THREE.SRGBColorSpace;
  const out = { texture: tex, aspect: width / height }; textCache.set(key, out); return out;
}
