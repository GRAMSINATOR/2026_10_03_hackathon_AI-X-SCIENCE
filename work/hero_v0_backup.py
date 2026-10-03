"""Evidence Field: self-contained HTML/JS control surface rendered from the uncertainty field (qc.field).
Every visual state maps to a field rule; see docs/FIELD_MODEL.md."""
import base64
import io
import json
import os

from PIL import Image

from .features import CACHE


def _thumbs(field, h=46):
    out = {}
    for r in field['rows']:
        for prof in r['profiles'].values():
            for t in prof['tiles']:
                k = t['key']
                if k in out:
                    continue
                p = os.path.join(CACHE, f'{k}_BSE.jpg')
                if not os.path.exists(p):
                    continue
                im = Image.open(p).convert('L')
                im = im.resize((max(1, int(im.width * h / im.height)), h))
                b = io.BytesIO()
                im.save(b, 'JPEG', quality=70)
                out[k] = 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
    return out


def render(field, reference_name):
    data = json.dumps(dict(field=field, thumbs=_thumbs(field), ref=reference_name), default=float)
    return TEMPLATE.replace('__DATA__', data)


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><title>Evidence Field</title>
<style>
:root{--bg:#0d0d0d;--panel:#1a1a19;--line:rgba(255,255,255,.10);--ink:#fff;--ink2:#c3c2b7;--mut:#898781;
--up:#d95926;--down:#3987e5;--spatial:#199e70;--base:#9085e9;--scale:#c98500;--comp:#d55181;
--good:#0ca30c;--warn:#fab219;--crit:#d03b3b}
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
.rh b{color:var(--ink);font-size:13px}.rh.sel{background:#262624}.rh .bd{font-size:10px;margin-top:2px}
.rh.linked{opacity:.45}
.pad{position:relative;height:60px;border-radius:9px;background:#232321;border:1px solid rgba(255,255,255,.07);cursor:pointer;
display:flex;align-items:center;justify-content:center;flex-direction:column;transition:all .35s;overflow:hidden}
.pad .val{font-weight:700;font-size:13px;z-index:2}.pad .z{font-size:10px;color:var(--ink2);z-index:2}
.pad.sel{outline:2px solid #fff;outline-offset:1px}
.pad.linked{opacity:.4}
.pad .gl{position:absolute;top:3px;right:5px;font-size:12px;z-index:3;letter-spacing:1px}
.pad .bl{position:absolute;bottom:2px;left:5px;font-size:10px;z-index:3;color:var(--ink2)}
.pad.hollow{background:transparent!important;border:1.5px dashed rgba(255,255,255,.28)}
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
.bar{display:flex;height:10px;border-radius:3px;overflow:hidden;margin:4px 0}
.muted{color:var(--mut)}.rule{font-size:11px;color:var(--ink2);margin:2px 0}
.kbtn{cursor:pointer;font-size:11px;padding:2px 7px;border-radius:5px;border:1px solid var(--line);margin-left:4px;color:var(--ink2)}.kbtn.on{color:#fff;border-color:#fff}
</style></head><body>
<div class="top"><div class="brand">EPISTEMIC ACQUISITION CONTROLLER · <b id="bname"></b> <span class="muted">vs approved <span id="rname"></span></span></div>
<div class="verdict" id="verdict"></div></div>
<div class="steps" id="steps"></div>
<div class="head" id="head"></div>
<div class="main"><div class="panel"><div class="grid" id="grid"></div><div class="legend" id="legend"></div></div>
<div class="panel side" id="side"></div></div>
<div class="lower"><div class="panel"><div id="striphead" style="font-size:12px;color:var(--ink2);margin-bottom:4px"></div><svg id="strip" width="100%" height="190"></svg></div>
<div class="panel" id="drawer"></div></div>
<script>
const D=__DATA__, F=D.field;
const STEPS=['SIGNAL','SCRUTINY','FIELD','OUTER RIM','NEXT CAPTURE'];
let step=0, selRow=null, selCell=null, selAct=null, stripK=null;
const cols=F.columns, rows=F.rows;
const $=id=>document.getElementById(id);
const fmt=(v,c)=>v==null?'–':(Math.abs(v*c.scale)>=100?(v*c.scale).toFixed(0):(v*c.scale).toPrecision(3));
const VC={ACCEPT:['var(--good)','✓'],INVESTIGATE:['var(--warn)','!'],REJECT:['var(--crit)','✕'],REFERENCE:['var(--down)','◆']};
const GLY={spatial:['⤢','var(--spatial)','spatial rim: structure at or beyond the captured extent'],scale:['◎','var(--scale)','scale rim: excess piled at the detection floor'],
 composition:['◇','var(--comp)','composition rim: chemistry not measured'],acquisition:['⚡','var(--ink2)','acquisition: untested regime or explains the deviation']};
function rgba(dir,a){return dir<0?`rgba(57,135,229,${a})`:`rgba(217,89,38,${a})`}
function head(){
 const s=F.summary, a=F.actions[0]||{};
 const H=[[`${s.n_deviating} cell${s.n_deviating==1?'':'s'} deviate from the approved envelope.`,'Brightness = |z| relative to the calibrated 95% threshold for this micrograph\'s sampling. Arrow = direction.'],
 [`${s.n_surviving} of ${s.n_deviating} survive scrutiny.`,'Solid = robust KPI · consistent across tiles · tested acquisition changes explain < 50%. Hatched = apparent signal that did not survive. Flicker = acquisition could explain it, or untested regime.'],
 ['Each envelope = approved material spread + spatial sampling + baseline support.','Ring = dominant reducible component (aqua = spatial sampling of this micrograph, violet = size of the approved reference); thickness = reducible share. Header: minimum detectable change.'],
 [`${F.rims.filter(r=>r.consequential).length} consequential rim${F.rims.filter(r=>r.consequential).length==1?'':'s'}`+(F.pivotal.length?` — the verdict rests on ${F.pivotal.join(', ')}.`:'.'),'Rims mark where the dataset stops constraining reality: ⤢ spatial extent · ◎ resolution floor · ◇ unmeasured composition · ⚡ acquisition · ★ decision leverage. Strip below: captured section; the band fades where nothing was observed.'],
 [`Next capture: ${a.title||'none required'}`,'Ranked: decision-critical → flag-level → support. Each action names its trigger evidence, the uncertainty it addresses, and why it beats the obvious alternative. Select one to light its trigger cells.']];
 $('head').innerHTML=`<div>${H[step][0]}</div><div class="sub">${H[step][1]}</div>`;
}
function steps(){ $('steps').innerHTML=STEPS.map((s,i)=>`<div class="step ${i==step?'on':''}" onclick="go(${i})"><span class="n">${i+1}</span>${s}</div>`).join('') }
function go(i){step=i; if(step==4&&!selAct&&F.actions.length) pickAct(0,false); render()}
function colHead(c){
 if(!c.measured) return `<div class="ch" title="${c.label}"><b>${c.short}</b>${step>=3?'<span class="chip" style="border-color:var(--comp);color:var(--comp)">not acquired</span>':''}</div>`;
 let h=`<div class="ch" title="${c.label} — ${c.modality}"><b>${c.short}</b><span class="muted">${c.cls}</span>`;
 if(step>=2) h+=`<br><span class="chip" style="border-color:var(--base)">MDC ±${fmt(c.mdc95,c)}${c.unit=='%'?' pt':''}</span>`;
 if(step>=3&&c.spatial){const s=c.spatial;const t=s.cls=='short-range'?'short-range':s.cls=='fov-scale'?`≈${s.range_um.toFixed(0)} µm`:`>${s.range_um.toFixed(0)} µm`;
  h+=`<br><span class="chip" style="border-color:${s.cls=='short-range'?'var(--line)':'var(--spatial)'};color:${s.cls=='short-range'?'var(--mut)':'var(--spatial)'}" title="adjacent-tile variance ${s.excess.toFixed(1)}× short-range prediction (95% CI ${s.excess_ci[0].toFixed(1)}–${s.excess_ci[1].toFixed(1)})">⤢ ${t}</span>`}
 return h+'</div>';
}
function padHTML(r,c){
 const cell=F.cells[r.parent][c.kpi]; const id=r.parent+':'+c.kpi; let cls='pad', st='', gl='', inner='', bl='';
 const pulse=selAct!=null&&F.actions[selAct].targets.includes(id);
 if(!c.measured){ cls+=' unm'; if(step>=3&&cell.consequential){cls+=' comp-c'; gl='<span style="color:var(--comp)">◇</span>'}
   inner=`<div class="val" style="color:var(--mut)">?</div><div class="z">not acquired</div>`; if(step<3) cls+=' hollow'; }
 else if(cell.state=='unmeasurable'){ cls+=' unm'; inner=`<div class="val" style="color:var(--mut)">∅</div><div class="z">not measurable</div>` }
 else{
  const dev=cell.dev, a=dev<1?0.05+0.10*dev:Math.min(0.95,0.35+0.25*(dev-1));
  st+=`background:${rgba(cell.dir,a)};`;
  if(step>=1&&cell.deviating&&!cell.survives){ st=`background:repeating-linear-gradient(135deg,${rgba(cell.dir,.22)} 0 5px,transparent 5px 10px);border:1.5px dashed ${rgba(cell.dir,.8)};` }
  if(step>=1&&cell.deviating&&cell.survives) st+=`box-shadow:0 0 16px 2px ${rgba(cell.dir,.55)};`;
  if(step>=2){const strong=cell.deviating; const w=strong?1.5+3*cell.reducible_share:1+1.5*cell.reducible_share; const hue=cell.dominant=='spatial'?'25,158,112':'144,133,233';
   st+=`box-shadow:inset 0 0 0 ${w.toFixed(1)}px rgba(${hue},${strong?1:.45})${cell.deviating&&cell.survives?','+'0 0 16px 2px '+rgba(cell.dir,.55):''};`}
  if(step>=1&&cell.acq_sensitive) cls+=' flick';
  const arrow=cell.dir>0?'▲':cell.dir<0?'▼':'';
  inner=`<div class="val">${fmt(cell.value,c)}<span style="font-size:10px;margin-left:2px">${dev>=1?arrow:''}</span></div><div class="z">z ${cell.z>=0?'+':''}${cell.z.toFixed(1)}</div>`;
  if(step>=3){ (cell.rims||[]).forEach(t=>{gl+=`<span style="color:${GLY[t][1]}" title="${GLY[t][2]}">${GLY[t][0]}</span>`});
   if(cell.acq_sensitive) gl+=`<span title="${GLY.acquisition[2]}">⚡</span>`; if(cell.beyond_support&&cell.deviating) bl='beyond ref'}
 }
 if(r.ref_linked) cls+=' linked'; if(selCell==id) cls+=' sel'; if(pulse) cls+=' pulse';
 return `<div class="${cls}" style="${st}" onclick="pickCell('${r.parent}','${c.kpi}')" title="${(cell.rules||[]).join(' | ').replace(/"/g,"'")}">${inner}<div class="gl">${gl}</div><div class="bl">${bl}</div></div>`;
}
function rowHead(r){
 let bd=`${r.n_tiles} tile${r.n_tiles>1?'s':''} · ${r.section_um.toFixed(0)} µm section`;
 let b2=''; if(r.ref_linked) b2+='<span title="physical continuation of an approved baseline cross-section: not independent">∥ ref-linked</span> ';
 if(step>=3&&r.pivotal) b2+=`<span style="color:var(--warn)" title="verdict without it: ${r.leverage.verdict_without} — ${r.leverage.why}">★ pivotal</span> `;
 if(step>=3&&r.acq_untested&&r.acq_untested.length) b2+='<span title="acquired outside the tested acquisition range">⚡ untested acq.</span>';
 return `<div class="rh ${selRow==r.parent?'sel':''} ${r.ref_linked?'linked':''}" onclick="pickRow('${r.parent}')"><b>${r.parent}</b><span>${bd}</span><span class="bd">${b2}</span></div>`;
}
function grid(){
 const show=cols.filter(c=>c.measured||step>=3);
 const g=$('grid'); g.style.gridTemplateColumns=`150px repeat(${show.length},minmax(70px,1fr))`;
 let h='<div></div>'+show.map(colHead).join('');
 rows.forEach(r=>{h+=rowHead(r)+show.map(c=>padHTML(r,c)).join('')});
 g.innerHTML=h;
 $('legend').innerHTML=`<span><i class="sw" style="background:var(--up)"></i>above approved</span><span><i class="sw" style="background:var(--down)"></i>below approved</span>`+
 (step>=1?`<span><i class="sw" style="background:repeating-linear-gradient(135deg,rgba(217,89,38,.5) 0 3px,transparent 3px 6px)"></i>did not survive</span><span>flicker = acquisition-sensitive</span>`:'')+
 (step>=2?`<span><i class="sw" style="box-shadow:inset 0 0 0 3px var(--spatial)"></i>spatial sampling dominates</span><span><i class="sw" style="box-shadow:inset 0 0 0 3px var(--base)"></i>baseline support dominates</span>`:'')+
 (step>=3?`<span style="color:var(--spatial)">⤢ spatial</span><span style="color:var(--scale)">◎ scale</span><span style="color:var(--comp)">◇ composition</span><span>⚡ acquisition</span><span>∅ not measurable</span>`:'');
}
function side(){
 const el=$('side');
 if(step<4){
  const pop=F.rims.find(r=>r.type=='population');
  const list=F.rims.filter(r=>r.type!='population'&&(step>=3?true:r.consequential));
  el.innerHTML=`<h3>${step>=3?'OUTER RIM':'EVIDENCE STATE'}</h3>`+
   `<div class="detail"><b>Decision</b>: ${F.verdict} (batch p = ${F.p_batch.toFixed(3)}), ${F.n_independent} independent micrograph${F.n_independent==1?'':'s'}.</div>`+
   (step>=1?`<div class="detail"><b>Survives</b>: ${F.summary.surviving.join(', ')||'nothing'}.</div>`:'')+
   (step>=3?`<div class="detail" style="margin-top:8px"><b style="color:var(--base)">Population</b>: ${pop.text}</div>`+
     list.slice(0,8).map(r=>`<div class="detail"><b style="color:${(GLY[r.type]||['','var(--ink2)'])[1]}">${(GLY[r.type]||['∅'])[0]} ${r.type}</b> · ${r.target.replace(':',' · ')}${r.consequential?' <span style="color:var(--warn)">★ consequential</span>':''}<br>${r.text}</div>`).join(''):
     `<div class="detail muted" style="margin-top:8px">Step through: scrutiny removes signals that do not survive; the field shows what bounds each envelope; the rim shows where support fades; then the controller proposes what to measure.</div>`);
  return;
 }
 el.innerHTML='<h3>NEXT CAPTURE</h3>'+F.actions.map((a,i)=>`<div class="act tier${a.tier} ${selAct==i?'on':''}" onclick="pickAct(${i})">
  <div><span class="verb">${a.verb}</span><span class="t">${a.title}</span></div>
  <div class="meta">tier ${a.tier} · addresses ${a.addresses} · ${a.status} · cost ${a.cost}</div>
  ${selAct==i?`<div class="detail"><ul style="padding-left:16px;margin:4px 0">${a.trigger.map(t=>`<li>${t}</li>`).join('')}</ul><b>Why this</b>: ${a.why}${a.effect?`<br><b>Computed effect</b>: ${a.effect}`:''}</div>`:''}</div>`).join('');
}
function pickAct(i,re=true){selAct=i; const t=F.actions[i].targets[0]; if(t){selRow=t.split(':')[0]} if(re) render()}
function pickRow(p){selRow=p; render()}
function pickCell(p,k){selRow=p; selCell=p+':'+k; if(['additive_area_frac','additive_density','porosity'].includes(k)) stripK=k; render()}
function drawer(){
 const el=$('drawer'); if(!selCell){el.innerHTML='<div class="muted">Select a pad to audit the primitive statistics behind it.</div>'; return}
 const [p,k]=selCell.split(':'); const c=cols.find(x=>x.kpi==k), cell=F.cells[p][k], r=rows.find(x=>x.parent==p);
 if(!c.measured||cell.state){el.innerHTML=`<b>${p} · ${c.short}</b><div class="rule">${(cell.rules||[]).join('<br>')}</div><div class="rule">${c.modality}</div>`;return}
 const comp=cell.components, tiles=Object.entries(cell.tiles).map(([f,v])=>`${f} ${fmt(v,c)}`).join(' · ');
 el.innerHTML=`<b>${p} · ${c.label}</b>
 <table class="kv"><tr><td>value</td><td>${fmt(cell.value,c)} ${c.unit} (${cell.status})</td></tr>
 <tr><td>approved</td><td>${fmt(cell.mean,c)} ± ${fmt(cell.sd_ref,c)} ${c.unit}; 95% envelope here ${fmt(cell.envelope[0],c)}–${fmt(cell.envelope[1],c)}</td></tr>
 <tr><td>z / thresholds</td><td>${cell.z.toFixed(2)} vs q95 ${cell.q95.toFixed(2)}, q99 ${cell.q99.toFixed(2)} (simulated for ${r.n_tiles} tile${r.n_tiles>1?'s':''})</td></tr>
 <tr><td>variance budget</td><td><div class="bar"><div style="width:${100*comp.material}%;background:#898781" title="approved material spread"></div><div style="width:${100*comp.spatial}%;background:var(--spatial)" title="spatial sampling"></div><div style="width:${100*comp.baseline}%;background:var(--base)" title="baseline support"></div></div>
   material ${(100*comp.material).toFixed(0)}% · spatial sampling ${(100*comp.spatial).toFixed(0)}% · baseline support ${(100*comp.baseline).toFixed(0)}%</td></tr>
 <tr><td>tiles</td><td>${tiles} (${cell.tiles_beyond95}/${Object.keys(cell.tiles).length} beyond 95%)</td></tr>
 <tr><td>acquisition</td><td>worst tested change (${cell.acq_worst}) shifts it by ${fmt(cell.acq_shift,c)} ${c.unit}${cell.acq_share!=null?` = ${(100*cell.acq_share).toFixed(0)}% of the deviation`:''}</td></tr></table>
 ${(cell.rules||[]).map(x=>`<div class="rule">• ${x}</div>`).join('')}`;
}
function strip(){
 const svg=$('strip'), W=svg.clientWidth||1000, r=rows.find(x=>x.parent==selRow)||rows[0]; if(!r){svg.innerHTML='';return}
 const devK=['additive_density','additive_area_frac','porosity'].find(k=>F.cells[r.parent][k].deviating);
 const k=stripK&&r.profiles[stripK]?stripK:(devK||'additive_density'); const pr=r.profiles[k], c=cols.find(x=>x.kpi==k);
 $('striphead').innerHTML=`<b style="color:#fff">${r.parent}</b> · captured section ${pr.length_um.toFixed(0)} µm · 100-µm window profile of `+
  ['additive_density','additive_area_frac','porosity'].map(x=>`<span class="kbtn ${x==k?'on':''}" onclick="stripK='${x}';render()">${cols.find(y=>y.kpi==x).short}</span>`).join('')+
  ` <span class="muted">— band = approved 100-µm windows (visual aid; decisions are micrograph-level)</span>`;
 const xs=[]; pr.runs.forEach(run=>run.sx.forEach(x=>xs.push(x)));
 const totalX=Math.max(...pr.tiles.map(t=>t.x0+t.width),1);
 const L=70,R=W-70, sx=x=>L+(R-L)*x/totalX;
 const vals=[]; pr.runs.forEach(run=>run.smooth.forEach(v=>vals.push(v))); vals.push(pr.band.lo,pr.band.hi);
 const vmin=Math.min(...vals), vmax=Math.max(...vals), pad=(vmax-vmin)*.12||1; const top=14, h=96, sy=v=>top+h-(h*(v-vmin+pad)/(vmax-vmin+2*pad));
 const x0=sx(0), x1=sx(totalX);
 let g=`<defs><linearGradient id="fl" x1="0" x2="1"><stop offset="0" stop-color="#9085e9" stop-opacity="0"/><stop offset="1" stop-color="#9085e9" stop-opacity=".22"/></linearGradient>
 <linearGradient id="fr" x1="0" x2="1"><stop offset="0" stop-color="#9085e9" stop-opacity=".22"/><stop offset="1" stop-color="#9085e9" stop-opacity="0"/></linearGradient></defs>`;
 if(step>=3) g+=`<rect x="${x0-60}" y="${sy(pr.band.hi)}" width="60" height="${sy(pr.band.lo)-sy(pr.band.hi)}" fill="url(#fl)"/><rect x="${x1}" y="${sy(pr.band.hi)}" width="60" height="${sy(pr.band.lo)-sy(pr.band.hi)}" fill="url(#fr)"/>`;
 g+=`<rect x="${x0}" y="${sy(pr.band.hi)}" width="${x1-x0}" height="${sy(pr.band.lo)-sy(pr.band.hi)}" fill="#9085e9" fill-opacity=".22"/>`;
 if(step>=3) g+=`<text x="${x0-58}" y="${sy(pr.band.lo)+12}" fill="#898781" font-size="10">unobserved</text><text x="${x1+4}" y="${sy(pr.band.lo)+12}" fill="#898781" font-size="10">unobserved</text>`;
 g+=`<text x="4" y="11" fill="#898781" font-size="10">${c.short} (${c.unit})</text>`;
 const dcol=F.cells[r.parent][k].dir<0?'#3987e5':'#d95926';
 const off=0; pr.runs.forEach((run,i)=>{const pts=run.sx.map((x,j)=>`${sx(x)},${sy(run.smooth[j])}`).join(' ');
  g+=`<polyline points="${pts}" fill="none" stroke="${dcol}" stroke-width="2.2"/>`;
  if(step>=3&&run.open_left) g+=`<text x="${sx(run.sx[0]+off)-6}" y="${sy(run.smooth[0])+4}" fill="var(--spatial)" font-size="16" text-anchor="end">◀ open</text>`;
  if(step>=3&&run.open_right) g+=`<text x="${sx(run.sx[run.sx.length-1]+off)+6}" y="${sy(run.smooth[run.smooth.length-1])+4}" fill="var(--spatial)" font-size="16">open ▶</text>`;
 });
 g+=`<text x="4" y="${sy(pr.band.hi)+3}" fill="#898781" font-size="10">${fmt(pr.band.hi,c)}</text><text x="4" y="${sy(pr.band.lo)+3}" fill="#898781" font-size="10">${fmt(pr.band.lo,c)}</text>`;
 pr.tiles.forEach(t=>{ const im=D.thumbs[t.key]; const xx=sx(t.x0), ww=sx(t.x0+t.width)-xx;
  const col=t.batch==D.ref?'#3987e5':t.batch==F.batch?'#d95926':'#199e70';
  if(im) g+=`<image href="${im}" x="${xx}" y="${top+h+16}" width="${ww}" height="46" preserveAspectRatio="none"/>`;
  g+=`<rect x="${xx}" y="${top+h+16}" width="${ww}" height="46" fill="none" stroke="${col}" stroke-width="2"/><text x="${xx+3}" y="${top+h+74}" fill="#c3c2b7" font-size="10">${t.key.split('__')[1]} · ${t.batch.replace('Batch_','B')}</text>`;
 });
 svg.innerHTML=g;
}
function render(){ $('bname').textContent=F.batch; $('rname').textContent=D.ref; const [vc,vi]=VC[F.verdict]||['#fff','?'];
 $('verdict').innerHTML=`<span class="v" style="color:${vc}">${vi} ${F.verdict}</span><span class="s">batch p = ${F.p_batch.toFixed(3)} · ${F.n_independent} independent micrographs${F.pivotal.length?' · rests on '+F.pivotal.join(', '):''}</span>`;
 steps(); head(); grid(); side(); drawer(); strip(); }
selRow=(F.pivotal[0])||(rows[0]||{}).parent; render(); window.addEventListener('resize',strip);
</script></body></html>"""
