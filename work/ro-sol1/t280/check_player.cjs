// Deterministic event/control checks, not browser or codec validation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const elements = new Map();
const buttons = new Map();
function video(id) {
  const listeners = new Map();
  const button = {textContent: ''};
  buttons.set(id, button);
  return {
    id, paused: true, currentTime: 0, playbackRate: 1, loop: true,
    autoplay: true, failPlay: false, loads: 0,
    play() { this.paused = false; return this.failPlay ? Promise.reject(new Error('Autoplay blocked')) : Promise.resolve(); },
    pause() { this.paused = true; },
    load() { this.loads++; this.playbackRate = 1; },
    addEventListener(type, fn) { if (!listeners.has(type)) listeners.set(type, new Set()); listeners.get(type).add(fn); },
    removeEventListener(type, fn) { listeners.get(type)?.delete(fn); },
    emit(type) { for (const fn of [...(listeners.get(type) || [])]) fn(); },
    closest() { return {querySelector() {return button;}}; }
  };
}
for (let row = 1; row <= 5; row++) {
  for (const side of ['left', 'right']) {
    const id = `v-r${row}-${side}`;
    elements.set(id, video(id));
  }
}
const context = vm.createContext({document: {getElementById: id => elements.get(id)}});
const html = fs.readFileSync(path.join(__dirname, 'corrected_index.html'), 'utf8');
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
const run = script => vm.runInContext(script, context);
const pairIds = "['v-r1-left','v-r1-right']";
const left = elements.get('v-r1-left');
const right = elements.get('v-r1-right');
const checks = [];
const variant = {active:false, classList:{add() {variant.active=true;}}};
variant.parentElement = {querySelectorAll() {return [{classList:{remove() {}}}];}};
context.variant = variant;
const settle = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  await settle();
  assert(!left.paused && !right.paused && !left.loop && !right.loop);
  checks.push('paired autoplay and shared loop boundaries');
  run(`togglePlay(${pairIds})`);
  assert(left.paused && right.paused);
  checks.push('pause both from pair control');
  run(`setSpeed(${pairIds}, '0.5')`);
  left.currentTime = 1.3; right.currentTime = 1.1;
  run("switchVideo('v-r1-right','clips/control',variant)");
  assert(left.paused && right.paused && left.currentTime === 0 && right.currentTime === 0);
  right.emit('loadedmetadata');
  await settle();
  assert(left.paused && right.paused && variant.active);
  assert(left.playbackRate === .5 && right.playbackRate === .5);
  checks.push('paused variant change keeps pause, resets both, restores speed after load');
  run(`togglePlay(${pairIds})`); await settle();
  left.currentTime = 2.2; right.currentTime = 2.1;
  run("switchVideo('v-r1-right','clips/physical',variant)");
  assert(left.paused && right.paused);
  right.emit('loadedmetadata'); await settle();
  assert(!left.paused && !right.paused && left.currentTime === 0 && right.currentTime === 0);
  checks.push('playing variant change waits for metadata then restarts both');
  left.currentTime = 3.875; right.currentTime = 3.875;
  left.emit('ended'); await settle();
  assert(left.currentTime === 0 && right.currentTime === 0 && !left.paused && !right.paused);
  checks.push('first clip ended resets and resumes both');
  run("switchVideo('v-r1-right','clips/broken',variant)");
  right.emit('error'); await settle();
  assert(left.paused && right.paused);
  assert(buttons.get(left.id).textContent === 'Play');
  checks.push('variant load error leaves both paused');
  right.failPlay = true;
  run(`togglePlay(${pairIds})`); await settle();
  assert(left.paused && right.paused && buttons.get(left.id).textContent === 'Play');
  checks.push('autoplay rejection pauses both and offers Play');
  right.failPlay = false;
  left.currentTime = 1; right.currentTime = 2;
  run(`restartSync(${pairIds})`); await settle();
  assert(left.currentTime === 0 && right.currentTime === 0 && !left.paused && !right.paused);
  checks.push('restart recovers paired playback');
  const expectedSource = fs.readFileSync(path.join(__dirname, 'player.js'), 'utf8').trim();
  assert.equal(html.match(/<script>([\s\S]*?)<\/script>/)[1].trim(), expectedSource);
  assert(!html.includes('href="#5315"') && !html.includes('href="#5440"') && !html.includes('href="#2720"') && !html.includes('href="#5563"'));
  assert(!html.includes('Total Verified Fixes') && !html.includes('85.0% Settle') && !html.includes('21&times; Acceleration Gain'));
  checks.push('tested JS equals embedded release copy; old unsupported headlines and dead anchors removed');
  console.log(JSON.stringify({scope:'Node mock media-event/control checks; no browser execution',checks_passed:checks.length,checks},null,2));
})().catch(error => { console.error(error); process.exitCode=1; });
