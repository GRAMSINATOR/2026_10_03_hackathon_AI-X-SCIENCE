// Evidence Field as a physical instrument: lacquered keys seated in the sockets of a white polymer face plate, seen
// straight-on through an orthographic camera (no perspective: every key has identical apparent size). A small fixed
// tilt only lets the key walls read. Physicality comes from thickness, edge geometry, material, a diffuse top-right
// light and soft contact shadows. Selection = depth: the selected key is seated deeper, immediately (no travel animation).
import { useMemo, useRef, useEffect, useState, useCallback } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { keyVisual, structureVisual, categoryInfo } from '../model/adapter.js';
import { MATERIAL, mix, hexToRgb } from '../model/palette.js';
import { populationSchedule, keyPhase } from '../model/wave.js';
import { KEY, PLATE, keyElevation, keyGeometry, plateGeometry, roundedRectRing, contactShadowTexture, cavityTexture, textTexture, useStudioEnvironment } from './resources.js';

export const TILT = 0.2;          // radians from straight-down; orthographic, so rows and columns never foreshorten unequally
const FLOOR_Y = -0.3;             // socket floor (inside the plate)
const UNRESOLVED = '#dddcd7';     // key colour before the population wave reaches it
const reduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export function layoutField(M) {
  const cols = M.columns.length, rows = M.rows.length;
  const gridW = cols * KEY.w + (cols - 1) * KEY.gap, gridD = rows * KEY.d + (rows - 1) * KEY.gap;
  const labelW = 1.62, headerD = 0.62, mx = 0.3, mz = 0.28;
  const bodyW = labelW + gridW + 2 * mx, bodyD = headerD + gridD + 2 * mz;
  const x0 = -bodyW / 2 + mx + labelW, z0 = -bodyD / 2 + mz + headerD;
  const pos = (r, c) => [x0 + c * (KEY.w + KEY.gap) + KEY.w / 2, z0 + r * (KEY.d + KEY.gap) + KEY.d / 2];
  return { cols, rows, gridW, gridD, bodyW, bodyD, x0, z0, labelX: -bodyW / 2 + mx, headerZ: -bodyD / 2 + mz + headerD / 2, pos };
}
const viewHeight = L => L.bodyD * Math.cos(TILT) + (PLATE.t + KEY.up) * Math.sin(TILT) + 0.04;

const FINISH = { gloss: [0.34, 0.75, 0.24], matte: [0.8, 0, 0.8], glass: [0.22, 0.6, 0.15] };
function targetMaterial(v) {
  let col = v.finish === 'glass' ? MATERIAL.glass : mix(MATERIAL.ivory, v.hue, v.chroma);
  if (v.ghost) col = mix(col, MATERIAL.ghost, 0.55);
  const f = FINISH[v.finish] || FINISH.gloss;
  return { color: col, roughness: f[0], clearcoat: f[1], clearcoatRoughness: f[2],
           emissive: v.emissive > 0 ? v.hue : '#000000', emissiveIntensity: v.emissive * 0.6 };
}
const lum = hex => { const [r, g, b] = hexToRgb(hex); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
// typography carries salience through contrast only: same size and position on every key
function inkFor(v, colour) {
  if (lum(colour) < 0.5) return v.ink === 'soft' ? 'rgba(255,255,255,0.72)' : '#ffffff';
  return { full: MATERIAL.ink, medium: '#4b4944', soft: MATERIAL.inkSoft }[v.ink] || MATERIAL.ink;
}

const SHADOW = { up: { dx: -0.075, dz: 0.09, opacity: 0.4, s: 1 }, pressed: { dx: -0.02, dz: 0.025, opacity: 0.14, s: 0.93 } };

function Key({ k, pos, vis, t0, sched, onSelect }) {
  const mat = useRef(), lmat = useRef();
  // keyed on colour inputs only: pressing a key must not restart a colour transition
  const target = useMemo(() => targetMaterial(vis), [vis.hue, vis.chroma, vis.finish, vis.ghost, vis.emissive]);   // eslint-disable-line react-hooks/exhaustive-deps
  const cur = useRef(null), trans = useRef({ target: null, ts: 0, from: null });
  const { invalidate, clock } = useThree();
  const text = useMemo(() => (vis.showValue ? textTexture(vis.sub ? [k.valueText, vis.sub] : k.valueText,
    { color: inkFor(vis, target.color), size: 46, width: 320, height: 128, sub: 0.6 }) : null), [k, vis, target.color]);
  useFrame(() => {
    if (!mat.current) return;
    const now = clock.getElapsedTime() * 1000;
    const ph = keyPhase((clock.getElapsedTime() - t0.current) * 1000, sched.starts[k.id] || 0, sched.duration, reduced || t0.current < 0);
    // colour transitions between stages are time-based (240 ms ease-out from a snapshot); key travel is never animated
    const c = cur.current || (cur.current = { color: new THREE.Color(target.color), e: new THREE.Color(target.emissive), ei: target.emissiveIntensity });
    const tr = trans.current;
    if (tr.target !== target) { tr.target = target; tr.ts = now; tr.from = { color: c.color.clone(), e: c.e.clone(), ei: c.ei }; }
    const q = Math.min(1, (now - tr.ts) / 240), a = reduced ? 1 : 1 - (1 - q) ** 3, f = tr.from;
    c.color.copy(f.color).lerp(new THREE.Color(target.color), a); c.e.copy(f.e).lerp(new THREE.Color(target.emissive), a);
    c.ei = f.ei + (target.emissiveIntensity - f.ei) * a;
    mat.current.color.copy(new THREE.Color(UNRESOLVED).lerp(new THREE.Color(MATERIAL.ivory), ph.material).lerp(c.color, ph.colour));
    mat.current.roughness = target.roughness; mat.current.clearcoat = target.clearcoat; mat.current.clearcoatRoughness = target.clearcoatRoughness;
    mat.current.emissive.copy(c.e).lerp(new THREE.Color('#ffffff'), ph.edge * 0.5);
    mat.current.emissiveIntensity = c.ei * ph.colour + ph.edge * 0.18;
    if (lmat.current) lmat.current.opacity = ph.text;
    if (!(ph.p >= 1 && (a >= 1 || reduced))) invalidate();
  });
  const click = e => { e.stopPropagation(); if (e.delta < 5) onSelect(k.id); };
  const st = vis.selected ? SHADOW.pressed : SHADOW.up;
  const top = keyElevation(vis.selected);                     // immediate: no spring, easing or interpolation
  return (
    <group position={[pos[0], 0, pos[1]]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[st.dx, 0.0015, st.dz]} scale={[st.s, st.s, 1]} renderOrder={1}>
        <planeGeometry args={[KEY.w + 0.5, KEY.d + 0.42]} />
        <meshBasicMaterial map={contactShadowTexture()} color="#2e2c28" transparent opacity={st.opacity} depthWrite={false} toneMapped={false} />
      </mesh>
      <group position={[0, top, 0]}>
        <mesh geometry={keyGeometry()} onClick={click}
              onPointerOver={e => { e.stopPropagation(); document.body.style.cursor = 'pointer'; }} onPointerOut={() => { document.body.style.cursor = ''; }}>
          <meshPhysicalMaterial ref={mat} color={UNRESOLVED} roughness={0.34} clearcoat={0.75} clearcoatRoughness={0.24}
                                envMapIntensity={vis.selected ? 0.5 : 0.8} />
        </mesh>
        {text && (
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.002, 0]} renderOrder={3}>
            <planeGeometry args={[1.14, 0.456]} />
            <meshBasicMaterial ref={lmat} map={text.texture} transparent opacity={0} depthWrite={false} toneMapped={false} />
          </mesh>
        )}
      </group>
    </group>
  );
}

// an empty socket: the dimension was never acquired. Same footprint, no key, recessed occluded cavity.
function Socket({ k, pos, vis, onSelect }) {
  const ring = useMemo(() => roundedRectRing(KEY.w + 2 * KEY.seam + 0.05, KEY.d + 2 * KEY.seam + 0.05, KEY.r + KEY.seam + 0.025, 0.035), []);
  const click = e => { e.stopPropagation(); if (e.delta < 5) onSelect(k.id); };
  return (
    <group position={[pos[0], 0, pos[1]]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, FLOOR_Y + 0.002, 0]} onClick={click}
            onPointerOver={e => { e.stopPropagation(); document.body.style.cursor = 'pointer'; }} onPointerOut={() => { document.body.style.cursor = ''; }}>
        <planeGeometry args={[KEY.w + 2 * KEY.seam + 0.06, KEY.d + 2 * KEY.seam + 0.06]} />
        <meshBasicMaterial map={cavityTexture()} color="#000" transparent opacity={vis.selected ? 0.6 : 0.38} depthWrite={false} toneMapped={false} />
      </mesh>
      {vis.ring && (
        <mesh geometry={ring} position={[0, 0.003, 0]}>
          <meshBasicMaterial color={vis.ring} transparent opacity={0.35 + 0.6 * vis.ringStrength} toneMapped={false} />
        </mesh>
      )}
    </group>
  );
}

function FocusRing({ pos }) {   // keyboard focus only (independent of the pressed selection state)
  const ring = useMemo(() => roundedRectRing(KEY.w + 2 * KEY.seam + 0.09, KEY.d + 2 * KEY.seam + 0.09, KEY.r + KEY.seam + 0.045, 0.03), []);
  return <mesh geometry={ring} position={[pos[0], 0.004, pos[1]]}><meshBasicMaterial color={MATERIAL.ink} toneMapped={false} /></mesh>;
}

function Engraving({ lines, position, w, h, align = 'center', color = MATERIAL.engrave, size = 40, sub = 0.6, weight = 600 }) {
  const t = useMemo(() => textTexture(lines, { color, size, align, width: Math.round(256 * w), height: Math.round(256 * h), sub, weight }), [lines, color, size, align, w, h, sub, weight]);
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={position} renderOrder={2}>
      <planeGeometry args={[w, h]} />
      <meshBasicMaterial map={t.texture} transparent depthWrite={false} toneMapped={false} />
    </mesh>
  );
}

function Body({ L, struct, M, stage }) {
  const plate = useMemo(() => plateGeometry(L), [L]);
  return (
    <group>
      <mesh geometry={plate}>
        <meshPhysicalMaterial color={MATERIAL.body} roughness={0.58} clearcoat={0.25} clearcoatRoughness={0.45} envMapIntensity={0.7} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, FLOOR_Y, 0]}>
        <planeGeometry args={[L.bodyW - 0.2, L.bodyD - 0.2]} />
        <meshStandardMaterial color={MATERIAL.cavity} roughness={1} envMapIntensity={0.4} />
      </mesh>
      {M.columns.map(c => {
        const [x] = L.pos(0, c.index);
        let sub = c.unit;
        if (!c.acquired) sub = 'not acquired';
        else if (stage === 2) sub = `MDC ±${(c.mdc * c.factor).toPrecision(2)}${c.unit === '%' ? ' pt' : ''}`;
        else if (stage >= 3 && c.spatial) sub = c.spatial.cls === 'short-range' ? 'short-range' : c.spatial.cls === 'fov-scale' ? `≈${Math.round(c.spatial.range_um)} µm` : `>${Math.round(c.spatial.range_um)} µm`;
        const acc = struct.cols[c.id] && struct.cols[c.id].accent;
        return <Engraving key={c.id} lines={[c.short, sub || ' ']} position={[x, 0.002, L.headerZ]} w={1.42} h={0.52} size={42}
                          color={acc ? mix(acc, MATERIAL.ink, 0.25) : c.acquired ? MATERIAL.engrave : '#9b978f'} />;
      })}
      {M.rows.map(r => {
        const [, z] = L.pos(r.index, 0);
        const sub = r.refLinked && stage >= 1 ? 'reference-linked' : `${r.nFields} field${r.nFields > 1 ? 's' : ''} · ${Math.round(r.sectionUm)} µm`;
        const acc = struct.rows[r.id] && struct.rows[r.id].accent;
        return (
          <group key={r.id}>
            <Engraving lines={[r.id, sub]} position={[L.labelX + 0.82, 0.002, z]} w={1.6} h={0.48} align="left" size={52}
                       color={r.refLinked && stage >= 1 ? '#a19d95' : '#3d3b37'} />
            {acc && <mesh position={[L.labelX - 0.08, 0.003, z]} rotation={[-Math.PI / 2, 0, 0]}>
              <planeGeometry args={[0.06, 0.42]} /><meshBasicMaterial color={acc} toneMapped={false} /></mesh>}
          </group>
        );
      })}
      {struct.rail && (
        <mesh position={[0, 0.003, L.bodyD / 2 - 0.13]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[L.gridW, 0.045]} />
          <meshBasicMaterial color={struct.rail.hue} transparent opacity={0.3 + 0.6 * struct.rail.strength} toneMapped={false} />
        </mesh>
      )}
    </group>
  );
}

function Scene({ M, stage, sel, onSelectKey, ready, focus }) {
  const { gl, scene, camera, size, invalidate, clock } = useThree();
  useEffect(() => { useStudioEnvironment(gl, scene); gl.toneMapping = THREE.LinearToneMapping; gl.toneMappingExposure = 0.92; invalidate();
                    (window.__gl = window.__gl || {}).field = gl.info; }, [gl, scene, invalidate]);
  const L = useMemo(() => layoutField(M), [M]);
  useEffect(() => {   // orthographic, straight-on; zoom fits the plate exactly to the canvas
    camera.position.set(0, 40 * Math.cos(TILT), 40 * Math.sin(TILT)); camera.up.set(0, 1, 0); camera.lookAt(0, 0, 0);
    camera.zoom = Math.min(size.width / (L.bodyW * 1.004), size.height / viewHeight(L)); camera.updateProjectionMatrix(); invalidate();
  }, [camera, size, L, invalidate]);
  const sched = useMemo(() => populationSchedule(M.keys.map(k => ({ id: k.id, row: k.row, col: k.col }))), [M]);
  const t0 = useRef(-1);
  useEffect(() => { if (ready) { t0.current = clock.getElapsedTime(); invalidate(); } }, [ready, clock, invalidate]);
  const struct = useMemo(() => structureVisual(M, stage, sel), [M, stage, sel]);
  const visuals = useMemo(() => Object.fromEntries(M.keys.map(k => [k.id, keyVisual(M, k, stage, sel)])), [M, stage, sel]);
  return (
    <>
      <hemisphereLight args={['#ffffff', '#b9b6ae', 0.55]} />
      <directionalLight position={[4.5, 8, -4]} intensity={1.35} />
      <Body L={L} struct={struct} M={M} stage={stage} />
      {M.keys.map(k => k.kind === 'missing'
        ? <Socket key={k.id} k={k} pos={L.pos(k.row, k.col)} vis={visuals[k.id]} onSelect={onSelectKey} />
        : <Key key={k.id} k={k} pos={L.pos(k.row, k.col)} vis={visuals[k.id]} t0={t0} sched={sched} onSelect={onSelectKey} />)}
      {focus && <FocusRing pos={L.pos(focus.row, focus.col)} />}
    </>
  );
}

export default function Instrument({ M, stage, sel, onSelectKey, onClear }) {
  const [ready, setReady] = useState(false);
  useEffect(() => { (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => setReady(true)); }, []);
  const L = useMemo(() => layoutField(M), [M]);
  // keyboard: arrows move an accessible focus (drawn as its own ring), Enter/Space presses the key, Escape releases
  const [kbd, setKbd] = useState(false), [focusRC, setFocusRC] = useState({ row: 0, col: 0 });
  const keyAt = useCallback((r, c) => M.keys.find(k => k.row === r && k.col === c), [M]);
  const onKeyDown = e => {
    const mv = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] }[e.key];
    if (mv) { e.preventDefault(); setKbd(true); setFocusRC(f => ({ row: Math.max(0, Math.min(L.rows - 1, f.row + mv[0])), col: Math.max(0, Math.min(L.cols - 1, f.col + mv[1])) })); }
    else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setKbd(true); const k = keyAt(focusRC.row, focusRC.col); if (k) onSelectKey(k.id); }
    else if (e.key === 'Escape') onClear();
  };
  const fk = keyAt(focusRC.row, focusRC.col), fv = fk && keyVisual(M, fk, stage, sel), fc = fk && M.columns.find(c => c.id === fk.dimension);
  return (
    <div className="instrument" style={{ aspectRatio: (L.bodyW / viewHeight(L)).toFixed(4) }} tabIndex={0} role="application"
         aria-label="Evidence instrument. Arrow keys move, Enter selects, Escape clears." onKeyDown={onKeyDown}
         onPointerDown={() => setKbd(false)} onBlur={() => setKbd(false)}>
      {ready && (
        <Canvas frameloop="demand" orthographic dpr={[1, 2]} camera={{ zoom: 60, position: [0, 40, 8], near: 0.1, far: 200 }} onPointerMissed={onClear}
                gl={{ antialias: true, powerPreference: 'low-power' }}>
          <Scene M={M} stage={stage} sel={sel} onSelectKey={onSelectKey} ready={ready} focus={kbd ? focusRC : null} />
        </Canvas>
      )}
      <p className="sr-only" aria-live="polite">{kbd && fk ? `${fk.entity} · ${fc.label} · ${fk.kind === 'missing' ? 'not acquired' : fk.valueText} · ${categoryInfo(fv).label}${fv.selected ? ' · selected' : ''}` : ''}</p>
    </div>
  );
}
