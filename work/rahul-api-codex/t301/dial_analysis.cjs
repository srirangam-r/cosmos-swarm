
const DIAL_PERIODS = Object.freeze([0.6,0.9,1.18,1.5,2.0]);
function need(ok,msg){if(!ok) throw Error(msg);}
function mean(a){return a.length?a.reduce((s,x)=>s+x,0)/a.length:null;}
function summary(a){
 const m=mean(a);
 return {n:a.length,mean:m,sd:a.length>1?Math.sqrt(a.reduce((s,x)=>s+(x-m)**2,0)/(a.length-1)):null,
 min:a.length?Math.min(...a):null,max:a.length?Math.max(...a):null};
}
function fit(x,y){
 need(x.length===y.length&&x.length>=2,"two paired values required");
 const mx=mean(x),my=mean(y);
 const xx=x.reduce((s,v)=>s+(v-mx)**2,0);
 const yy=y.reduce((s,v)=>s+(v-my)**2,0);
 const xy=x.reduce((s,v,i)=>s+(v-mx)*(y[i]-my),0);
 need(xx>0,"dose varies");
 const slope=xy/xx,intercept=my-slope*mx,err=y.map((v,i)=>v-x[i]);
 const tiny=16*Number.EPSILON**2*Math.max(1,y.reduce((s,v)=>s+v*v,0));
 return {n:x.length,slope,intercept_s:intercept,r2:yy<=tiny?null:Math.min(1,xy*xy/(xx*yy)),
 bias_s:mean(err),rmse_to_command_s:Math.sqrt(mean(err.map(v=>v*v))),
 mean_abs_relative_error:mean(err.map((v,i)=>Math.abs(v)/x[i]))};
}
function makeDialPlan(scenes,seeds){
 need(Array.isArray(scenes)&&scenes.length>=1&&scenes.every(s=>typeof s==="string"&&s.length>0),"scene strings");
 need(new Set(scenes).size===scenes.length,"unique scenes");
 need(Array.isArray(seeds)&&seeds.length>=1&&seeds.every(Number.isSafeInteger)&&seeds.every(s=>s>=0),"integer seeds");
 need(new Set(seeds).size===seeds.length,"unique seeds");
 return scenes.flatMap(scene=>seeds.flatMap(seed=>DIAL_PERIODS.map(target_s=>({
  id:JSON.stringify([scene,seed,target_s]),scene,seed,target_s
 }))));
}
function analyzeDial(plan,observations){
 need(Array.isArray(plan)&&plan.length>0&&Array.isArray(observations),"arrays required");
 const scenes=[...new Set(plan.map(p=>p.scene))].sort();
 const seeds=[...new Set(plan.map(p=>p.seed))].sort((a,b)=>a-b);
 const expected=makeDialPlan(scenes,seeds),byId=new Map(plan.map(p=>[p.id,p]));
 need(byId.size===plan.length&&plan.length===expected.length,"unique crossed plan");
 for(const p of expected){
  const q=byId.get(p.id);
  need(q&&q.scene===p.scene&&q.seed===p.seed&&q.target_s===p.target_s,"plan identity mismatch");
 }
 const obs=new Map();
 for(const r of observations){
  need(r&&typeof r.id==="string"&&byId.has(r.id),"unknown observation");
  need(!obs.has(r.id),"duplicate observation");
  obs.set(r.id,r);
 }
 const rows=expected.map(p=>{
  const r=obs.get(p.id),reasons=[];
  if(!r) reasons.push("missing");
  else{
   if(r.flag_acf!=="ok") reasons.push("acf_flag");
   if(r.flag_mp!=="ok") reasons.push("mp_flag");
   if(!Number.isFinite(r.acf_s)||r.acf_s<=0) reasons.push("acf_period");
   if(!Number.isFinite(r.mp_s)||r.mp_s<=0) reasons.push("mp_period");
   if(!Number.isFinite(r.flicker)||r.flicker<0||r.flicker>=0.08) reasons.push("flicker");
   if(r.strip_ok!==true) reasons.push("strip");
   if(r.native_verified!==true) reasons.push("native_unverified");
   if(Number.isFinite(r.acf_s)&&r.acf_s>0&&Number.isFinite(r.mp_s)&&r.mp_s>0&&
      2*Math.abs(r.acf_s-r.mp_s)/(r.acf_s+r.mp_s)>0.10) reasons.push("tool_gap");
  }
  return {...p,observation:r??null,qc_accepted:reasons.length===0,reasons};
 });
 const lines=scenes.flatMap(scene=>seeds.map(seed=>{
  const rr=rows.filter(r=>r.scene===scene&&r.seed===seed);
  const complete=rr.every(r=>r.qc_accepted),metrics={};
  for(const tool of ["acf_s","mp_s"]){
   const endpoints=[rr[0],rr.at(-1)],pairs=[];
   for(let i=1;i<rr.length;i++) pairs.push({lo_s:rr[i-1].target_s,hi_s:rr[i].target_s,
    response:rr[i-1].qc_accepted&&rr[i].qc_accepted?
      (rr[i].observation[tool]-rr[i-1].observation[tool])/(rr[i].target_s-rr[i-1].target_s):null});
   metrics[tool]={fit:complete?fit(rr.map(r=>r.target_s),rr.map(r=>r.observation[tool])):null,
    endpoint_response:endpoints.every(r=>r.qc_accepted)?
      (endpoints[1].observation[tool]-endpoints[0].observation[tool])/(endpoints[1].target_s-endpoints[0].target_s):null,
    adjacent:pairs};
  }
  return {scene,seed,accepted:rr.filter(r=>r.qc_accepted).length,planned:rr.length,complete,metrics};
 }));
 const tools={};
 for(const tool of ["acf_s","mp_s"]){
  const accepted=rows.filter(r=>r.qc_accepted);
  const byScene=scenes.map(scene=>{
   const ll=lines.filter(l=>l.scene===scene),complete=ll.every(l=>l.complete);
   return {scene,planned_lines:ll.length,complete_lines:ll.filter(l=>l.complete).length,
    slope:complete?mean(ll.map(l=>l.metrics[tool].fit.slope)):null};
  });
  const ss=byScene.filter(s=>s.slope!==null).map(s=>s.slope);
  const dose=DIAL_PERIODS.map(target_s=>{
   const rr=rows.filter(r=>r.target_s===target_s);
   return {target_s,planned:rr.length,accepted:rr.filter(r=>r.qc_accepted).length,
    output_s:summary(rr.filter(r=>r.qc_accepted).map(r=>r.observation[tool]))};
  });
  const seedSpread=[];
  if(seeds.length===2) for(const scene of scenes) for(const target_s of DIAL_PERIODS){
   const rr=rows.filter(r=>r.scene===scene&&r.target_s===target_s);
   seedSpread.push({scene,target_s,sample_sd_s:rr.every(r=>r.qc_accepted)?
    Math.abs(rr[0].observation[tool]-rr[1].observation[tool])/Math.sqrt(2):null});
  }
  tools[tool]={secondary_accepted_only_fit:accepted.length>=2&&new Set(accepted.map(r=>r.target_s)).size>=2?
    fit(accepted.map(r=>r.target_s),accepted.map(r=>r.observation[tool])):null,
   complete_scene_slopes:summary(ss),full_grid_slope_summary:ss.length===scenes.length?summary(ss):null,byScene,
   leave_one_complete_scene_out_mean_slopes:ss.length>1?ss.map((_,i)=>mean(ss.filter((v,j)=>j!==i))):[],
   dose,paired_endpoints:summary(lines.map(l=>l.metrics[tool].endpoint_response).filter(v=>v!==null)),
   guided_seed_spread:seedSpread};
 }
 return {scope:"Summary/QC arithmetic only; no planted, physical-recovery, causal, or NVIDIA certification.",
  gates:{flicker_lt:0.08,symmetric_tool_gap_lte:0.10,flags:"both ok",strip_and_native:"explicit true"},
  all_slots_pass_qc:rows.every(r=>r.qc_accepted),
  planned:rows.length,received:obs.size,qc_accepted:rows.filter(r=>r.qc_accepted).length,
  scenes:scenes.length,seeds_per_scene:seeds.length,planned_lines:lines.length,
  complete_lines:lines.filter(l=>l.complete).length,
  missing:rows.filter(r=>r.reasons.includes("missing")).length,
  rows,lines,tools};
}

if(typeof module!=='undefined') module.exports={DIAL_PERIODS,makeDialPlan,analyzeDial,fit};
