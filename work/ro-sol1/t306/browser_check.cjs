// Dependency-free CDP over anonymous pipes: no debugging listener or web server.
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');
const out = process.env.DEMO_OUTPUT ? path.resolve(process.env.DEMO_OUTPUT) : __dirname;
fs.mkdirSync(out, {recursive:true});
const preview = path.join(__dirname, 'preview.html');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'ro-sol1-browser-'));
const log = fs.openSync(path.join(out, 'browser_stderr.log'), 'w');
const browser = spawn(process.env.DEMO_BROWSER || '/opt/brave.com/brave/brave', [
  '--headless', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
  '--disable-background-networking', '--disable-extensions', '--disable-component-update',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--no-first-run', '--no-default-browser-check', '--remote-debugging-pipe',
  `--user-data-dir=${profile}`
], {stdio: ['ignore', 'ignore', log, 'pipe', 'pipe'], detached: true});
const report = {utc: new Date().toISOString(), deployed_snapshot_sha256: crypto.createHash('sha256').update(fs.readFileSync(preview)).digest('hex'),
  mode: 'headless installed Brave, anonymous CDP pipes, default muted autoplay policy', checks: [], exceptions: []};
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
async function check(name, expression) {
  const detail = await evaluate(expression);
  report.checks.push({name, pass: !!detail.pass, detail});
  console.log(`${detail.pass ? 'PASS' : 'FAIL'} ${name}`);
}
async function screenshot(name) {
  const result = await cdp('Page.captureScreenshot', {format: 'png', captureBeyondViewport: false}, session);
  fs.writeFileSync(path.join(out, name), Buffer.from(result.data, 'base64'));
}

(async () => {
 try {
  report.browser=await cdp('Browser.getVersion');
  const target=await cdp('Target.createTarget',{url:'about:blank'});
  ({sessionId:session}=await cdp('Target.attachToTarget',{targetId:target.targetId,flatten:true}));
  await cdp('Page.enable',{},session); await cdp('Runtime.enable',{},session);
  await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false},session);
  await cdp('Page.navigate',{url:pathToFileURL(preview).href},session);
  await until(`document.querySelectorAll('video').length===8&&[...document.querySelectorAll('video')].every(v=>v.readyState>=2||v.error)`);
  await evaluate(`window.row=document.getElementById('row-ball-gravity');row.scrollIntoView({block:'start'});window.pair=pairFor(['v-r5-left','v-r5-right']);`);
  await check('row5 reports failed measurement QC and complete denominator',`({pass:row.innerText.includes('FAILED MEASUREMENT QC')&&row.innerText.includes('0/18')&&row.innerText.includes('All 18 diffusion clips completed')&&row.innerText.includes('not been established'),text:row.innerText})`);
  await check('both displayed clips explicitly prescribe analytical proxy gravity',`({pass:[...row.querySelectorAll('.video-label-row')].every(e=>e.innerText.toLowerCase().includes('analytical proxy')&&e.innerText.toLowerCase().includes('prescribed g')),labels:[...row.querySelectorAll('.video-label-row')].map(e=>e.innerText)})`);
  await check('no stale queued or gravity success labels in corrected row',`({pass:!(/queued|in flight|forces Cosmos|Effective Gravitational|Uncalibrated|Calibrated Proxy/i.test(row.innerText))})`);
  await check('ownerQC anchor and earlier evidence links resolve',`(()=>{let broken=[...document.querySelectorAll('a[href^="#"]')].map(e=>e.hash).filter(h=>!document.getElementById(h.slice(1)));return {pass:!broken.length&&!!document.getElementById('5887'),broken}})()`);
  await check('eight existing media players decode',`({pass:[...document.querySelectorAll('video')].every(v=>v.readyState>=2&&v.videoWidth>0&&!v.error),videos:[...document.querySelectorAll('video')].map(v=>({id:v.id,source:v.currentSrc,width:v.videoWidth,height:v.videoHeight,error:v.error?.message}))})`);
  await evaluate(`playPair(pair)`); await delay(350);
  await check('ball proxy pair plays',`({pass:pair.playing&&pair.videos.every(v=>!v.paused)})`);
  await evaluate(`row.querySelector('.sync-controls button').click()`);
  await check('ball proxy pair pauses',`({pass:!pair.playing&&pair.videos.every(v=>v.paused)})`);
  await evaluate(`setSpeed(['v-r5-left','v-r5-right'],.5);restartSync(['v-r5-left','v-r5-right'])`); await delay(200);
  await check('ball proxy restart preserves speed',`({pass:pair.playing&&pair.videos.every(v=>!v.paused&&v.currentTime<.5&&v.playbackRate===.5)})`);
  await evaluate(`pausePair(pair)`); await screenshot('ball_row.png');
  await evaluate(`document.getElementById('5887').scrollIntoView({block:'center'})`); await screenshot('qc_registry.png');
  report.final=await evaluate(`({url:location.href,registry:document.getElementById('5887').parentElement.innerText})`);
 } catch(e) {report.error=e.stack;process.exitCode=1;}
 finally {
  fs.writeFileSync(path.join(out,'browser_check.json'),JSON.stringify(report,null,2)+'\n');
  try {await cdp('Browser.close')} catch(e) {}
  if(browser.exitCode===null){try{process.kill(-browser.pid,'SIGTERM')}catch(e){}}
  fs.closeSync(log);fs.rmSync(profile,{recursive:true,force:true});
  if(report.checks.some(c=>!c.pass)||report.exceptions.length)process.exitCode=1;
 }
})();
