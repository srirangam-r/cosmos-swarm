    function singleVideoMode(v) {
      return v.dataset.format !== 'gif';
    }

    function paintSingle(v) {
      const controls = v.closest('section').querySelector('.sync-controls');
      const videoMode = singleVideoMode(v);
      controls.querySelectorAll('button, select').forEach(e => { e.disabled = !videoMode; });
      controls.querySelector('button').textContent = v.paused ? 'Play' : 'Pause';
    }

    function playSingle(v) {
      if (!singleVideoMode(v)) return;
      v.play().catch(() => paintSingle(v));
    }

    function toggleSinglePlay(id, btn) {
      const v = document.getElementById(id);
      if (!v || !singleVideoMode(v)) return;
      if (v.paused) playSingle(v); else v.pause();
      paintSingle(v);
    }

    function restartSingle(id) {
      const v = document.getElementById(id);
      if (!v || !singleVideoMode(v)) return;
      v.currentTime = 0;
      playSingle(v);
      paintSingle(v);
    }

    function setSingleSpeed(id, val) {
      const v = document.getElementById(id);
      if (!v || !singleVideoMode(v)) return;
      const rate = Number(val);
      if (Number.isFinite(rate) && rate > 0) v.playbackRate = rate;
    }

    function setFormat(vidId, imgId, fmt, btn) {
      const v = document.getElementById(vidId);
      const img = document.getElementById(imgId);
      if (!v || !img || !['gif', 'mp4'].includes(fmt)) return;
      btn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      v.dataset.format = fmt;
      v.style.display = fmt === 'gif' ? 'none' : 'block';
      img.style.display = fmt === 'gif' ? 'block' : 'none';
      if (fmt === 'gif') v.pause(); else playSingle(v);
      paintSingle(v);
    }

    document.querySelectorAll('video[id^="v-demo-"]').forEach(v => {
      v.dataset.format = 'mp4';
      ['play', 'pause', 'ended', 'error'].forEach(event => v.addEventListener(event, () => {
        if (!singleVideoMode(v) && !v.paused) v.pause();
        paintSingle(v);
      }));
      paintSingle(v);
    });
