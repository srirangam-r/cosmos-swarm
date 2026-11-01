// Shared controls and loop boundaries. This is not frame-accurate playback.
const demoPairs = new Map();
function pairFor(ids) {
  return demoPairs.get(ids[0]) || demoPairs.get(ids[1]);
}
function paintButton(pair) {
  const button = pair.videos[0].closest('section').querySelector('.sync-controls button');
  if (button) button.textContent = pair.playing ? 'Pause' : 'Play';
}
function pausePair(pair) {
  pair.playing = false;
  pair.videos.forEach(v => v.pause());
  paintButton(pair);
}
async function playPair(pair) {
  pair.playing = true;
  paintButton(pair);
  try {
    await Promise.all(pair.videos.map(v => v.play()));
  } catch (_) {
    // Browser autoplay/codec failures must not leave one side playing alone.
    pausePair(pair);
  }
}
function resetPair(pair) {
  pair.videos.forEach(v => { v.currentTime = 0; });
}
function togglePlay(ids) {
  const pair = pairFor(ids);
  if (!pair || pair.loading) return;
  if (pair.playing) pausePair(pair); else playPair(pair);
}
function restartSync(ids) {
  const pair = pairFor(ids);
  if (!pair || pair.loading) return;
  resetPair(pair);
  playPair(pair);
}
function setSpeed(ids, value) {
  const rate = Number(value);
  if (!Number.isFinite(rate) || rate <= 0) return;
  ids.forEach(id => { document.getElementById(id).playbackRate = rate; });
}
function switchVideo(targetId, baseSrc, button) {
  const pair = demoPairs.get(targetId);
  if (!pair || pair.loading) return;
  const target = document.getElementById(targetId);
  const resume = pair.playing;
  const rate = target.playbackRate;
  pausePair(pair);
  pair.loading = true;
  resetPair(pair);
  const clean = () => {
    target.removeEventListener('loadedmetadata', ready);
    target.removeEventListener('error', failed);
    pair.loading = false;
  };
  const ready = () => {
    clean();
    resetPair(pair);
    pair.videos.forEach(v => { v.playbackRate = rate; });
    button.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
    button.classList.add('active');
    if (resume) playPair(pair);
  };
  const failed = () => { clean(); pausePair(pair); };
  target.addEventListener('loadedmetadata', ready);
  target.addEventListener('error', failed);
  target.innerHTML = `<source src="${baseSrc}.mp4" type="video/mp4"><source src="${baseSrc}.webm" type="video/webm">`;
  target.load();
}
function attachPair(id0, id1) {
  const videos = [document.getElementById(id0), document.getElementById(id1)];
  if (videos.some(v => !v)) return;
  const pair = {videos, playing: false, loading: false};
  videos.forEach(v => {
    // Native independent looping suppresses 'ended' and allows pair drift.
    v.loop = false;
    v.autoplay = false;
    v.pause();
    demoPairs.set(v.id, pair);
    v.addEventListener('ended', () => {
      if (!pair.playing || pair.loading) return;
      resetPair(pair);
      playPair(pair);
    });
    v.addEventListener('error', () => pausePair(pair));
  });
  playPair(pair);
}
for (let row = 1; row <= 5; row++) attachPair(`v-r${row}-left`, `v-r${row}-right`);
