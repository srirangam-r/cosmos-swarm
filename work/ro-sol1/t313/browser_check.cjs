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
const report = {utc: new Date().toISOString(), preview_sha256: crypto.createHash('sha256').update(fs.readFileSync(preview)).digest('hex'),
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
  await cdp('Page.enable',{},session);await cdp('Runtime.enable',{},session);
  await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false},session);
  await cdp('Page.navigate',{url:pathToFileURL(preview).href},session);
  await until(`document.querySelectorAll('video').length===8&&[...document.querySelectorAll('video')].every(v=>v.readyState>=2||v.error)`);
  await evaluate(`window.row=document.getElementById('row-donor-transfer');row.scrollIntoView({block:'start'});window.pair=pairFor(['v-r3-left','v-r3-right']);pausePair(pair);`);
  await check('historical E6 media distinguished from E7 benchmark',`({pass:row.innerText.includes('selected historical E6 media')&&row.innerText.includes('not the E7 benchmark grid')&&[...row.querySelectorAll('.card-header button')].every(b=>b.innerText.includes('E6')),text:row.innerText})`);
  await check('full E7 donor and plain denominators visible',`({pass:row.innerText.includes('8/16 clean clips and 6/16')&&row.innerText.includes('4/16 clean and 0/16')&&row.innerText.includes('8 targets × 2 seeds')&&row.innerText.includes('flicker < 0.08')})`);
  await check('partial donor clock and uncertainty qualified',`({pass:row.innerText.includes('0.68 (0.70 expected)')&&row.innerText.includes('only 3 targets')&&row.innerText.includes('[-2.2, 1.15]')&&row.innerText.includes('underpowered')&&row.innerText.includes('no general noise-shaping fix')&&row.innerText.includes('no independent remeasurement')})`);
  await check('no stale awaiting or universal flicker-free statement',`({pass:!(/E7b lands|completely flicker-free|0.998|0.001s/.test(row.innerText))})`);
  await check('new E7 evidence anchor and all earlier anchors resolve',`(()=>{const broken=[...document.querySelectorAll('a[href^="#"]')].map(e=>e.hash).filter(h=>!document.getElementById(h.slice(1)));return {pass:broken.length===0&&!!document.getElementById('6167'),broken}})()`);
  await check('donor pair still decodes original assets',`({pass:pair.videos.every(v=>v.readyState>=2&&v.videoWidth===416&&!v.error),sources:pair.videos.map(v=>v.currentSrc)})`);
  await evaluate(`playPair(pair)`);await delay(350);
  await check('pair plays and pauses through existing controls',`(()=>{const wasPlaying=pair.playing&&pair.videos.every(v=>!v.paused);row.querySelector('.sync-controls button').click();return {pass:wasPlaying&&!pair.playing&&pair.videos.every(v=>v.paused)}})()`);
  await evaluate(`row.querySelectorAll('.card-header button')[1].click()`);
  await until(`!pair.loading&&document.getElementById('v-r3-right').readyState>=2`);
  await check('inversion variant retains historical diagnostic label',`({pass:row.querySelector('.card-header button.active').innerText.includes('Diagnostic')&&document.getElementById('v-r3-right').currentSrc.includes('donor_recon_real.mp4')&&document.getElementById('badge-r3').innerText.toLowerCase().includes('historical e6'),label:document.getElementById('badge-r3').innerText})`);
  await evaluate(`row.querySelectorAll('.card-header button')[0].click()`);
  await until(`!pair.loading&&document.getElementById('v-r3-right').readyState>=2`);
  await evaluate(`pausePair(pair);row.scrollIntoView({block:'start'})`);await screenshot('donor_row.png');
  await evaluate(`row.querySelector('.card-footer').scrollIntoView({block:'center'})`);await screenshot('e7_readout.png');
  await evaluate(`document.getElementById('6167').scrollIntoView({block:'center'})`);await screenshot('e7_registry.png');
  await check('registry attributes human source and preserves denominator/uncertainty',`({pass:document.getElementById('6167').innerText.includes('Raj')&&document.getElementById('6167').innerText.includes('224 generated clips')&&document.getElementById('6167').innerText.includes('[-2.2, 1.15]'),text:document.getElementById('6167').innerText})`);
  await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},session);
  await evaluate(`row.scrollIntoView({block:'start'})`);
  await check('390px donor row fits viewport',`({pass:row.getBoundingClientRect().right<=innerWidth+1&&row.scrollWidth<=row.clientWidth+1,viewport:innerWidth,rowWidth:row.clientWidth,scrollWidth:row.scrollWidth})`);
  await screenshot('donor_mobile.png');
 } catch(e){report.error=e.stack;process.exitCode=1;}
 finally {
  fs.writeFileSync(path.join(out,'browser_check.json'),JSON.stringify(report,null,2)+'\n');
  try{await cdp('Browser.close')}catch(e){}
  if(browser.exitCode===null){try{process.kill(-browser.pid,'SIGTERM')}catch(e){}}
  fs.closeSync(log);fs.rmSync(profile,{recursive:true,force:true});
  if(report.checks.some(c=>!c.pass)||report.exceptions.length)process.exitCode=1;
 }
})();
