const {DIAL_PERIODS,makeDialPlan,analyzeDial,fit}=require('./dial_analysis.cjs');
function regression(){

let checks=0;
function assert(ok,label){if(!ok)throw Error(label);checks++;}
function close(a,b,tol=1e-10){return Math.abs(a-b)<=tol*Math.max(1,Math.abs(a),Math.abs(b));}
const plan=makeDialPlan(["syntheticA","syntheticB","syntheticC"],[1,2]);
const obs=(fn)=>plan.map(p=>({id:p.id,acf_s:fn(p),mp_s:fn(p),
 flag_acf:"ok",flag_mp:"ok",flicker:.005,strip_ok:true,native_verified:true}));
const run=(rows)=>analyzeDial(plan,rows);
const unity=obs(p=>p.target_s),u=run(unity);
assert(u.planned===30&&u.qc_accepted===30&&u.complete_lines===6,"complete denominator");
assert(u.all_slots_pass_qc&&u.tools.acf_s.full_grid_slope_summary.n===3,"full grid summary");
for(const tool of ["acf_s","mp_s"]){
 const a=u.tools[tool];
 assert(a.complete_scene_slopes.n===3&&close(a.complete_scene_slopes.mean,1),"scene unity");
 assert(a.secondary_accepted_only_fit.rmse_to_command_s===0,"zero calibration error");
 assert(a.paired_endpoints.n===6&&close(a.paired_endpoints.mean,1),"paired unity");
 assert(a.guided_seed_spread.length===15&&a.guided_seed_spread.every(s=>s.sample_sd_s===0),"seed spread");
}
const twice=run(obs(p=>2*p.target_s));
assert(close(twice.tools.acf_s.secondary_accepted_only_fit.r2,1),"twice perfect correlation");
assert(close(twice.tools.acf_s.complete_scene_slopes.mean,2),"twice wrong gain");
assert(close(twice.tools.acf_s.secondary_accepted_only_fit.mean_abs_relative_error,1),"twice 100pct error");
const flat=run(obs(p=>1.2));
assert(flat.tools.acf_s.secondary_accepted_only_fit.r2===null,"constant R2 undefined");
assert(flat.tools.acf_s.complete_scene_slopes.mean===0&&flat.tools.acf_s.paired_endpoints.mean===0,"constant no response");
const sceneIndex=p=>["syntheticA","syntheticB","syntheticC"].indexOf(p.scene);
const hetero=run(obs(p=>.6+sceneIndex(p)*(p.target_s-.6)));
assert(close(hetero.tools.acf_s.complete_scene_slopes.mean,1),"hetero grand gain");
assert(close(hetero.tools.acf_s.complete_scene_slopes.sd,1),"hetero scene SD");
assert(hetero.tools.acf_s.byScene.map(s=>s.slope).every((v,i)=>close(v,i)),"hetero exposed");
const chosen={syntheticA:.6,syntheticB:1.18,syntheticC:2};
const selective=run(obs(p=>chosen[p.scene]).filter((r,i)=>plan[i].target_s===chosen[plan[i].scene]));
assert(selective.planned===30&&selective.received===6&&selective.missing===24,"selected retains missing");
assert(selective.complete_lines===0&&selective.tools.acf_s.complete_scene_slopes.mean===null,"selected no primary gain");
assert(close(selective.tools.acf_s.secondary_accepted_only_fit.r2,1),"selected seductive R2");
const partial=run(unity.slice(1));
assert(partial.qc_accepted===29&&partial.complete_lines===5,"one missing drops one line");
assert(partial.tools.acf_s.complete_scene_slopes.n===2,"one missing drops one complete scene");
assert(partial.tools.acf_s.full_grid_slope_summary===null&&!partial.all_slots_pass_qc,"partial full-grid headline withheld");
assert(partial.tools.acf_s.paired_endpoints.n===5,"endpoint denominator");
const middle=run(unity.filter((r,i)=>i!==2));
assert(middle.complete_lines===5&&middle.tools.acf_s.paired_endpoints.n===6,"missing middle keeps endpoint diagnostic");
const bad=[
 ["flag_acf","check","acf_flag"],["flag_mp","fail","mp_flag"],
 ["acf_s",NaN,"acf_period"],["mp_s",0,"mp_period"],
 ["flicker",.08,"flicker"],["flicker",-1,"flicker"],["flicker",null,"flicker"],
 ["strip_ok",false,"strip"],["native_verified",false,"native_unverified"],
 ["native_verified","true","native_unverified"],["mp_s",12,"tool_gap"]
];
for(const [field,value,reason] of bad){
 const rows=unity.map(r=>({...r,[field]:value})),o=run(rows);
 assert(o.qc_accepted===0&&o.complete_lines===0,"bad rows excluded "+reason);
 assert(o.rows.every(r=>r.reasons.includes(reason)),"reason retained "+reason);
}
const near=run(unity.map(r=>({...r,mp_s:r.acf_s*1.05})));
assert(near.qc_accepted===30&&close(near.tools.mp_s.complete_scene_slopes.mean,1.05),"two tools kept separate");
const seedShift=run(obs(p=>p.target_s+(JSON.parse(p.id)[1]===1?0:.2)));
assert(seedShift.tools.acf_s.guided_seed_spread.every(s=>close(s.sample_sd_s,.2/Math.sqrt(2))),"within-cell seed SD");
assert(JSON.stringify(run([...unity].reverse()))===JSON.stringify(u),"observation order invariant");
const xp=DIAL_PERIODS,mx=xp.reduce((s,x)=>s+x,0)/xp.length;
const ex2=xp.reduce((s,x)=>s+x*x,0)/xp.length;
let affineFixtures=0;
for(const b of [.1,.5,1,1.7,3])for(const a of [0,.1,1,3]){
 const f=fit(xp,xp.map(x=>a+b*x));
 assert(close(f.slope,b)&&close(f.intercept_s,a),"affine coefficients");
 const expectedRmse=Math.sqrt((b-1)**2*ex2+2*a*(b-1)*mx+a*a);
 assert(close(f.rmse_to_command_s,expectedRmse),"affine analytic MSE");
 assert(close(f.bias_s,a+(b-1)*mx),"affine analytic bias");
 affineFixtures++;
}
const rejects=[
 ()=>run([...unity,unity[0]]),()=>run([{...unity[0],id:"unknown"}]),
 ()=>analyzeDial([...plan,plan[0]],unity),
 ()=>analyzeDial(plan.map((p,i)=>i? p:{...p,target_s:.7}),unity),
 ()=>makeDialPlan(["a","a"],[1,2]),()=>makeDialPlan(["a"],[1,1]),
 ()=>makeDialPlan(["a"],[-1]),()=>makeDialPlan(["a"],[1.5]),
 ()=>analyzeDial([],[]),()=>run([null])
];
for(const fn of rejects){let threw=false;try{fn()}catch{threw=true}assert(threw,"bad input rejected");}
return {checks,affineFixtures,rejectedInputs:rejects.length,qcFailureFixtures:bad.length,
 examples:{twiceR2:twice.tools.acf_s.secondary_accepted_only_fit.r2,
 twiceRmseS:twice.tools.acf_s.secondary_accepted_only_fit.rmse_to_command_s,
 heteroSceneSlopes:hetero.tools.acf_s.byScene.map(s=>s.slope),
 selectiveAccepted:selective.qc_accepted,selectiveMissing:selective.missing,
 selectiveCompleteLines:selective.complete_lines,selectiveR2:selective.tools.acf_s.secondary_accepted_only_fit.r2}};

}
console.log(JSON.stringify(regression(),null,2));
