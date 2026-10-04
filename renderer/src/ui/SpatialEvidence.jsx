// Flat, registered spatial evidence at native image scale. One µm x-axis is shared by the stitched micrograph and its
// segmentation overlays, the 100-µm window profile with the approved local band, the observed / unobserved extent, a
// prospective capture and the (empty) composition row. The strip is wider than the screen, so it scrolls horizontally;
// the y-axis stays pinned. Nothing here is 3D: scientific imagery is never given the lacquered-key treatment.
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { HUE } from '../model/palette.js';
import { SPATIAL_LAYER_DIMS, formatValue } from '../model/adapter.js';
import { registration, prospective } from '../model/stack.js';

const OVERLAY = { highz: { label: 'detected high-Z objects', color: [255, 190, 20], phase: 2 }, pores: { label: 'detected pores', color: [40, 150, 255], phase: 0 } };
const INK = '#1f1e1b', MUT = '#8b8880', CAPTURED = '#f5f4f0', HATCH = '#c9c7c0', OPEN_TEXT = '#0f7a55';
const AXIS_W = 64, CHART_H = 124;

const maskCache = new Map();
function useMask(uri, phase, color) {
  const [url, setUrl] = useState(maskCache.get(uri + phase) || null);
  useEffect(() => {
    if (!uri || maskCache.has(uri + phase)) { setUrl(maskCache.get(uri + phase) || null); return; }
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
      const g = c.getContext('2d'); g.drawImage(img, 0, 0);
      const d = g.getImageData(0, 0, c.width, c.height), p = d.data;
      for (let i = 0; i < p.length; i += 4) {           // labels stored as grey levels 0/1/2
        const on = phase === 2 ? p[i] >= 2 : p[i] === 0;
        p[i] = color[0]; p[i + 1] = color[1]; p[i + 2] = color[2]; p[i + 3] = on ? 215 : 0;
      }
      g.putImageData(d, 0, 0); const u = c.toDataURL(); maskCache.set(uri + phase, u); setUrl(u);
    };
    img.src = uri;
  }, [uri, phase, color]);
  return url;
}
function Overlay({ a, x, y, w, h, kind }) {
  const o = OVERLAY[kind], url = useMask(a && a.seg, o.phase, o.color);
  return url ? <image href={url} x={x} y={y} width={w} height={h} preserveAspectRatio="none" style={{ imageRendering: 'pixelated' }} /> : null;
}

export default function SpatialEvidence({ M, entity, setEntity, stage, action, assets, imagery = true, kpi, setKpi, overlays, setOverlays, highlightKpi }) {
  const scroller = useRef(null);
  const reg = useMemo(() => registration(M, entity), [M, entity]);
  const avail = useMemo(() => SPATIAL_LAYER_DIMS.filter(d => M.PROF[`${entity}:${d}`]), [M, entity]);
  const dim = avail.includes(kpi) ? kpi : (avail.find(d => ['deviant', 'out'].includes(M.OBS[`${entity}:${d}`].reference_relation.status)) || avail[0]);
  const prof = dim && M.PROF[`${entity}:${dim}`], col = M.columns.find(c => c.id === dim), obs = dim && M.OBS[`${entity}:${dim}`];
  const pro = useMemo(() => (stage === 4 && reg ? prospective(M, entity, reg, action) : null), [M, entity, reg, stage, action]);
  const miss = M.MISS[`${entity}:composition`];
  // native scale: one image pixel per screen pixel, so overlays stay crisp and readable
  const pxPerUm = useMemo(() => {
    const s = (reg ? reg.runs.flatMap(r => r.fields) : []).map(f => assets[f.id] && assets[f.id].image_px_um).filter(Boolean).sort((a, b) => a - b);
    if (!imagery) return 2;   // public mode: no imagery to resolve, so the registered evidence fits the bay
    return s.length ? Math.max(3, Math.min(6, 1 / s[Math.floor(s.length / 2)])) : 4.5;
  }, [reg, assets, imagery]);
  const geo = useMemo(() => {
    if (!reg || !prof) return null;
    const fieldW = reg.runs[0].fields[0].widthUm;
    const profs = avail.map(d => M.PROF[`${entity}:${d}`]);
    // an open edge (on any KPI of this micrograph) reserves one field of space: where the evidence would continue and
    // where EXTEND would capture next. Fixed per micrograph, so the axis never jumps between stages or KPIs.
    const openL = profs.some(p => p.runs[0].open_at_start), openR = profs.some(p => p.runs[p.runs.length - 1].open_at_end);
    const padL = openL ? fieldW * 1.06 : fieldW * 0.12, padR = openR ? fieldW * 1.06 : fieldW * 0.12;
    const dom = [-padL, reg.totalUm + padR], W = Math.round((dom[1] - dom[0]) * pxPerUm), sx = x => (x - dom[0]) * pxPerUm;
    const stripY = 20, stripH = imagery ? reg.heightUm * pxPerUm : 44, chartY = stripY + stripH + 22, compY = chartY + CHART_H + 12, H = compY + 30;
    return { padL, padR, W, sx, stripY, stripH, chartY, compY, H };
  }, [reg, prof, avail, M, entity, pxPerUm, imagery]);

  // bring the evidence that matters into view: the prospective capture (NEXT CAPTURE), else the strongest window
  useLayoutEffect(() => {
    const el = scroller.current; if (!el || !geo || !prof) return;
    let target = null;
    const r0 = prof.runs[0], rN = prof.runs[prof.runs.length - 1];
    if (pro && pro.regions.length) target = pro.regions[0].x0Um + pro.regions[0].widthUm / 2;
    else if (stage >= 3 && r0.open_at_start) target = reg.runs[0].offsetUm + el.clientWidth / (2 * pxPerUm) - geo.padL * 0.6;
    else if (stage >= 3 && rN.open_at_end) target = reg.runs[reg.runs.length - 1].offsetUm + rN.length_um - el.clientWidth / (2 * pxPerUm) + geo.padR * 0.6;
    else {
      const b = prof.reference_band, mid = (b.lo + b.hi) / 2; let best = -1;
      prof.runs.forEach((r, i) => r.window_means.forEach((v, j) => { const d = Math.abs(v - mid); if (d > best) { best = d; target = reg.runs[i].offsetUm + r.window_centres_um[j]; } }));
    }
    if (target != null) el.scrollLeft = Math.max(0, geo.sx(target) - el.clientWidth / 2);
  }, [geo, prof, pro, reg, stage, pxPerUm]);

  if (!reg || !prof || !geo) return <div className="spatial empty">No spatial profile for {entity}.</div>;
  const { padL, padR, W, sx, stripY, stripH, chartY, compY, H } = geo;
  const b = prof.reference_band, vals = [b.lo, b.hi];
  prof.runs.forEach(r => { r.column_values.forEach(v => vals.push(v)); r.window_means.forEach(v => vals.push(v)); });
  const vmin = Math.min(...vals), vmax = Math.max(...vals), pd = (vmax - vmin) * 0.1 || 1;
  const sy = v => chartY + 8 + (CHART_H - 16) * (1 - (v - vmin + pd) / (vmax - vmin + 2 * pd));
  const fmt = v => (v * col.factor).toPrecision(3);
  const showOpen = stage >= 3, emphBand = stage === 2, compHot = miss && miss.consequential && stage >= 3;
  const segs = [];
  prof.runs.forEach((r, i) => {
    for (let j = 1; j < r.window_centres_um.length; j++) {
      const v = (r.window_means[j] + r.window_means[j - 1]) / 2, c = v > b.hi ? HUE.above : v < b.lo ? HUE.below : INK;
      segs.push(<line key={`${i}-${j}`} x1={sx(reg.runs[i].offsetUm + r.window_centres_um[j - 1])} y1={sy(r.window_means[j - 1])}
                      x2={sx(reg.runs[i].offsetUm + r.window_centres_um[j])} y2={sy(r.window_means[j])} stroke={c} strokeWidth={2.6} strokeLinecap="round" />);
    }
  });
  const ticks = [vmin, (vmin + vmax) / 2, vmax];
  const nFields = reg.runs.reduce((n, r) => n + r.fields.length, 0);
  return (
    <div className="spatial">
      <div className="sp-bar">
        <div className="sp-ent">{M.rows.map(r => <button key={r.id} className={r.id === entity ? 'on' : ''} onClick={() => setEntity(r.id)}>{r.id}</button>)}</div>
        <div className="sp-kpi">{avail.map(d => { const c = M.columns.find(x => x.id === d); return (
          <button key={d} className={`${d === dim ? 'on' : ''} ${highlightKpi === d ? 'hl' : ''}`} onClick={() => setKpi(d)}>{c.short}</button>); })}</div>
        {imagery && <div className="sp-ov">{Object.entries(OVERLAY).map(([k, o]) => (
          <label key={k}><input type="checkbox" checked={!!overlays[k]} onChange={e => setOverlays({ ...overlays, [k]: e.target.checked })} />
            <i style={{ background: `rgb(${o.color.join(',')})` }} />{o.label}</label>))}</div>}
        {!imagery && <span className="sp-withheld">micrograph imagery withheld · public mode shows derived numbers only</span>}
        <span className="sp-key"><i className="hatch" />not captured
          <i style={{ background: MUT }} />25 µm columns · context
          <i style={{ background: HUE.above }} />100 µm local means · compared
          <i style={{ background: HUE.population, opacity: 0.6 }} />parent-bootstrap envelope
          <i style={{ background: HUE.spatial }} />open edge <em>· {imagery ? 'native scale, ' : ''}scroll ⇆</em></span>
      </div>
      <div className="sp-view">
        <svg className="sp-axisbox" width={AXIS_W} height={H} aria-hidden="true">
          <text x={4} y={stripY + 12} className="sp-axis">{nFields} field{nFields > 1 ? 's' : ''}</text>
          <text x={4} y={stripY + 27} className="sp-tick">{Math.round(reg.totalUm)} µm</text>
          <text x={4} y={stripY + 42} className="sp-tick">captured</text>
          <text x={AXIS_W - 6} y={chartY - 6} className="sp-tick" textAnchor="end">{col.unit}</text>
          {ticks.map((t, i) => <text key={i} x={AXIS_W - 6} y={sy(t) + 4} className="sp-tick" textAnchor="end">{fmt(t)}</text>)}
          <text x={4} y={compY + 13} className="sp-tick">chemistry</text>
        </svg>
        <div className="sp-scroll" ref={scroller} tabIndex={0} aria-label="registered strip, scroll horizontally">
          <svg width={W} height={H} role="img" aria-label={`registered spatial evidence for ${entity}: raw 25 micrometre columns and unsmoothed 100 micrometre local means for ${col.label}, compared with a descriptive ${b.n_parents}-parent bootstrap envelope`}>
            <defs>
              <linearGradient id="openL" x1="1" x2="0"><stop offset="0" stopColor={HUE.spatial} stopOpacity="0.4" /><stop offset="1" stopColor={HUE.spatial} stopOpacity="0" /></linearGradient>
              <linearGradient id="openR" x1="0" x2="1"><stop offset="0" stopColor={HUE.spatial} stopOpacity="0.4" /><stop offset="1" stopColor={HUE.spatial} stopOpacity="0" /></linearGradient>
              <pattern id="unobs" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke={HATCH} strokeWidth="1.6" /></pattern>
            </defs>
            {/* not captured everywhere; captured runs on top */}
            <rect x={0} y={stripY} width={W} height={stripH} fill="url(#unobs)" />
            <rect x={0} y={chartY} width={W} height={CHART_H} fill="url(#unobs)" />
            {reg.runs.map((r, i) => <rect key={'c' + i} x={sx(r.offsetUm)} y={chartY} width={r.lengthUm * pxPerUm} height={CHART_H} fill={CAPTURED} />)}
            {/* micrograph at native scale + registered overlays */}
            {reg.runs.flatMap(r => r.fields).map(f => {
              const a = assets[f.id], x = sx(f.x0Um), w = f.widthUm * pxPerUm, h = f.heightUm * pxPerUm, isBatch = f.batch === M.meta.batch;
              const v = obs && obs.per_field && obs.per_field[f.id];
              return (
                <g key={f.id}>
                  {imagery && a && a.bse && <image href={a.bse} x={x} y={stripY} width={w} height={h} preserveAspectRatio="none" />}
                  {!imagery && <><rect x={x} y={stripY} width={w} height={stripH} fill={CAPTURED} />
                    <text x={x + w / 2} y={stripY + stripH / 2 + 4} textAnchor="middle" className="sp-note dim">field footprint · image withheld</text></>}
                  {imagery && overlays.pores && <Overlay a={a} x={x} y={stripY} w={w} h={h} kind="pores" />}
                  {imagery && overlays.highz && <Overlay a={a} x={x} y={stripY} w={w} h={h} kind="highz" />}
                  <rect x={x} y={stripY} width={w} height={imagery ? h : stripH} fill="none" stroke={isBatch ? INK : '#9b978f'} strokeWidth={isBatch ? 1.2 : 1} />
                  <text x={x + 4} y={stripY - 6} className="sp-tick" fill={isBatch ? INK : MUT}>{f.id.split('__')[1]} · {f.batch.replace('Batch_', 'B')}{isBatch ? '' : ' (other batch)'}
                    {v != null && <tspan className="sp-val" dx={10}>{col.short} {formatValue(v, col)} {col.unit}</tspan>}</text>
                </g>);
            })}
            {reg.runs.length > 1 && reg.runs.slice(1).map((r, i) => { const prev = reg.runs[i], cx = sx((prev.offsetUm + prev.lengthUm + r.offsetUm) / 2); return (
              <text key={'g' + i} x={cx} y={stripY + stripH / 2} className="sp-note dim" textAnchor="middle"><tspan x={cx}>gap</tspan><tspan x={cx} dy={13}>separation</tspan><tspan x={cx} dy={13}>unknown</tspan></text>); })}
            {pro && pro.regions.map((g, i) => (
              <g key={'p' + i}>
                <rect x={sx(g.x0Um)} y={stripY} width={g.widthUm * pxPerUm} height={stripH} fill={INK} fillOpacity={0.04} stroke={INK} strokeDasharray="7 5" strokeWidth={1.6} />
                <text x={sx(g.x0Um + g.widthUm / 2)} y={stripY + stripH / 2 + 4} textAnchor="middle" className="sp-note" fill={INK}>
                  {g.side === 'same' ? 'repeat · same footprint (prospective)' : 'next field · prospective capture'}</text>
              </g>))}
            {/* ruler edge between image and profile: ticks every 25 µm (profile column), long ticks every 100 µm (window) */}
            {reg.runs.map((r, i) => (
              <g key={'ru' + i}>
                <rect x={sx(r.offsetUm)} y={stripY + stripH + 6} width={r.lengthUm * pxPerUm} height={9} fill="#d9d6cf" />
                <rect x={sx(r.offsetUm)} y={stripY + stripH + 6} width={r.lengthUm * pxPerUm} height={1} fill="rgba(52,46,38,.25)" />
                {Array.from({ length: Math.floor(r.lengthUm / 25) + 1 }, (_, j) => (
                  <line key={j} x1={sx(r.offsetUm + 25 * j)} x2={sx(r.offsetUm + 25 * j)} y1={stripY + stripH + 6} y2={stripY + stripH + (j % 4 === 0 ? 15 : 10)}
                        stroke="#6f6c66" strokeWidth={j % 4 === 0 ? 1.2 : 0.8} />))}
              </g>))}
            {/* profile: approved local band, 25-µm columns, 100-µm windows coloured against the band */}
            {reg.runs.map((r, i) => (
              <g key={'b' + i}>
                <rect x={sx(r.offsetUm)} y={sy(b.hi)} width={r.lengthUm * pxPerUm} height={sy(b.lo) - sy(b.hi)} fill={HUE.population} opacity={emphBand ? 0.26 : 0.13} />
                <line x1={sx(r.offsetUm)} x2={sx(r.offsetUm + r.lengthUm)} y1={sy(b.hi)} y2={sy(b.hi)} stroke={HUE.population} strokeOpacity={0.75} strokeDasharray="3 3" />
                <line x1={sx(r.offsetUm)} x2={sx(r.offsetUm + r.lengthUm)} y1={sy(b.lo)} y2={sy(b.lo)} stroke={HUE.population} strokeOpacity={0.75} strokeDasharray="3 3" />
                <text x={sx(r.offsetUm) + 6} y={sy(b.lo) - sy(b.hi) > 18 ? sy(b.hi) + 13 : sy(b.hi) - 5} className="sp-note" fill="#5a3fb0">
                  {`${b.label || 'PARENT-BOOTSTRAP ENVELOPE'} · 100 µm means · ${b.n_parents} parents · descriptive`}</text>
              </g>))}
            {prof.runs.map((r, i) => r.column_centres_um.map((x, j) => (
              <circle key={`${i}-c${j}`} cx={sx(reg.runs[i].offsetUm + x)} cy={sy(r.column_values[j])} r={2.3} fill={MUT} opacity={0.55} />)))}
            {segs}
            {showOpen && prof.runs.map((r, i) => (
              <g key={'o' + i}>
                {r.open_at_start && <><rect x={sx(reg.runs[i].offsetUm) - padL * pxPerUm * 0.8} y={chartY} width={padL * pxPerUm * 0.8} height={CHART_H} fill="url(#openL)" />
                  <text x={sx(reg.runs[i].offsetUm) + 8} y={chartY + 14} className="sp-note" fill={OPEN_TEXT}>◀ open edge: local mean still outside the envelope; extent not bounded</text></>}
                {r.open_at_end && <><rect x={sx(reg.runs[i].offsetUm + r.length_um)} y={chartY} width={padR * pxPerUm * 0.8} height={CHART_H} fill="url(#openR)" />
                  <text x={sx(reg.runs[i].offsetUm + r.length_um) - 8} y={chartY + 14} textAnchor="end" className="sp-note" fill={OPEN_TEXT}>open edge ▶</text></>}
              </g>))}
            {/* composition: never filled, because nothing was measured */}
            {reg.runs.map((r, i) => (
              <rect key={'m' + i} x={sx(r.offsetUm)} y={compY} width={r.lengthUm * pxPerUm} height={18} rx={4} fill="none"
                    stroke={compHot ? HUE.composition : '#a19d95'} strokeDasharray="5 4" />))}
            {reg.runs.flatMap(r => r.fields).map(f => (   /* repeated per field so it stays legible while scrolling */
              <text key={'ct' + f.id} x={sx(f.x0Um) + 8} y={compY + 13} className="sp-note" fill={compHot ? '#b0287a' : MUT}>
                composition: not acquired{miss && miss.consequential ? ' (consequential for this micrograph)' : ''}</text>))}
            <line x1={sx(reg.totalUm) - 100 * pxPerUm} x2={sx(reg.totalUm)} y1={compY + 26} y2={compY + 26} stroke={INK} strokeWidth={2} />
            <text x={sx(reg.totalUm) - 100 * pxPerUm - 6} y={compY + 30} textAnchor="end" className="sp-tick">100 µm</text>
          </svg>
        </div>
      </div>
    </div>
  );
}
