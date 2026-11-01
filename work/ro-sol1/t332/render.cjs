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

(async()=>{
 try {
  report.browser_pid=browser.pid;report.browser=await cdp('Browser.getVersion');
  const target=await cdp('Target.createTarget',{url:'about:blank'});
  ({sessionId:session}=await cdp('Target.attachToTarget',{targetId:target.targetId,flatten:true}));
  await cdp('Page.enable',{},session);await cdp('Runtime.enable',{},session);
  const source=JSON.parse(fs.readFileSync(path.join(__dirname,'source/out/t276_results.json')));
  const frames=Object.fromEntries(JSON.parse(fs.readFileSync(path.join(__dirname,'source/frames.json'))).map(f=>[f.id,f]));
  for(const [name,width,height,mobile] of [['desktop',1440,1200,false],['mobile',390,1600,true]]){
   await cdp('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile},session);
   await cdp('Page.navigate',{url:pathToFileURL(preview).href},session);
   await until(`document.readyState==='complete'&&[...document.images].every(i=>i.complete&&i.naturalWidth>0)`);
   const state=await evaluate(`({overflow:document.documentElement.scrollWidth>innerWidth,text:document.querySelector('main').innerText,rows:[...document.querySelectorAll('#clips tbody tr')].map(r=>({clip:r.dataset.clip,cells:[...r.cells].map(c=>c.textContent)})),links:[...document.querySelectorAll('a')].map(a=>a.getAttribute('href')),images:[...document.images].map(i=>({src:i.getAttribute('src'),width:i.naturalWidth,height:i.naturalHeight}))})`);
   if(state.overflow||state.rows.length!==18)throw new Error('Layout or count failure');
   for(const phrase of ['supplied from later real video','ungated numerical readings','0/6 clean','does not determine angular velocity','NVIDIA non-regression','0.057','raw FAIL','Static images are not a playback check','three real_06 Nano-Phys MP4s','not a six-pair improvement estimate','not proof that the rendered swing failed'])if(!state.text.includes(phrase))throw new Error('Missing scope label: '+phrase);
   const links=state.links.filter(x=>!x.startsWith('http')).map(x=>({href:x,exists:fs.existsSync(path.resolve(__dirname,x.split('#')[0]))}));
   if(!links.every(x=>x.exists))throw new Error('Missing evidence link');
   for(const row of source.rows){
    const saved=state.rows.find(r=>r.clip===row.clip);if(!saved)throw new Error('Missing row '+row.clip);
    const norm=x=>x===null?'—':(x/frames[row.frame].P_real_s).toFixed(3);
    if(saved.cells[3]!== (row.clean?'PASS':'REJECT')||saved.cells[4]!==norm(row.P_acf_s)||saved.cells[5]!==row.flag_acf||saved.cells[6]!==norm(row.P_mp_s)||saved.cells[7]!==row.flag_mp||saved.cells[8]!==row.r2_mp.toFixed(2)||saved.cells[9]!==row.flicker.toFixed(4))throw new Error('Source display mismatch: '+row.clip);
   }
   await screenshot(name+'.png');
   const filters=[];
   for(const sceneName of ['all','real_06','real_14'])for(const armName of ['all','plain','nphys','nphys_x17']){
    await evaluate(`document.querySelector('#scene').value=${JSON.stringify(sceneName)};document.querySelector('#arm').value=${JSON.stringify(armName)};document.querySelector('#scene').dispatchEvent(new Event('change'))`);
    const visible=await evaluate(`[...document.querySelectorAll('#clips tbody tr')].filter(r=>!r.hidden).map(r=>r.dataset.clip)`);
    const expected=source.rows.filter(r=>(sceneName==='all'||r.frame===sceneName)&&(armName==='all'||r.arm===armName)).map(r=>r.clip);
    if(JSON.stringify(visible)!==JSON.stringify(expected))throw new Error('Filter mismatch');
    filters.push({scene:sceneName,arm:armName,visible});
   }
   await evaluate(`document.querySelector('#scene').value='all';document.querySelector('#arm').value='all';document.querySelector('#scene').dispatchEvent(new Event('change'));document.querySelector('#rows').scrollIntoView()`);
   await screenshot(name+'_rows.png');
   const sheets=[];
   for(const armName of ['nphys','plain','nphys_x17']){
    await evaluate(`document.querySelector('#sheet').value=${JSON.stringify(armName)};document.querySelector('#sheet').dispatchEvent(new Event('change'))`);
    await until(`document.querySelector('#sheet-image').complete&&document.querySelector('#sheet-image').naturalWidth>0`);
    const sheet=await evaluate(`({src:document.querySelector('#sheet-image').getAttribute('src'),width:document.querySelector('#sheet-image').naturalWidth,height:document.querySelector('#sheet-image').naturalHeight,href:document.querySelector('#sheet-link').getAttribute('href')})`);
    if(sheet.src!=='source/out/strip_'+armName+'.jpg'||sheet.href!==sheet.src)throw new Error('Sheet selector mismatch');
    sheets.push({arm:armName,...sheet});
   }
   await evaluate(`document.querySelector('#strips').scrollIntoView()`);await screenshot(name+'_sheet.png');
   report.renders.push({name,state,links,filters,sheets});
  }
  if(report.exceptions.length)throw new Error('Browser runtime exception');
  report.passed=true;
 }catch(e){report.error=e.stack;process.exitCode=1;}
 finally{
  fs.writeFileSync(path.join(out,'browser_render.json'),JSON.stringify(report,null,2)+'\n');
  try{await cdp('Browser.close')}catch(e){}
  if(browser.exitCode===null){try{process.kill(-browser.pid,'SIGTERM')}catch(e){}}
  fs.closeSync(log);fs.rmSync(profile,{recursive:true,force:true});
 }
})();
