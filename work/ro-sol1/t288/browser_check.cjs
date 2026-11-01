// CDP transport reused from task283; tests below exercise task288.
// Dependency-free CDP over anonymous pipes: no debugging listener or web server.
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');
const out = __dirname;
const preview = process.env.DEMO_PREVIEW ? path.resolve(process.env.DEMO_PREVIEW) : path.join(out, 'offline.html');
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
  mode: 'headless installed Brave, anonymous CDP pipes, file URL, default muted autoplay policy', checks: [], exceptions: [], external_requests: []};
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
    if (msg.method === 'Network.requestWillBeSent' && /^https?:/.test(msg.params.request.url)) report.external_requests.push(msg.params.request.url);
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
  const r = await cdp('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true, userGesture: true}, session);
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
    report.browser = await cdp('Browser.getVersion');
    const target = await cdp('Target.createTarget', {url:'about:blank'});
    ({sessionId:session} = await cdp('Target.attachToTarget', {targetId:target.targetId,flatten:true}));
    await cdp('Page.enable', {}, session); await cdp('Runtime.enable', {}, session);
    await cdp('Network.enable', {}, session);
    await cdp('Network.setBlockedURLs', {urls:['http://*','https://*','ws://*','wss://*']}, session);
    await cdp('Emulation.setDeviceMetricsOverride', {width:1440,height:1100,deviceScaleFactor:1,mobile:false}, session);
    await cdp('Page.navigate', {url:pathToFileURL(preview).href}, session);
    await until(`[...document.querySelectorAll('video')].length===2 && [...document.querySelectorAll('video')].every(v=>v.readyState>=2||v.error)`);
    report.media = await evaluate(`Promise.all([...document.querySelectorAll('video')].map(async v=>{
      const body=Uint8Array.from(atob(v.src.split(',')[1]),c=>c.charCodeAt(0));
      const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',body))].map(x=>x.toString(16).padStart(2,'0')).join('');
      return {id:v.id,sha256:hash,bytes:body.length,width:v.videoWidth,height:v.videoHeight,duration:v.duration,paused:v.paused,ready:v.readyState,error:v.error?.message};
    }))`);
    const manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
    report.checks.push({name:'embedded bytes equal both pinned source MP4s',pass:report.media.every((m,i)=>m.sha256===manifest.media[i].sha256&&m.bytes===manifest.media[i].bytes),detail:report.media});
    await check('both embedded MP4s decode and start paused offline',`({pass:[...document.querySelectorAll('video')].every(v=>v.readyState>=2&&v.videoWidth>0&&!v.error&&v.paused&&v.duration===3.875)})`);
    await screenshot('offline_pendulum.png');
    for(const id of ['pendulum','ball']) {
      await evaluate(`document.getElementById('choose-${id}').click()`);
      await evaluate(`document.getElementById('${id}-video').currentTime=1`);
      await until(`!document.getElementById('${id}-video').seeking`);
      await check(`${id}: seek to 1s works offline`, `(()=>{const v=document.getElementById('${id}-video');return {pass:Math.abs(v.currentTime-1)<.05,actual:v.currentTime,seekable:Array.from({length:v.seekable.length},(_,i)=>[v.seekable.start(i),v.seekable.end(i)])}})()`);
      await evaluate(`window.beforeFrames=document.getElementById('${id}-video').getVideoPlaybackQuality().totalVideoFrames;document.getElementById('${id}').querySelector('[data-play]').click()`);
      await delay(450);
      await check(`${id}: Play advances actual decoded frames`,`(()=>{const v=document.getElementById('${id}-video');return {pass:!v.paused&&v.getVideoPlaybackQuality().totalVideoFrames>beforeFrames&&v.currentTime>1.1,frames:v.getVideoPlaybackQuality().totalVideoFrames-beforeFrames,time:v.currentTime}})()`);
      await evaluate(`document.getElementById('${id}').querySelector('[data-play]').click()`);
      await check(`${id}: Pause stops the video`, `({pass:document.getElementById('${id}-video').paused&&document.getElementById('${id}').querySelector('[data-play]').textContent==='Play'})`);
      await evaluate(`(()=>{const select=document.getElementById('${id}').querySelector('select');select.value='0.5';select.dispatchEvent(new Event('change'))})()`);
      await check(`${id}: speed control sets half speed`, `({pass:document.getElementById('${id}-video').playbackRate===.5})`);
      await evaluate(`document.getElementById('${id}').querySelector('[data-restart]').click()`);
      await delay(250);
      await check(`${id}: Restart resets and plays`, `(()=>{const v=document.getElementById('${id}-video');return {pass:!v.paused&&v.currentTime>0&&v.currentTime<.4,time:v.currentTime}})()`);
      await evaluate(`(()=>{const card=document.getElementById('${id}'),v=card.querySelector('video'),select=card.querySelector('select');select.value='1';select.dispatchEvent(new Event('change'));window.loopPeak=0;window.wrapSeen=false;v.ontimeupdate=()=>{if(v.currentTime>3.6)window.loopPeak=v.currentTime;if(window.loopPeak>3.6&&v.currentTime<.6)window.wrapSeen=true};v.currentTime=3.65})()`);
      await until('window.wrapSeen',5000);
      await check(`${id}: actual playback wraps end to start`, `({pass:window.wrapSeen&&!document.getElementById('${id}-video').paused,peak:window.loopPeak,time:document.getElementById('${id}-video').currentTime})`);
      await evaluate(`document.getElementById('${id}-video').pause()`);
      await evaluate(`document.getElementById('${id}').querySelector('[data-fullscreen]').click()`);
      await until(`!!document.fullscreenElement`,2000);
      await check(`${id}: Full screen keeps the caption card`, `({pass:document.fullscreenElement?.id==='${id}'&&!document.fullscreenElement.querySelector('.note').hidden})`);
      await evaluate('document.exitFullscreen()');
    }
    await evaluate(`document.getElementById('choose-pendulum').click();document.getElementById('pendulum').querySelector('[data-play]').click()`);
    await delay(200);
    await evaluate(`document.getElementById('choose-ball').click()`);
    await check('switching pauses hidden video and marks selected button', `({pass:document.getElementById('pendulum-video').paused&&document.getElementById('pendulum').hidden&&!document.getElementById('ball').hidden&&document.getElementById('choose-ball').getAttribute('aria-pressed')==='true'})`);
    await evaluate(`document.activeElement?.blur()`);
    async function key(key,code,extra={}) {await cdp('Input.dispatchKeyEvent',{type:'keyDown',key,code,...extra},session);await cdp('Input.dispatchKeyEvent',{type:'keyUp',key,code,...extra},session)}
    await key('1','Digit1'); await key(' ','Space',{windowsVirtualKeyCode:32}); await delay(200);
    await check('physical keyboard 1 and Space select and play',`({pass:!document.getElementById('pendulum').hidden&&!document.getElementById('pendulum-video').paused})`);
    await key('r','KeyR'); await delay(200);
    await check('physical keyboard R restarts',`({pass:document.getElementById('pendulum-video').currentTime<.4})`);
    await key('2','Digit2');
    await check('physical keyboard 2 switches and pauses previous',`({pass:!document.getElementById('ball').hidden&&document.getElementById('pendulum-video').paused})`);
    await evaluate(`document.getElementById('ball-video').currentTime=1.4`);
    await until(`!document.getElementById('ball-video').seeking`);
    await screenshot('offline_ball.png');
    await cdp('Emulation.setDeviceMetricsOverride', {width:390,height:844,deviceScaleFactor:1,mobile:false}, session);
    await check('390px viewport has no horizontal overflow',`({pass:document.documentElement.scrollWidth<=390,width:document.documentElement.scrollWidth})`);
    await screenshot('offline_mobile.png');
    report.checks.push({name:'no external network requests or uncaught page exceptions',pass:report.external_requests.length===0&&report.exceptions.length===0,detail:{external_requests:report.external_requests,exceptions:report.exceptions}});
  } catch(error) {report.fatal=String(error.stack||error);process.exitCode=1}
  finally {
    report.passed=report.checks.filter(c=>c.pass).length;
    report.failed=report.checks.filter(c=>!c.pass).length;
    if(report.failed)process.exitCode=1;
    fs.writeFileSync(path.join(out,'browser_check.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({passed:report.passed,failed:report.failed,fatal:report.fatal}));
    try{await cdp('Browser.close')}catch(_){}
    try{process.kill(-browser.pid,'SIGKILL')}catch(_){}
    fs.closeSync(log);for(const p of pending.values())clearTimeout(p.timer);
    try{fs.rmSync(profile,{recursive:true,force:true})}catch(_){}
  }
})();
