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
  mode: 'headless installed Brave, anonymous CDP pipes, static local page; no video playback', renders: [], exceptions: []};
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
  const target=await cdp('Target.createTarget',{url:'about:blank'});
  ({sessionId:session}=await cdp('Target.attachToTarget',{targetId:target.targetId,flatten:true}));
  await cdp('Page.enable',{},session); await cdp('Runtime.enable',{},session);
  const source=JSON.parse(fs.readFileSync(path.join(__dirname,'source/t319_results.json')));
  for(const [name,width,height,mobile] of [['desktop',1440,1200,false],['mobile',390,1600,true]]) {
   await cdp('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile},session);
   await cdp('Page.navigate',{url:pathToFileURL(preview).href},session);
   await until(`document.readyState==='complete'&&document.querySelector('#plain').textContent==='0.5439'`);
   const state=await evaluate(`({overflow:document.documentElement.scrollWidth>innerWidth,text:document.querySelector('main').innerText,rows:document.querySelectorAll('tbody tr').length,links:[...document.querySelectorAll('a')].map(a=>a.getAttribute('href'))})`);
   if(state.overflow||state.rows!==6)throw new Error('Layout/row count failed');
   for(const phrase of ['never approved','degenerate','ddof=0','Retiming changes playback time','one pendulum rig','provisional','plausibility judge','not an NVIDIA-identical','cause of the DOVER drop'])if(!state.text.includes(phrase))throw new Error('Missing label: '+phrase);
   const links=state.links.filter(x=>!x.startsWith('http')).map(x=>({href:x,exists:fs.existsSync(path.resolve(__dirname,x.split('#')[0]))}));
   if(!links.every(x=>x.exists))throw new Error('Missing local evidence link');
   report.renders.push({name,state,links});
   await screenshot(name+'.png');
   const metrics=[];
   for(const key of ['dover_fused','dover_technical','dover_aesthetic','dd_binary','dd_norm']){
    await evaluate(`document.querySelector('#metric').value=${JSON.stringify(key)};document.querySelector('#metric').dispatchEvent(new Event('change'))`);
    const values=await evaluate(`({plain:document.querySelector('#plain').textContent,nphys:document.querySelector('#nphys').textContent,real:document.querySelector('#real').textContent,summary:document.querySelector('#metric-summary').textContent,note:document.querySelector('#metric-note').textContent})`);
    const r=source.metrics[key];
    if(values.plain!==r.plain_mean.toFixed(4)||values.nphys!==r.nphys_mean.toFixed(4)||values.real!==r.real_mean.toFixed(4)||!values.summary.includes(r.delta_scene_mean.toFixed(4))||!r.delta_boot95_exact.every(v=>values.summary.includes(v.toFixed(4))))throw new Error('Metric display differs from source: '+key);
    if(key==='dd_norm'&&!values.note.includes('proxy'))throw new Error('Proxy label missing');
    metrics.push({key,...values});
   }
   await evaluate(`document.querySelector('#scores').scrollIntoView()`); await screenshot(name+'_metrics.png');
   await evaluate(`document.querySelector('#receipts').scrollIntoView()`); await screenshot(name+'_receipts.png');
   report.renders.push({name,metrics});
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
