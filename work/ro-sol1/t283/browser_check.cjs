// Dependency-free CDP over anonymous pipes: no debugging listener or web server.
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');
const out = __dirname;
const preview = process.env.DEMO_PREVIEW ? path.resolve(process.env.DEMO_PREVIEW) : path.join(out, 'preview.html');
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
  mode: 'headless installed Brave, anonymous CDP pipes, file URL, default muted autoplay policy', checks: [], exceptions: []};
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
    const target = await cdp('Target.createTarget', {url: 'about:blank'});
    ({sessionId: session} = await cdp('Target.attachToTarget', {targetId: target.targetId, flatten: true}));
    await cdp('Page.enable', {}, session); await cdp('Runtime.enable', {}, session);
    await cdp('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false}, session);
    await cdp('Page.navigate', {url: pathToFileURL(preview).href}, session);
    await until(`document.querySelectorAll('video').length === 10 && [...document.querySelectorAll('video')].every(v=>v.readyState>=2 || v.error)`);
    report.initial = await evaluate(`(()=>[...document.querySelectorAll('video')].map(v=>({id:v.id,source:v.currentSrc.split('/').pop(),duration:v.duration,width:v.videoWidth,height:v.videoHeight,ready:v.readyState,error:v.error?.message,paused:v.paused,time:v.currentTime,frames:v.getVideoPlaybackQuality().totalVideoFrames})))()`);
    await check('all ten video elements decode', `({pass:[...document.querySelectorAll('video')].every(v=>v.videoWidth>0 && v.readyState>=2 && !v.error)})`);
    await evaluate(`window.beforeFrames=[...document.querySelectorAll('video')].map(v=>v.getVideoPlaybackQuality().totalVideoFrames)`);
    await delay(900);
    await check('muted autoplay advances every video', `(()=>{const delta=[...document.querySelectorAll('video')].map((v,i)=>v.getVideoPlaybackQuality().totalVideoFrames-beforeFrames[i]);return {pass:delta.every(n=>n>0)&&[...document.querySelectorAll('video')].every(v=>!v.paused),delta}})()`);
    await evaluate(`document.getElementById('v-r1-left').closest('section').scrollIntoView()`);
    await screenshot('pendulum_preview.png');
    await evaluate(`window.ids=['v-r1-left','v-r1-right']; document.getElementById(ids[0]).closest('section').querySelector('.sync-controls button').click()`);
    await delay(200);
    await check('pause control pauses both sides', `({pass:ids.every(id=>document.getElementById(id).paused) && !pairFor(ids).playing})`);
    await evaluate(`document.getElementById('speed-r1').value='0.5'; document.getElementById('speed-r1').dispatchEvent(new Event('change'))`);
    // Use the actual existing onclick button, without assuming its CSS class.
    await evaluate(`document.querySelector('button[onclick*="pendulum_simproxy_x17"]').click()`);
    await until(`!pairFor(ids).loading`);
    await check('paused variant change resets both and preserves speed', `(()=>{const p=pairFor(ids);return {pass:p.videos.every(v=>v.paused&&v.currentTime<.1&&v.playbackRate===.5)&&document.getElementById(ids[1]).currentSrc.includes('x17'),times:p.videos.map(v=>v.currentTime),rates:p.videos.map(v=>v.playbackRate)}})()`);
    await evaluate(`togglePlay(ids)`); await delay(300);
    await evaluate(`document.querySelector('button[onclick*="pendulum_simproxy_phys"]').click()`);
    await until(`!pairFor(ids).loading && ids.every(id=>!document.getElementById(id).paused)`);
    await delay(300);
    await check('playing variant change resumes both near same time', `(()=>{const p=pairFor(ids),t=p.videos.map(v=>v.currentTime);return {pass:p.playing&&p.videos.every(v=>!v.paused&&v.playbackRate===.5)&&Math.abs(t[0]-t[1])<.15&&Math.max(...t)<1,times:t}})()`);
    await evaluate(`restartSync(ids)`); await delay(200);
    await check('restart resets and plays both sides', `(()=>{const p=pairFor(ids),t=p.videos.map(v=>v.currentTime);return {pass:p.playing&&p.videos.every(v=>!v.paused)&&Math.max(...t)<.5&&Math.abs(t[0]-t[1])<.15,times:t}})()`);
    await evaluate(`window.ends=0; document.getElementById(ids[0]).addEventListener('ended',()=>window.ends++); setSpeed(ids,1); pairFor(ids).videos.forEach(v=>v.currentTime=3.55)`);
    await until(`window.ends>0`); await delay(200);
    await check('real ended event restarts the pair', `(()=>{const p=pairFor(ids),t=p.videos.map(v=>v.currentTime);return {pass:window.ends>0&&p.playing&&p.videos.every(v=>!v.paused&&!v.loop)&&Math.max(...t)<1&&Math.abs(t[0]-t[1])<.15,ends:window.ends,times:t}})()`);
    await evaluate(`for(let n=1;n<=5;n++)pausePair(pairFor(['v-r'+n+'-left','v-r'+n+'-right']))`);
    const media = JSON.parse(fs.readFileSync(path.resolve(out, '../t279/smoke_333821f.json'))).media;
    report.media = [];
    for (const item of media) {
      const file = path.resolve(out, '../../rahul-5-agy/gallery', item.source);
      const url = pathToFileURL(file).href;
      const result = await evaluate(`new Promise(resolve=>{
        const v=document.createElement('video');v.muted=true;v.preload='auto';
        let timer;const done=r=>{clearTimeout(timer);v.pause();v.removeAttribute('src');v.load();v.remove();resolve(r)};
        timer=setTimeout(()=>done({pass:false,error:'load/decode timeout'}),4000);
        v.onerror=()=>done({pass:false,error:v.error?.message});
        v.onloadeddata=()=>done({pass:v.videoWidth>0,width:v.videoWidth,height:v.videoHeight,duration:v.duration,ready:v.readyState});
        document.body.append(v);v.src=${JSON.stringify(url)};v.load();
      })`);
      report.media.push({source:item.source, sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),...result});
    }
    report.checks.push({name:'all 24 MP4 and WebM sources decode in browser',pass:report.media.every(m=>m.pass),detail:{total:report.media.length,failed:report.media.filter(m=>!m.pass)}});
    console.log(`${report.checks.at(-1).pass?'PASS':'FAIL'} all 24 MP4 and WebM sources decode in browser`);
    await evaluate(`switchVideo('v-r1-right','file:///tmp/ro-sol1-does-not-exist',document.querySelector('button[onclick*="pendulum_simproxy_x17"]'))`);
    await delay(2000);
    await check('missing variant exits loading and leaves pair recoverable', `(()=>{const p=pairFor(ids);return {pass:!p.loading&&!p.playing&&p.videos.every(v=>v.paused),loading:p.loading,playing:p.playing,networkState:p.videos[1].networkState,error:p.videos[1].error?.message}})()`);
    await evaluate(`document.querySelector('button[onclick*="pendulum_simproxy_phys"]').click()`);
    await until(`!pairFor(ids).loading && document.getElementById(ids[1]).readyState>=2`);
    await evaluate(`document.getElementById(ids[0]).closest('section').querySelector('.sync-controls button').click()`);
    await delay(200);
    await check('valid variant and Play recover after missing media', `(()=>{const p=pairFor(ids);return {pass:p.playing&&p.videos.every(v=>!v.paused&&!v.error)&&p.videos[1].currentTime>0,times:p.videos.map(v=>v.currentTime)}})()`);
    const fallback = path.join(profile, 'webm-only');
    fs.symlinkSync(path.resolve(out, '../../rahul-5-agy/gallery/clips/pendulum_simproxy_phys.webm'), fallback+'.webm');
    await evaluate(`switchVideo('v-r1-right',${JSON.stringify(pathToFileURL(fallback).href)},document.querySelector('button[onclick*="pendulum_simproxy_phys"]'))`);
    await until(`!pairFor(ids).loading && pairFor(ids).videos.every(v=>!v.paused)`);
    await check('failed MP4 falls back to WebM and resumes pair', `(()=>{const p=pairFor(ids);return {pass:p.playing&&p.videos.every(v=>!v.paused&&!v.error)&&p.videos[1].currentSrc.endsWith('.webm'),source:p.videos[1].currentSrc.split('/').pop()}})()`);
    await check('no uncaught page exception', `({pass:true})`);
    report.checks.at(-1).pass = report.exceptions.length === 0;
    await cdp('Page.navigate', {url:'http://sha-devel.tail0c526a.ts.net:8085/'}, session);
    await until(`document.querySelectorAll('video').length === 10 && [...document.querySelectorAll('video')].every(v=>v.readyState>=2 || v.error)`);
    await delay(500);
    report.live = await evaluate(`({url:location.href,utc:new Date().toISOString(),title:document.title,videos:[...document.querySelectorAll('video')].map(v=>({id:v.id,source:v.currentSrc.split('/').pop(),width:v.videoWidth,height:v.videoHeight,duration:v.duration,paused:v.paused,time:v.currentTime,error:v.error?.message}))})`);
    await check('live gallery ten players decode', `({pass:[...document.querySelectorAll('video')].every(v=>v.videoWidth>0&&!v.error)})`);
    // Muted native autoplay is visibility-dependent on HTTP pages in Chromium.
    // Validate each pair while visible, as it will be during the presentation.
    report.live.visible_rows = [];
    for (let row=1; row<=5; row++) {
      await evaluate(`document.getElementById('v-r${row}-left').scrollIntoView({block:'center'})`);
      await delay(500);
      const result = await evaluate(`({row:${row},videos:['left','right'].map(side=>{const v=document.getElementById('v-r${row}-'+side);return {id:v.id,paused:v.paused,time:v.currentTime,error:v.error?.message}})})`);
      report.live.visible_rows.push(result);
    }
    report.checks.push({name:'live gallery each visible pair autoplays',pass:report.live.visible_rows.every(r=>r.videos.every(v=>!v.paused&&v.time>0&&!v.error)),detail:report.live.visible_rows});
    console.log(`${report.checks.at(-1).pass?'PASS':'FAIL'} live gallery each visible pair autoplays`);
    await evaluate(`document.getElementById('v-r1-left').closest('section').scrollIntoView()`);
    await screenshot('live_pendulum.png');
  } catch (error) {report.fatal = String(error); console.error(error); process.exitCode = 1;}
  finally {
    report.passed = report.checks.filter(c=>c.pass).length;
    report.failed = report.checks.filter(c=>!c.pass).length;
    if (report.failed) process.exitCode = 1;
    fs.writeFileSync(path.join(out, 'browser_check.json'), JSON.stringify(report, null, 2)+'\n');
    try {await cdp('Browser.close');} catch (_) {}
    try {process.kill(-browser.pid, 'SIGKILL');} catch (_) {}
    fs.closeSync(log);
    for (const p of pending.values()) clearTimeout(p.timer);
  }
})();
