// Dependency-free CDP over anonymous pipes: no debugging listener or web server.
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');
const out = process.env.DEMO_OUTPUT ? path.resolve(process.env.DEMO_OUTPUT) : __dirname;
fs.mkdirSync(out, {recursive:true});
const preview = path.join(__dirname, 'served_gallery.html');
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
    report.browser = await cdp('Browser.getVersion');
    const target = await cdp('Target.createTarget', {url: 'about:blank'});
    ({sessionId: session} = await cdp('Target.attachToTarget', {targetId: target.targetId, flatten: true}));
    await cdp('Page.enable', {}, session); await cdp('Runtime.enable', {}, session);
    await cdp('Emulation.setDeviceMetricsOverride', {width:1440,height:1100,deviceScaleFactor:1,mobile:false}, session);
    await cdp('Page.navigate', {url:process.env.DEMO_URL || 'http://sha-devel.tail0c526a.ts.net:8085/'}, session);
    await until(`document.querySelectorAll('video').length===8 && [...document.querySelectorAll('video')].every(v=>v.readyState>=2||v.error)`);
    report.initial = await evaluate(`({url:location.href,videos:[...document.querySelectorAll('video')].map(v=>({id:v.id,source:v.currentSrc,width:v.videoWidth,height:v.videoHeight,duration:v.duration,paused:v.paused,error:v.error?.message})),brokenAnchors:[...document.querySelectorAll('a[href^="#"]')].map(a=>a.getAttribute('href')).filter(h=>!document.getElementById(h.slice(1)))})`);
    await check('all eight deployed video players decode',`({pass:[...document.querySelectorAll('video')].every(v=>v.readyState>=2&&v.videoWidth>0&&!v.error)})`);
    await check('every internal evidence link resolves',`(()=>{const broken=[...document.querySelectorAll('a[href^="#"]')].map(a=>a.getAttribute('href')).filter(h=>!document.getElementById(h.slice(1)));return {pass:broken.length===0,broken}})()`);
    for (const stem of ['pendulum','ball']) {
      await evaluate(`window.vid=document.getElementById('v-demo-${stem}');window.img=document.getElementById('img-demo-${stem}');window.card=vid.closest('section');window.playButton=card.querySelector('.sync-controls button');card.scrollIntoView({block:'start'});`);
      await delay(400);
      await evaluate(`vid.play();window.startFrames=vid.getVideoPlaybackQuality().totalVideoFrames;window.loopEvents=0;vid.addEventListener('timeupdate',()=>{if(window.previousTime>2&&vid.currentTime<.5)loopEvents++;window.previousTime=vid.currentTime})`);
      await delay(500);
      await check(`${stem}: native MP4 advances decoded frames`, `({pass:!vid.paused&&vid.getVideoPlaybackQuality().totalVideoFrames>startFrames,frames:vid.getVideoPlaybackQuality().totalVideoFrames-startFrames,duration:vid.duration,width:vid.videoWidth,height:vid.videoHeight})`);
      await screenshot(`${stem}_mp4.png`);
      await until(`window.loopEvents>0`,6000);
      await check(`${stem}: native MP4 wraps through end`, `({pass:loopEvents>0&&!vid.paused,wraps:loopEvents})`);
      await evaluate(`playButton.click()`); await delay(100);
      await check(`${stem}: Pause updates state and button`, `({pass:vid.paused&&playButton.textContent.trim()==='Play',paused:vid.paused,label:playButton.textContent.trim()})`);
      await evaluate(`card.querySelector('button[onclick^="restartSingle"]').click()`); await delay(200);
      await check(`${stem}: Restart starts and updates button`, `({pass:!vid.paused&&vid.currentTime<.5&&playButton.textContent.trim()==='Pause',paused:vid.paused,time:vid.currentTime,label:playButton.textContent.trim()})`);
      await evaluate(`window.speed=card.querySelector('select');speed.value='.5';speed.value='0.5';speed.dispatchEvent(new Event('change'))`);
      await check(`${stem}: speed control applies`, `({pass:vid.playbackRate===.5,rate:vid.playbackRate})`);
      await evaluate(`card.querySelector('button[onclick*="setFormat"][onclick*="gif"]').click()`);
      await until(`img.complete&&img.naturalWidth>0`);
      await check(`${stem}: GIF toggle shows image and pauses MP4`, `({pass:vid.paused&&getComputedStyle(vid).display==='none'&&getComputedStyle(img).display!=='none'&&img.naturalWidth>0,imageWidth:img.naturalWidth,imageHeight:img.naturalHeight})`);
      await screenshot(`${stem}_gif_a.png`); await delay(650); await screenshot(`${stem}_gif_b.png`);
      await check(`${stem}: MP4 controls are inactive in GIF mode`, `({pass:[...card.querySelectorAll('.sync-controls button,.sync-controls select')].every(e=>e.disabled||getComputedStyle(e).display==='none'),controls:[...card.querySelectorAll('.sync-controls button,.sync-controls select')].map(e=>({text:e.textContent.trim(),disabled:e.disabled}))})`);
      // Exercise the real rendered Pause/Play control while GIF is visible.
      await evaluate(`playButton.click()`); await delay(200);
      await check(`${stem}: GIF mode cannot restart hidden MP4`, `({pass:vid.paused,paused:vid.paused,label:playButton.textContent.trim(),videoDisplay:getComputedStyle(vid).display})`);
      await evaluate(`card.querySelector('button[onclick*="setFormat"][onclick*="mp4"]').click()`); await delay(250);
      await check(`${stem}: MP4 return has accurate label and speed`, `({pass:!vid.paused&&getComputedStyle(vid).display!=='none'&&getComputedStyle(img).display==='none'&&playButton.textContent.trim()==='Pause'&&vid.playbackRate===.5,label:playButton.textContent.trim(),rate:vid.playbackRate})`);
      await evaluate(`vid.pause()`);
    }
    for (const n of [3,4,5]) {
      await evaluate(`window.ids=['v-r${n}-left','v-r${n}-right'];window.pair=pairFor(ids);pair.videos[0].closest('section').scrollIntoView({block:'center'});playPair(pair)`);
      await delay(400);
      await check(`pair ${n}: visible pair plays`, `({pass:pair.playing&&pair.videos.every(v=>!v.paused&&!v.error),times:pair.videos.map(v=>v.currentTime)})`);
      await evaluate(`pair.videos[0].closest('section').querySelector('.sync-controls button').click()`);
      await check(`pair ${n}: pause affects both players`, `({pass:!pair.playing&&pair.videos.every(v=>v.paused)})`);
      await evaluate(`setSpeed(ids,.5);restartSync(ids)`);await delay(250);
      await check(`pair ${n}: restart preserves speed and starts both`, `({pass:pair.playing&&pair.videos.every(v=>!v.paused&&v.currentTime<.5&&v.playbackRate===.5),times:pair.videos.map(v=>v.currentTime)})`);
      await evaluate(`pausePair(pair)`);
    }
    await evaluate(`window.ids=['v-r3-left','v-r3-right'];window.pair=pairFor(ids);document.getElementById(ids[0]).closest('section').scrollIntoView({block:'center'});document.querySelector('button[onclick*="donor_recon_real"]').click()`);
    await until(`!pair.loading&&pair.videos[1].readyState>=2`);
    await check('adopted pair variant resets paused pair and retains speed', `({pass:!pair.playing&&pair.videos.every(v=>v.paused&&v.currentTime<.1&&v.playbackRate===.5)&&pair.videos[1].currentSrc.includes('donor_recon_real'),times:pair.videos.map(v=>v.currentTime),source:pair.videos[1].currentSrc})`);
    await evaluate(`playPair(pair);document.querySelector('button[onclick*="donor_transfer_fixed"]').click()`);
    await until(`!pair.loading&&pair.videos.every(v=>!v.paused)`);
    await check('adopted pair playing variant resumes both', `({pass:pair.playing&&pair.videos.every(v=>!v.paused&&v.playbackRate===.5),times:pair.videos.map(v=>v.currentTime)})`);
    await screenshot('diagnostic_pair.png');
    await check('no uncaught browser exception',`({pass:true})`);report.checks.at(-1).pass=report.exceptions.length===0;
  } catch(error) {report.fatal=String(error);console.error(error);process.exitCode=1;}
  finally {
    report.passed=report.checks.filter(c=>c.pass).length;report.failed=report.checks.filter(c=>!c.pass).length;
    if(report.failed)process.exitCode=1;
    fs.writeFileSync(path.join(out,'browser_check.json'),JSON.stringify(report,null,2)+'\n');
    try{await cdp('Browser.close');}catch(_){}
    try{process.kill(-browser.pid,'SIGKILL');}catch(_){}
    fs.closeSync(log);for(const p of pending.values())clearTimeout(p.timer);
  }
})();
