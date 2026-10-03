"""V1 EXPLORATORY / DIAGNOSTIC RENDERER for the uncertainty field (contract `epistemic-field/1`).

This is one possible renderer, not the product's canonical representation. It consumes ONLY the field JSON (plus image
assets) and contains no scientific rules: every visual mapping below (brightness, hatching, flicker, ring hue/width,
glyphs, row order, spacing between unconnected runs, the 5-step disclosure) is a presentation choice over contract
fields. See docs/REPRESENTATION_CONTRACT.md.
"""
import base64
import io
import json
import os

from PIL import Image


def _thumbs(field, asset_dir, h=46):
    out = {}
    for f in field['provenance']['fields']:
        p = os.path.join(asset_dir, f"{f['id']}_BSE.jpg")
        if os.path.exists(p):
            im = Image.open(p).convert('L')
            im = im.resize((max(1, int(im.width * h / im.height)), h))
            b = io.BytesIO()
            im.save(b, 'JPEG', quality=70)
            out[f['id']] = 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
    return out


def render(field, asset_dir='cache/fields'):
    """field: the contract dict (e.g. json.load of reports/<batch>/field.json)."""
    assert field.get('schema_version') == 'epistemic-field/1', 'V1 renderer expects epistemic-field/1'
    data = json.dumps(dict(field=field, thumbs=_thumbs(field, asset_dir)), default=float)
    return TEMPLATE.replace('__DATA__', data)


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><title>Evidence Field · V1 exploratory renderer</title>
<style>
:root{--bg:#0d0d0d;--panel:#1a1a19;--line:rgba(255,255,255,.10);--ink:#fff;--ink2:#c3c2b7;--mut:#898781;
--up:#d95926;--down:#3987e5;--spatial:#199e70;--base:#9085e9;--scale:#c98500;--comp:#d55181;--good:#0ca30c;--warn:#fab219;--crit:#d03b3b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:13px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif}
.top{display:flex;align-items:center;gap:14px;padding:12px 16px;border-bottom:1px solid var(--line)}
.brand{font-weight:700;letter-spacing:.06em;font-size:12px;color:var(--ink2)}.brand b{color:var(--ink)}
.verdict{margin-left:auto;display:flex;gap:8px;align-items:center;padding:5px 10px;border-radius:6px;border:1px solid var(--line);background:var(--panel)}
.verdict .v{font-weight:800}.verdict .s{color:var(--ink2);font-size:12px}
.steps{display:flex;gap:6px;padding:10px 16px 0}
.step{cursor:pointer;padding:7px 12px;border-radius:7px;border:1px solid var(--line);background:#141413;color:var(--ink2);font-weight:600;font-size:12px;letter-spacing:.04em}
.step.on{background:#262624;color:var(--ink);border-color:rgba(255,255,255,.35)}.step .n{color:var(--mut);margin-right:5px}
.head{padding:8px 16px 4px;min-height:44px;font-size:15px}.head .sub{color:var(--ink2);font-size:12px;margin-top:2px}
.main{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:12px;padding:6px 16px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px}
.grid{display:grid;gap:6px;align-items:stretch}
.ch{font-size:11px;color:var(--ink2);text-align:center;padding:2px 2px 4px;line-height:1.25}
.ch b{display:block;color:var(--ink);font-size:12px}.ch .chip{display:inline-block;margin-top:3px;padding:1px 5px;border-radius:4px;font-size:10px;border:1px solid var(--line)}
.rh{display:flex;flex-direction:column;justify-content:center;padding:0 6px;border-radius:8px;cursor:pointer;font-size:11px;color:var(--ink2)}
.rh b{color:var(--ink);font-size:13px}.rh.sel{background:#262624}.rh .bd{font-size:10px;margin-top:2px}.rh.linked{opacity:.45}
.pad{position:relative;height:60px;border-radius:9px;background:#232321;border:1px solid rgba(255,255,255,.07);cursor:pointer;
display:flex;align-items:center;justify-content:center;flex-direction:column;transition:all .35s;overflow:hidden}
.pad .val{font-weight:700;font-size:13px;z-index:2}.pad .z{font-size:10px;color:var(--ink2);z-index:2}
.pad.sel{outline:2px solid #fff;outline-offset:1px}.pad.linked{opacity:.4}
.pad .gl{position:absolute;top:3px;right:5px;font-size:12px;z-index:3;letter-spacing:1px}
.pad .bl{position:absolute;bottom:2px;left:5px;font-size:10px;z-index:3;color:var(--ink2)}
.pad.unm{background:repeating-linear-gradient(45deg,transparent 0 6px,rgba(255,255,255,.05) 6px 8px)!important;border:1.5px dashed rgba(255,255,255,.25)}
.pad.comp-c{border:2px dashed var(--comp)!important}
.flick{animation:flick 1.3s infinite steps(1)}
@keyframes flick{0%{opacity:1}18%{opacity:.45}24%{opacity:1}57%{opacity:.6}61%{opacity:1}100%{opacity:1}}
.pulse{animation:pulse 1.1s infinite ease-in-out}
@keyframes pulse{0%,100%{box-shadow:0 0 0 2px #fff,0 0 18px 4px rgba(255,255,255,.55)}50%{box-shadow:0 0 0 2px #fff,0 0 4px 1px rgba(255,255,255,.15)}}
.side h3{margin:2px 0 8px;font-size:12px;letter-spacing:.08em;color:var(--ink2)}
.act{border:1px solid var(--line);border-radius:9px;padding:8px 10px;margin-bottom:7px;cursor:pointer;background:#141413}
.act.on{border-color:#fff;background:#232321}.act .t{font-weight:700}.act .meta{font-size:11px;color:var(--mut);margin-top:2px}
.verb{display:inline-block;font-size:10px;font-weight:800;letter-spacing:.06em;padding:1px 6px;border-radius:4px;margin-right:6px;background:#333;color:#fff}
.tier1 .verb{background:var(--crit)}.tier2 .verb{background:#7a6000}.tier3 .verb{background:#3a3a37}
.detail{font-size:12px;color:var(--ink2);margin-top:6px}.detail li{margin:2px 0}.detail b{color:var(--ink)}
.lower{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:12px;padding:6px 16px 16px}
.legend{font-size:11px;color:var(--ink2);display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}.legend span{white-space:nowrap}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-2px;margin-right:4px}
table.kv{width:100%;border-collapse:collapse;font-size:12px}table.kv td{padding:2px 4px;border-bottom:1px solid var(--line);vertical-align:top}
table.kv td:first-child{color:var(--mut);white-space:nowrap}
.bar{display:flex;height:10px;border-radius:3px;overflow:hidden;margin:4px 0}.muted{color:var(--mut)}.rule{font-size:11px;color:var(--ink2);margin:2px 0}
.kbtn{cursor:pointer;font-size:11px;padding:2px 7px;border-radius:5px;border:1px solid var(--line);margin-left:4px;color:var(--ink2)}.kbtn.on{color:#fff;border-color:#fff}
.tag{font-size:10px;color:var(--mut);border:1px solid var(--line);border-radius:4px;padding:1px 5px;margin-left:8px}
</style></head><body>
<div class="top"><div class="brand">EPISTEMIC ACQUISITION CONTROLLER · <b id="bname"></b> <span class="muted">vs approved <span id="rname"></span></span><span class="tag">V1 exploratory renderer</span></div>
<div class="verdict" id="verdict"></div></div>
<div class="steps" id="steps"></div><div class="head" id="head"></div>
<div class="main"><div class="panel"><div class="grid" id="grid"></div><div class="legend" id="legend"></div></div><div class="panel side" id="side"></div></div>
<div class="lower"><div class="panel"><div id="striphead" style="font-size:12px;color:var(--ink2);margin-bottom:4px"></div><svg id="strip" width="100%" height="190"></svg></div>
<div class="panel" id="drawer"></div></div>
<script>
// ---- contract access (indexing only; no scientific reasoning in this renderer)
const D=__DATA__, F=D.field;
const DIMS=F.dimensions, DIM=Object.fromEntries(DIMS.map(d=>[d.id,d]));
const OBS=Object.fromEntries(F.observations.map(o=>[o.id,o])), ENT=Object.fromEntries(F.entities.map(e=>[e.id,e]));
const MISS=Object.fromEntries(F.missing_dimensions.map(m=>[m.id,m])), PROF=Object.fromEntries(F.spatial_profiles.map(p=>[p.id,p]));
const RIM=Object.fromEntries(F.rims.map(r=>[r.id,r]));
const oid=(e,d)=>e+':'+d;
// ---- presentation choices (renderer-owned)
const ROWS=[...F.entities].sort((a,b)=>(a.independence.reference_linked-b.independence.reference_linked)||a.id.localeCompare(b.id));
const STEPS=['SIGNAL','SCRUTINY','FIELD','OUTER RIM','NEXT CAPTURE'];
const RUN_GAP_UM=60;   // visual spacing between unconnected runs (true separation unknown: contract run_separation)
let step=0, selRow=null, selCell=null, selAct=null, stripK=null;
const $=id=>document.getElementById(id);
const fmt=(v,d)=>v==null?'–':(Math.abs(v*d.display.factor)>=100?(v*d.display.factor).toFixed(0):(v*d.display.factor).toPrecision(3));
const VC={ACCEPT:['var(--good)','✓'],INVESTIGATE:['var(--warn)','!'],REJECT:['var(--crit)','✕'],REFERENCE:['var(--down)','◆']};
const GLY={spatial:['⤢','var(--spatial)'],scale:['◎','var(--scale)'],composition:['◇','var(--comp)'],acquisition:['⚡','var(--ink2)']};
const rgba=(dir,a)=>dir<0?`rgba(57,135,229,${a})`:`rgba(217,89,38,${a})`;
const status=o=>o.reference_relation.status, deviating=o=>['deviant','out'].includes(status(o));
const flicker=o=>(ENT[o.entity].acquisition.outside_tested_range.length>0)||o.acquisition_explains_deviation;
const pivotal=e=>!!(e.leverage&&e.leverage.flips);
function head(){
 const s=F.summary, a=F.actions[0]||{}, cr=s.consequential_rims.length;
 const H=[[`${s.n_deviating} observation${s.n_deviating==1?'':'s'} outside the approved envelope.`,'Brightness = exceedance ratio |z|/q95 (calibrated for each micrograph\'s sampling). Arrow = direction.'],
 [`${s.n_surviving} of ${s.n_deviating} survive scrutiny.`,'Solid = scrutiny outcome "survives". Hatched = "fails". Flicker = acquisition outside the tested range, or tested acquisition changes could explain the deviation.'],
 ['Each envelope = approved material spread + spatial sampling + baseline support.','Ring = larger reducible variance share (aqua spatial sampling, violet baseline support). Header: minimum detectable change.'],
 [`${cr} consequential rim${cr==1?'':'s'}`+(F.decision.pivotal.length?` — the verdict rests on ${F.decision.pivotal.join(', ')}.`:'.'),'⤢ spatial · ◎ scale · ◇ missing composition · ⚡ acquisition · ★ decision leverage. Strip: captured section; the band fades where nothing was observed.'],
 [`Next capture: ${a.title||'none required'}`,'Ranked by the controller (tier, then falsify → scale → identity → extent → prevalence). Select an action to light the observations it targets.']];
 $('head').innerHTML=`<div>${H[step][0]}</div><div class="sub">${H[step][1]}</div>`;
}
function steps(){ $('steps').innerHTML=STEPS.map((s,i)=>`<div class="step ${i==step?'on':''}" onclick="go(${i})"><span class="n">${i+1}</span>${s}</div>`).join('') }
function go(i){step=i; if(step==4&&selAct==null&&F.actions.length) pickAct(0,false); render()}
function colHead(d){
 if(!d.acquired) return `<div class="ch" title="${d.label}"><b>${d.short_label}</b><span class="chip" style="border-color:var(--comp);color:var(--comp)">not acquired</span></div>`;
 let h=`<div class="ch" title="${d.label} — ${d.modalities.join('+')}${d.cross_checks.length?' (cross-check '+d.cross_checks.join(',')+')':''}"><b>${d.short_label}</b><span class="muted">${d.robustness.cls}</span>`;
 if(step>=2) h+=`<br><span class="chip" style="border-color:var(--base)">MDC ±${fmt(d.reference.mdc95_3tiles,d)}${d.display.unit=='%'?' pt':''}</span>`;
 const s=d.spatial_support;
 if(step>=3&&s){const t=s.cls=='short-range'?'short-range':s.cls=='fov-scale'?`≈${s.range_um.toFixed(0)} µm`:`>${s.range_um.toFixed(0)} µm`;
  h+=`<br><span class="chip" style="border-color:${s.cls=='short-range'?'var(--line)':'var(--spatial)'};color:${s.cls=='short-range'?'var(--mut)':'var(--spatial)'}">⤢ ${t}</span>`}
 return h+'</div>';
}
function pad(e,d){
 const id=oid(e.id,d.id), A=selAct!=null?F.actions[selAct]:null; let cls='pad', st='', gl='', inner='', bl='';
 let pulse=!!(A&&(A.targets.observations.includes(id)||(!d.acquired&&A.targets.dimensions.includes(d.id)&&A.targets.entities.includes(e.id))));
 if(!d.acquired){ const m=MISS[id]; cls+=' unm'; if(m&&m.consequential){cls+=' comp-c'; gl='<span style="color:var(--comp)">◇</span>'}
   inner=`<div class="val" style="color:var(--mut)">?</div><div class="z">not acquired</div>`; }
 else{ const o=OBS[id], rr=o.reference_relation;
  if(rr.status=='not_measurable'){ cls+=' unm'; inner=`<div class="val" style="color:var(--mut)">∅</div><div class="z">not measurable</div>` }
  else{
   const x=rr.exceedance_ratio, a=x<1?0.05+0.10*x:Math.min(0.95,0.35+0.25*(x-1)), surv=o.scrutiny.outcome=='survives';
   st+=`background:${rgba(rr.direction,a)};`;
   if(step>=1&&o.scrutiny.outcome=='fails') st=`background:repeating-linear-gradient(135deg,${rgba(rr.direction,.22)} 0 5px,transparent 5px 10px);border:1.5px dashed ${rgba(rr.direction,.8)};`;
   const glow=step>=1&&surv?`0 0 16px 2px ${rgba(rr.direction,.55)}`:'';
   if(step>=2){const v=o.variance_shares, sp=v.spatial_sampling>=v.baseline_support, red=v.spatial_sampling+v.baseline_support, strong=deviating(o);
     const w=strong?1.5+3*red:1+1.5*red, hue=sp?'25,158,112':'144,133,233'; st+=`box-shadow:inset 0 0 0 ${w.toFixed(1)}px rgba(${hue},${strong?1:.45})${glow?','+glow:''};`}
   else if(glow) st+=`box-shadow:${glow};`;
   if(step>=1&&flicker(o)) cls+=' flick';
   inner=`<div class="val">${fmt(o.value,d)}<span style="font-size:10px;margin-left:2px">${x>=1?(rr.direction>0?'▲':'▼'):''}</span></div><div class="z">z ${rr.z>=0?'+':''}${rr.z.toFixed(1)}</div>`;
   if(step>=3){ o.rims.forEach(r=>{const t=RIM[r].type; if(GLY[t]) gl+=`<span style="color:${GLY[t][1]}">${GLY[t][0]}</span>`}); if(flicker(o)) gl+='<span>⚡</span>'; if(rr.beyond_reference_support&&deviating(o)) bl='beyond ref'}
  }
 }
 if(e.independence.reference_linked) cls+=' linked'; if(selCell==id) cls+=' sel'; if(pulse) cls+=' pulse';
 return `<div class="${cls}" style="${st}" onclick="pickCell('${e.id}','${d.id}')">${inner}<div class="gl">${gl}</div><div class="bl">${bl}</div></div>`;
}
function rowHead(e){
 let b2=''; if(e.independence.reference_linked) b2+='<span>∥ ref-linked</span> ';
 if(step>=3&&pivotal(e)) b2+=`<span style="color:var(--warn)" title="verdict without it: ${e.leverage.verdict_without} (${e.leverage.cause})">★ pivotal</span> `;
 if(step>=3&&e.acquisition.outside_tested_range.length) b2+='<span>⚡ untested acq.</span>';
 return `<div class="rh ${selRow==e.id?'sel':''} ${e.independence.reference_linked?'linked':''}" onclick="pickRow('${e.id}')"><b>${e.id}</b><span>${e.n_fields} field${e.n_fields>1?'s':''} · ${e.geometry.known_section_um.toFixed(0)} µm section</span><span class="bd">${b2}</span></div>`;
}
function grid(){
 const show=DIMS.filter(d=>d.acquired||step>=3), g=$('grid'); g.style.gridTemplateColumns=`150px repeat(${show.length},minmax(70px,1fr))`;
 g.innerHTML='<div></div>'+show.map(colHead).join('')+ROWS.map(e=>rowHead(e)+show.map(d=>pad(e,d)).join('')).join('');
 $('legend').innerHTML=`<span><i class="sw" style="background:var(--up)"></i>above approved</span><span><i class="sw" style="background:var(--down)"></i>below approved</span>`+
 (step>=1?`<span><i class="sw" style="background:repeating-linear-gradient(135deg,rgba(217,89,38,.5) 0 3px,transparent 3px 6px)"></i>fails scrutiny</span><span>flicker = acquisition-sensitive</span>`:'')+
 (step>=2?`<span><i class="sw" style="box-shadow:inset 0 0 0 3px var(--spatial)"></i>spatial sampling share larger</span><span><i class="sw" style="box-shadow:inset 0 0 0 3px var(--base)"></i>baseline support share larger</span>`:'')+
 (step>=3?`<span style="color:var(--spatial)">⤢ spatial</span><span style="color:var(--scale)">◎ scale</span><span style="color:var(--comp)">◇ composition</span><span>⚡ acquisition</span><span>∅ not measurable</span>`:'');
}
function side(){
 const el=$('side');
 if(step<4){ const pop=F.rims.find(r=>r.type=='population'), list=F.rims.filter(r=>r.type!='population');
  el.innerHTML=`<h3>${step>=3?'OUTER RIM':'EVIDENCE STATE'}</h3><div class="detail"><b>Decision</b>: ${F.decision.verdict} (batch p = ${F.decision.p_batch.toFixed(3)}), ${F.decision.n_independent} independent micrographs.</div>`+
   (step>=1?`<div class="detail"><b>Survives</b>: ${F.summary.surviving.join(', ')||'nothing'}.</div>`:'')+
   (step>=3?`<div class="detail" style="margin-top:8px"><b style="color:var(--base)">population</b>: ${pop.statement}</div>`+list.slice(0,9).map(r=>`<div class="detail"><b style="color:${(GLY[r.type]||['','var(--ink2)'])[1]}">${(GLY[r.type]||['∅'])[0]} ${r.type}</b> · ${r.target}${r.consequential?' <span style="color:var(--warn)">★ consequential</span>':''}<br>${r.statement}</div>`).join('')
   :`<div class="detail muted" style="margin-top:8px">Step through: scrutiny, field, rim, then next capture.</div>`); return; }
 el.innerHTML='<h3>NEXT CAPTURE</h3>'+F.actions.map((a,i)=>`<div class="act tier${a.tier} ${selAct==i?'on':''}" onclick="pickAct(${i})"><div><span class="verb">${a.verb}</span><span class="t">${a.title}</span></div>
  <div class="meta">tier ${a.tier} · addresses ${a.addresses} · ${a.status} · cost ${a.cost}</div>
  ${selAct==i?`<div class="detail"><ul style="padding-left:16px;margin:4px 0">${a.evidence.map(t=>`<li>${t}</li>`).join('')}</ul><b>Why this</b>: ${a.rationale}${a.effect?`<br><b>Effect</b>: ${effectText(a.effect)}`:''}<br><span class="muted">triggered by: ${a.triggered_by.join(', ')}</span></div>`:''}</div>`).join('');
}
function effectText(e){
 if(e.kind=='prevalence_ci_width') return `prevalence CI width ${(100*e.current).toFixed(0)} pts now → `+e.projected.map(p=>`${(100*p.ci_width).toFixed(0)} (+${p.added_sections})`).join(', ');
 if(e.kind=='minimum_detectable_change') return e.projected.map(p=>{const d=DIM[p.dimension];return `${d.short_label} MDC ${fmt(p.mdc95_now,d)} → ${fmt(p.mdc95_with_plus5,d)}`}).join('; ');
 if(e.kind=='field_spacing') return `spacing ≥ ${e.min_spacing_um.toFixed(0)} µm`;
 if(e.kind=='spatial_extent') return `known extent ${e.known_extent_um.toFixed(0)} µm, open at ${e.open_edges.join(' and ')}`;
 return JSON.stringify(e);
}
function pickAct(i,re=true){selAct=i; const a=F.actions[i]; const t=a.targets.entities[0]||(a.targets.observations[0]||'').split(':')[0]; if(t) selRow=t; if(re) render()}
function pickRow(p){selRow=p; render()}
function pickCell(p,k){selRow=p; selCell=oid(p,k); if(PROF[oid(p,k)]) stripK=k; render()}
function drawer(){
 const el=$('drawer'); if(!selCell){el.innerHTML='<div class="muted">Select a pad to audit the primitive statistics behind it.</div>'; return}
 const [p,k]=selCell.split(':'), d=DIM[k];
 if(!d.acquired){const m=MISS[selCell]; el.innerHTML=`<b>${p} · ${d.label}</b><div class="rule">not acquired; would require ${d.would_require.join(' / ')}</div><div class="rule">consequential: ${m.consequential}</div><div class="rule">${JSON.stringify(m.basis)}</div>`;return}
 const o=OBS[selCell], rr=o.reference_relation, e=ENT[p];
 if(rr.status=='not_measurable'){el.innerHTML=`<b>${p} · ${d.short_label}</b><div class="rule">not measurable: ${e.validity.reasons.join('; ')}</div>`;return}
 const v=o.variance_shares, sc=o.scrutiny;
 el.innerHTML=`<b>${p} · ${d.label}</b><table class="kv"><tr><td>value</td><td>${fmt(o.value,d)} ${d.display.unit} (${rr.status})</td></tr>
 <tr><td>approved</td><td>${fmt(rr.approved_mean,d)} ± ${fmt(d.reference.sd,d)} ${d.display.unit}; 95% envelope here ${fmt(rr.envelope95[0],d)}–${fmt(rr.envelope95[1],d)}</td></tr>
 <tr><td>z / thresholds</td><td>${rr.z.toFixed(2)} vs q95 ${rr.q95.toFixed(2)}, q99 ${rr.q99.toFixed(2)}</td></tr>
 <tr><td>variance shares</td><td><div class="bar"><div style="width:${100*v.approved_material}%;background:#898781"></div><div style="width:${100*v.spatial_sampling}%;background:var(--spatial)"></div><div style="width:${100*v.baseline_support}%;background:var(--base)"></div></div>
   material ${(100*v.approved_material).toFixed(0)}% · spatial sampling ${(100*v.spatial_sampling).toFixed(0)}% · baseline support ${(100*v.baseline_support).toFixed(0)}%</td></tr>
 <tr><td>fields</td><td>${Object.entries(o.per_field).map(([f,x])=>`${f.split('__')[1]} ${fmt(x,d)}`).join(' · ')} (${sc.fields_beyond_95}/${sc.n_fields} beyond 95%)</td></tr>
 <tr><td>scrutiny</td><td>${sc.outcome}${sc.failed.length?' — '+sc.failed.join(', '):''}${sc.conditional_on_untested_acquisition?' (conditional: untested acquisition)':''}</td></tr>
 <tr><td>acquisition</td><td>worst tested change (${d.robustness.worst_perturbation}) ${fmt(d.robustness.worst_shift,d)} ${d.display.unit}${sc.acquisition_share!=null?` = ${(100*sc.acquisition_share).toFixed(0)}% of the deviation`:''}</td></tr>
 <tr><td>rims</td><td>${o.rims.join(', ')||'–'}</td></tr></table>`;
}
function strip(){
 const svg=$('strip'), W=svg.clientWidth||1000, e=ENT[selRow]||ROWS[0]; if(!e){svg.innerHTML='';return}
 const avail=F.spatial_profiles.filter(p=>p.entity==e.id).map(p=>p.dimension);
 const k=(stripK&&avail.includes(stripK))?stripK:(avail.find(x=>deviating(OBS[oid(e.id,x)]))||avail[0]); if(!k){svg.innerHTML='';return}
 const pr=PROF[oid(e.id,k)], d=DIM[k];
 $('striphead').innerHTML=`<b style="color:#fff">${e.id}</b> · captured ${pr.captured_length_um.toFixed(0)} µm · ${pr.window_um}-µm window profile of `+
  avail.map(x=>`<span class="kbtn ${x==k?'on':''}" onclick="stripK='${x}';render()">${DIM[x].short_label}</span>`).join('')+` <span class="muted">— band = approved local windows (approximate)${pr.runs.length>1?' · run separation unknown':''}</span>`;
 const offs=[]; let acc=0; pr.runs.forEach(r=>{offs.push(acc); acc+=r.length_um+RUN_GAP_UM}); const totalX=Math.max(acc-RUN_GAP_UM,1);
 const L=70,R=W-70, sx=x=>L+(R-L)*x/totalX, b=pr.reference_band;
 const vals=[b.lo,b.hi]; pr.runs.forEach(r=>r.window_means.forEach(v=>vals.push(v)));
 const vmin=Math.min(...vals), vmax=Math.max(...vals), pd=(vmax-vmin)*.12||1, top=14, h=96, sy=v=>top+h-(h*(v-vmin+pd)/(vmax-vmin+2*pd));
 const x0=sx(0), x1=sx(totalX);
 let g=`<defs><linearGradient id="fl" x1="0" x2="1"><stop offset="0" stop-color="#9085e9" stop-opacity="0"/><stop offset="1" stop-color="#9085e9" stop-opacity=".22"/></linearGradient><linearGradient id="fr" x1="0" x2="1"><stop offset="0" stop-color="#9085e9" stop-opacity=".22"/><stop offset="1" stop-color="#9085e9" stop-opacity="0"/></linearGradient></defs>`;
 g+=`<text x="4" y="11" fill="#898781" font-size="10">${d.short_label} (${d.display.unit})</text>`;
 if(step>=3) g+=`<rect x="${x0-60}" y="${sy(b.hi)}" width="60" height="${sy(b.lo)-sy(b.hi)}" fill="url(#fl)"/><rect x="${x1}" y="${sy(b.hi)}" width="60" height="${sy(b.lo)-sy(b.hi)}" fill="url(#fr)"/><text x="${x0-58}" y="${sy(b.lo)+12}" fill="#898781" font-size="10">unobserved</text><text x="${x1+4}" y="${sy(b.lo)+12}" fill="#898781" font-size="10">unobserved</text>`;
 g+=`<rect x="${x0}" y="${sy(b.hi)}" width="${x1-x0}" height="${sy(b.lo)-sy(b.hi)}" fill="#9085e9" fill-opacity=".22"/><text x="4" y="${sy(b.hi)+3}" fill="#898781" font-size="10">${fmt(b.hi,d)}</text><text x="4" y="${sy(b.lo)+3}" fill="#898781" font-size="10">${fmt(b.lo,d)}</text>`;
 const col=OBS[oid(e.id,k)].reference_relation.direction<0?'#3987e5':'#d95926';
 pr.runs.forEach((r,i)=>{ const o=offs[i];
  g+=`<polyline points="${r.window_centres_um.map((x,j)=>`${sx(x+o)},${sy(r.window_means[j])}`).join(' ')}" fill="none" stroke="${col}" stroke-width="2.2"/>`;
  if(step>=3&&r.open_at_start) g+=`<text x="${sx(r.window_centres_um[0]+o)-6}" y="${sy(r.window_means[0])+4}" fill="var(--spatial)" font-size="16" text-anchor="end">◀ open</text>`;
  if(step>=3&&r.open_at_end) g+=`<text x="${sx(r.window_centres_um[r.window_centres_um.length-1]+o)+6}" y="${sy(r.window_means[r.window_means.length-1])+4}" fill="var(--spatial)" font-size="16">open ▶</text>`;
  r.fields.forEach(f=>{ const xx=sx(f.x0_um+o), ww=sx(f.x0_um+o+f.width_um)-xx, im=D.thumbs[f.field], bc=f.batch==F.context.reference?'#3987e5':f.batch==F.context.batch?'#d95926':'#199e70';
   if(im) g+=`<image href="${im}" x="${xx}" y="${top+h+16}" width="${ww}" height="46" preserveAspectRatio="none"/>`;
   g+=`<rect x="${xx}" y="${top+h+16}" width="${ww}" height="46" fill="none" stroke="${bc}" stroke-width="2"/><text x="${xx+3}" y="${top+h+74}" fill="#c3c2b7" font-size="10">${f.field.split('__')[1]} · ${f.batch.replace('Batch_','B')}</text>`; });
 });
 svg.innerHTML=g;
}
function render(){ $('bname').textContent=F.context.batch; $('rname').textContent=F.context.reference; const [vc,vi]=VC[F.decision.verdict]||['#fff','?'];
 $('verdict').innerHTML=`<span class="v" style="color:${vc}">${vi} ${F.decision.verdict}</span><span class="s">batch p = ${F.decision.p_batch.toFixed(3)} · ${F.decision.n_independent} independent micrographs${F.decision.pivotal.length?' · rests on '+F.decision.pivotal.join(', '):''}</span>`;
 steps(); head(); grid(); side(); drawer(); strip(); }
selRow=F.decision.pivotal[0]||(ROWS[0]||{}).id; render(); window.addEventListener('resize',strip);
</script></body></html>"""
