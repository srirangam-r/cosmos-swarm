// Reuses task317 CDP transport. Dependency-free CDP over anonymous pipes: no debugging listener or web server.
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');
const out = process.env.DEMO_OUTPUT ? path.resolve(process.env.DEMO_OUTPUT) : __dirname;
fs.mkdirSync(out, {recursive:true});
const preview = path.join(__dirname, 'index.html');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'ro-sol1-browser-'));
const log = fs.openSync(path.join(out, 'browser_stderr.log'), 'w');
const browser = spawn(process.env.DEMO_BROWSER || '/opt/brave.com/brave/brave', [
  '--headless', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
  '--disable-background-networking', '--disable-extensions', '--disable-component-update',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--no-first-run', '--no-default-browser-check', '--remote-debugging-pipe',
  `--user-data-dir=${profile}`
], {stdio: ['ignore', 'ignore', log, 'pipe', 'pipe'], detached: true});
const report = {utc: new Date().toISOString(), preview_sha256: crypto.createHash('sha256').update(fs.readFileSync(preview)).digest('hex'),
  mode: 'headless installed Brave, anonymous CDP pipes, static local page; 108 selector states; no video playback', renders: [], exceptions: []};
let serial = 0, buffer = '', session;
const pending = new Map();
browser.stdio[4].on('data', chunk => {
  buffer += chunk;
  let index;
  while ((index = buffer.indexOf('\0')) >= 0) {
    const msg = JSON.parse(buffer.slice(0, index)); buffer = buffer.slice(index + 1);
    if (msg.id && pending.has(msg.id)) {
      const p = pending.get(msg.id); pending.delete(msg.id); clearTimeout(p.timer);
      msg.error ? p.reject(new Error(JSON.stringify(msg.error))) : p.resolve(msg.result);
    }
    if (msg.method === 'Runtime.exceptionThrown') report.exceptions.push(msg.params.exceptionDetails);
  }
});
function cdp(method, params = {}, targetSession) {
  return new Promise((resolve, reject) => {
    const id = ++serial;
    const timer = setTimeout(() => {pending.delete(id); reject(new Error(`CDP timeout: ${method}`));}, 15000);
    pending.set(id, {resolve, reject, timer});
    browser.stdio[3].write(JSON.stringify({id, method, params, ...(targetSession ? {sessionId: targetSession} : {})}) + '\0');
  });
}
async function evaluate(expression) {
  const r = await cdp('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true}, session);
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(expression, timeout = 10000) {
  const end = Date.now() + timeout;
  do {if (await evaluate(expression)) return; await delay(100);} while (Date.now() < end);
  throw new Error(`Condition timeout: ${expression}`);
}
async function screenshot(name) {
  const result = await cdp('Page.captureScreenshot', {format: 'png', captureBeyondViewport: false}, session);
  fs.writeFileSync(path.join(out, name), Buffer.from(result.data, 'base64'));
}

(async () => {
 try {
  report.browser_pid=browser.pid; report.browser=await cdp('Browser.getVersion');
  fs.writeFileSync(path.join(out,'browser_render.json'),JSON.stringify({status:'running'}));
  const target=await cdp('Target.createTarget',{url:'about:blank'});
  ({sessionId:session}=await cdp('Target.attachToTarget',{targetId:target.targetId,flatten:true}));
  await cdp('Page.enable',{},session); await cdp('Runtime.enable',{},session);
  const source=JSON.parse(fs.readFileSync(path.join(__dirname,'source/t331_results.json')));
  for(const [name,width,height,mobile] of [['desktop',1440,1200,false],['mobile',390,1500,true]]) {
   await cdp('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile},session);
   await cdp('Page.navigate',{url:pathToFileURL(preview).href},session);
   await until(`document.readyState==='complete'&&document.querySelectorAll('#rows tr').length===18`);
   const state=await evaluate(`({overflow:document.documentElement.scrollWidth>innerWidth,text:document.querySelector('main').innerText,links:[...document.querySelectorAll('a')].map(a=>a.getAttribute('href'))})`);
   if(state.overflow)throw new Error('Document overflow');
   for(const phrase of ['provisional','20,000 Monte Carlo draws','Compare only within the re-encoded set','not an extra cost to add','symbolic','does not establish','one rig','no result for that fix','not separately identify','later-real-video periods'])if(!state.text.includes(phrase))throw new Error('Missing label: '+phrase);
   const links=state.links.filter(x=>!x.startsWith('http')).map(x=>({href:x,exists:fs.existsSync(path.resolve(__dirname,x.split('#')[0]))}));
   if(!links.every(x=>x.exists))throw new Error('Missing local evidence link');
   await screenshot(name+'.png');
   const interactions=[];
   for(const metric of ['dover_fused','dover_aesthetic','dover_technical']){
    for(const row of source[metric].rows){
     await evaluate(`document.querySelector('#metric').value=${JSON.stringify(metric)};document.querySelector('#scene').value=${JSON.stringify(row.scene)};document.querySelector('#seed').value=${JSON.stringify(String(row.seed))};document.querySelector('#metric').dispatchEvent(new Event('change'))`);
     const got=await evaluate(`({cells:Object.fromEntries([...document.querySelectorAll('[data-cell]')].map(x=>[x.dataset.cell,x.querySelector('strong').textContent])),rows:[...document.querySelectorAll('#rows tr')].map(x=>[...x.querySelectorAll('th,td')].map(y=>y.textContent)),summary:document.querySelector('#pair-summary').textContent,effects:Object.fromEntries([...document.querySelectorAll('[data-effect]')].map(x=>[x.dataset.effect,x.querySelector('.estimate').textContent])),share:document.querySelector('#share').textContent,mask:document.querySelector('#mask-summary').textContent,active:document.querySelectorAll('#rows .active').length,overflow:document.documentElement.scrollWidth>innerWidth})`);
     for(const key of ['pp','nn','np','pn'])if(got.cells[key]!==row[key].toFixed(5))throw new Error('Cell mismatch '+key);
     const expectedRows=source[metric].rows.map(r=>[r.scene+' / '+r.seed,...['pp','nn','np','pn','total','background','corridor'].map(k=>r[k].toFixed(5))]);
     if(JSON.stringify(got.rows)!==JSON.stringify(expectedRows))throw new Error('Source table mismatch');
     const fmt=x=>(x>=0?'+':'−')+Math.abs(x).toFixed(4);
     for(const key of ['total','background','corridor','interaction']){
      const s=source[metric].summary[key];
      if(!got.effects[key].includes(fmt(s.mean))||!s.ci95.every(v=>got.effects[key].includes(fmt(v))))throw new Error('Effect/interval mismatch');
     }
     if(got.active!==1||got.overflow||!got.summary.includes('Take '+row.scene+', seed '+row.seed)||!got.share.includes((100*source[metric].summary.share_background).toFixed(1)+'%')||!got.mask.includes((100*source.mask[row.scene+'_s'+row.seed].mask_frac_feather).toFixed(1)+'%'))throw new Error('Selection/layout mismatch');
     interactions.push({metric,scene:row.scene,seed:row.seed,source_cells_match:true,all18_source_rows_match:true,effects_match:true});
    }
   }
   await evaluate(`document.querySelector('#effects').scrollIntoView()`); await screenshot(name+'_effects.png');
   await evaluate(`document.querySelector('#factorial').scrollIntoView()`); await screenshot(name+'_factorial.png');
   await evaluate(`document.querySelector('#receipts').scrollIntoView()`); await screenshot(name+'_receipts.png');
   report.renders.push({name,width,height,state,links,interactions});
  }
  if(report.exceptions.length)throw new Error('Browser runtime exception');
  report.passed=true;
 }catch(e){report.error=e.stack;process.exitCode=1;}
 finally {
  fs.writeFileSync(path.join(out,'browser_render.json'),JSON.stringify(report,null,2)+'\n');
  try{await cdp('Browser.close')}catch(e){}
  if(browser.exitCode===null){try{process.kill(-browser.pid,'SIGTERM')}catch(e){}}
  fs.closeSync(log);fs.rmSync(profile,{recursive:true,force:true});
 }
})();
