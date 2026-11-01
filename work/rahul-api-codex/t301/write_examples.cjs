'use strict';
const fs = require('node:fs');
const path = require('node:path');
const {makeDialPlan} = require('./dial_analysis.cjs');
const {analyzeInput} = require('./analyze.cjs');
const dir = path.join(__dirname, 'examples');
fs.mkdirSync(dir, {recursive:true});
const plan = makeDialPlan(['syntheticA','syntheticB','syntheticC'], [1,2]);
const rows = fn => plan.map(p => ({id:p.id, acf_s:fn(p), mp_s:fn(p),
  flag_acf:'ok',flag_mp:'ok',flicker:.005,strip_ok:true,native_verified:true}));
const scenarios = {
  empty: [],
  unity: rows(p => p.target_s),
  twice_command: rows(p => 2*p.target_s),
  missing_middle: rows(p => p.target_s).filter((_,i)=>i!==2),
};
for (const [name,observations] of Object.entries(scenarios)) {
  const doc = {data_kind:'synthetic',
    context:'ILLUSTRATIVE ONLY. Scene IDs, seed IDs, periods, flags and acceptance booleans are synthetic, not an adopted task265 plan or model measurements.',
    plan, observations};
  const raw = JSON.stringify(doc,null,2)+'\n';
  fs.writeFileSync(path.join(dir, name+'_input.json'), raw);
  fs.writeFileSync(path.join(dir, name+'_report.json'), JSON.stringify(analyzeInput(raw),null,2)+'\n');
}
