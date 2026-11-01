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
  report.browser_pid=browser.pid;report.browser=await cdp('Browser.getVersion');
  const target=await cdp('Target.createTarget',{url:'about:blank'});
  ({sessionId:session}=await cdp('Target.attachToTarget',{targetId:target.targetId,flatten:true}));
  await cdp('Page.enable',{},session);await cdp('Runtime.enable',{},session);
  for(const [name,width,height,mobile] of [['desktop',1440,1040,false],['mobile',390,2000,true]]) {
   await cdp('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile},session);
   await cdp('Page.navigate',{url:pathToFileURL(preview).href},session);
   await until(`document.readyState==='complete'&&!!document.querySelector('main')`);
   await evaluate(`Promise.all([...document.images].map(async im=>{im.loading='eager';await im.decode()}))`);
   const state=await evaluate(`({overflow:document.documentElement.scrollWidth>innerWidth, text:document.querySelector('main').innerText, review:document.querySelector('#review').textContent, rows:document.querySelectorAll('#clips tbody tr').length, fits:document.querySelectorAll('#fits tbody tr').length, links:[...document.querySelectorAll('a')].map(a=>a.getAttribute('href'))})`);
   report.renders.push({name,state});
   const receipt=JSON.parse(fs.readFileSync(path.join(__dirname,'review_6380.json')));
   if(state.overflow || state.review!==receipt.body || state.rows!==20 || state.fits!==4 || !state.text.includes('1.0050 ± 0.0050') || !state.text.includes('17/20') || !state.text.includes('95% bootstrap interval') || !state.text.includes('unvalidated')) throw new Error('Audit readout acceptance failed');
   await screenshot(name+'.png');
   await evaluate(`document.querySelector('#flagged').click()`);
   const filtered=await evaluate(`({visible:[...document.querySelectorAll('#clips tbody tr')].filter(r=>!r.hidden).map(r=>r.querySelector('th').textContent),count:document.querySelector('#rowcount').textContent,pressed:document.querySelector('#flagged').getAttribute('aria-pressed')})`);
   if(filtered.visible.length!==3 || !filtered.visible.includes('pend11_P600_s2') || filtered.count!=='Showing 3 of 20' || filtered.pressed!=='true')throw new Error('Flagged filter failed');
   await evaluate(`document.querySelector('#source-note').open=true;document.querySelector('#source-note').scrollIntoView()`);
   await screenshot(name+'_source_note.png');
   await evaluate(`document.querySelector('#all').click()`);
   const reset=await evaluate(`[...document.querySelectorAll('#clips tbody tr')].filter(r=>!r.hidden).length`);
   if(reset!==20)throw new Error('All clips reset failed');
   report.renders.push({name,filtered,reset});
   // Exercise the local link and confirm that frozen dense-frame images decode.
   const href=await evaluate(`document.querySelector('a[href^=\"../t317/\"]').href`);
   await cdp('Page.navigate',{url:href},session);
   await until(`document.readyState==='complete'&&!!document.querySelector('#disagreement')`);
   await evaluate(`Promise.all([...document.querySelectorAll('#disagreement img')].map(async im=>{im.loading='eager';await im.decode()}))`);
   const linked=await evaluate(`({url:location.href,dense:document.querySelectorAll('#disagreement img').length,ok:[...document.querySelectorAll('#disagreement img')].every(im=>im.complete&&im.naturalWidth>0)})`);
   if(linked.dense!==8||!linked.ok)throw new Error('Frozen evidence navigation failed');
   report.renders.push({name,linked});
  }
 }catch(e){report.error=e.stack;process.exitCode=1;}
 finally {
  fs.writeFileSync(path.join(out,'browser_render.json'),JSON.stringify(report,null,2)+'\n');
  try{await cdp('Browser.close')}catch(e){}
  if(browser.exitCode===null){try{process.kill(-browser.pid,'SIGTERM')}catch(e){}}
  fs.closeSync(log);fs.rmSync(profile,{recursive:true,force:true});
 }
})();
