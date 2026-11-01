// Dependency-free CDP over anonymous pipes: no debugging listener or web server.
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');
const out = __dirname;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'ro-sol1-browser-'));
const log = fs.openSync(path.join(out, 'browser_stderr.log'), 'w');
const browser = spawn(process.env.DEMO_BROWSER || '/opt/brave.com/brave/brave', [
  '--headless', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
  '--disable-background-networking', '--disable-extensions', '--disable-component-update',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--no-first-run', '--no-default-browser-check', '--remote-debugging-pipe',
  `--user-data-dir=${profile}`
], {stdio: ['ignore', 'ignore', log, 'pipe', 'pipe'], detached: true});
const report = {utc: new Date().toISOString(), source_commit:'a597e6f',
  mode: 'headless installed Brave, anonymous CDP pipes, direct HTTP media URLs, explicit muted play, no autoplay override', checks: [], exceptions: []};
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
    report.browser = await cdp('Browser.getVersion');
    const target = await cdp('Target.createTarget', {url:'about:blank'});
    ({sessionId:session} = await cdp('Target.attachToTarget', {targetId:target.targetId,flatten:true}));
    await cdp('Page.enable', {}, session);
    await cdp('Runtime.enable', {}, session);
    await cdp('Emulation.setDeviceMetricsOverride', {width:1440,height:900,deviceScaleFactor:1,mobile:false}, session);
    report.media = [];
    for (const stem of ['pendulum_physics_start','ball_settle']) {
      const url = `http://board.tail0c526a.ts.net:8031/demos/${stem}.mp4`;
      await cdp('Page.navigate', {url}, session);
      await until(`document.querySelector('video')?.readyState>=2`);
      const initial = await evaluate(`(()=>{const v=document.querySelector('video');return {url:location.href,width:v.videoWidth,height:v.videoHeight,duration:v.duration,paused:v.paused,muted:v.muted,rate:v.playbackRate,ready:v.readyState,error:v.error?.message}})()`);
      report.media.push({stem,initial});
      await check(`${stem} direct MP4 decoded`, `(()=>{const v=document.querySelector('video');return {pass:v.videoWidth>0&&Math.abs(v.duration-3.875)<.001&&!v.error}})()`);
      await evaluate(`(async()=>{window.v=document.querySelector('video');v.muted=true;v.currentTime=0;window.before=v.getVideoPlaybackQuality().totalVideoFrames;await v.play()})()`);
      await delay(800);
      await check(`${stem} MP4 actually advances decoded frames`, `({pass:!v.paused&&v.currentTime>.3&&v.getVideoPlaybackQuality().totalVideoFrames>before,time:v.currentTime,decoded_frames:v.getVideoPlaybackQuality().totalVideoFrames-before})`);
      await evaluate(`v.pause();v.currentTime=1`);
      await until(`!v.seeking&&v.readyState>=2`);
      await check(`${stem} MP4 pause and seek`, `({pass:v.paused&&Math.abs(v.currentTime-1)<.01,time:v.currentTime,paused:v.paused,seekable:Array.from({length:v.seekable.length},(_,i)=>[v.seekable.start(i),v.seekable.end(i)]),buffered:Array.from({length:v.buffered.length},(_,i)=>[v.buffered.start(i),v.buffered.end(i)])})`);
      await evaluate(`v.loop=true;v.currentTime=0;window.rollovers=0;window.lastTime=0;v.addEventListener('timeupdate',()=>{if(lastTime>3&&v.currentTime<1)rollovers++;lastTime=v.currentTime});v.play()`);
      await delay(4300);
      await check(`${stem} MP4 loops across actual end`, `({pass:!v.paused&&rollovers>0,time:v.currentTime,rollovers})`);
      await until(`v.currentTime>=1`);
      await evaluate(`v.pause()`);
      await screenshot(`${stem}_http_mp4.png`);
      const localFile = path.resolve(out, '../../raj-demos', stem+'.mp4');
      report.media.at(-1).local_sha256=crypto.createHash('sha256').update(fs.readFileSync(localFile)).digest('hex');
      await cdp('Page.navigate', {url:pathToFileURL(localFile).href}, session);
      await until(`document.querySelector('video')?.readyState>=2`);
      await evaluate(`window.v=document.querySelector('video');v.pause();v.currentTime=1`);
      await until(`!v.seeking&&v.readyState>=2`);
      await check(`${stem} same local MP4 pause and seek`, `({pass:v.paused&&Math.abs(v.currentTime-1)<.01,time:v.currentTime,seekable:Array.from({length:v.seekable.length},(_,i)=>[v.seekable.start(i),v.seekable.end(i)])})`);
      await screenshot(`${stem}_local_mp4.png`);
      await cdp('Page.navigate', {url:`http://board.tail0c526a.ts.net:8031/demos/${stem}.gif`}, session);
      await until(`document.querySelector('img')?.complete&&document.querySelector('img')?.naturalWidth>0`);
      await check(`${stem} direct GIF decoded`, `(()=>{const im=document.querySelector('img');return {pass:im.complete&&im.naturalWidth>0,width:im.naturalWidth,height:im.naturalHeight}})()`);
      await delay(150);
      await screenshot(`${stem}_gif_a.png`);
      await delay(700);
      await screenshot(`${stem}_gif_b.png`);
      const a = fs.readFileSync(path.join(out,`${stem}_gif_a.png`));
      const b = fs.readFileSync(path.join(out,`${stem}_gif_b.png`));
      const animated = !a.equals(b);
      report.checks.push({name:`${stem} direct GIF visibly animates`,pass:animated,detail:{screenshot_a_sha256:crypto.createHash('sha256').update(a).digest('hex'),screenshot_b_sha256:crypto.createHash('sha256').update(b).digest('hex'),separation_ms:700}});
      console.log(`${animated?'PASS':'FAIL'} ${stem} direct GIF visibly animates`);
    }
    await cdp('Page.navigate', {url:'http://board.tail0c526a.ts.net:8031/demos/'}, session);
    await until(`document.readyState==='complete'`);
    report.demo_index = await evaluate(`({url:location.href,title:document.title,links:[...document.querySelectorAll('a')].map(a=>({text:a.textContent,href:a.href}))})`);
    await screenshot('demo_index.png');
    await cdp('Page.navigate', {url:'http://sha-devel.tail0c526a.ts.net:8085/'}, session);
    await delay(700);
    report.gallery = await evaluate(`({url:location.href,title:document.title,text:document.body.innerText.slice(0,1000),media:[...document.querySelectorAll('video')].map(v=>({id:v.id,src:v.currentSrc,ready:v.readyState,error:v.error?.message}))})`);
    await screenshot('gallery_recheck.png');
  } catch(error) {
    report.fatal=String(error); console.error(error);process.exitCode=1;
  } finally {
    report.passed=report.checks.filter(c=>c.pass).length;
    report.failed=report.checks.filter(c=>!c.pass).length;
    if(report.failed||report.exceptions.length)process.exitCode=1;
    fs.writeFileSync(path.join(out,'browser_check.json'),JSON.stringify(report,null,2)+'\n');
    try {await cdp('Browser.close');} catch (_) {}
    try {process.kill(-browser.pid,'SIGKILL');} catch (_) {}
    fs.closeSync(log);
    for(const p of pending.values())clearTimeout(p.timer);
    fs.rmSync(profile,{recursive:true,force:true});
  }
})();
