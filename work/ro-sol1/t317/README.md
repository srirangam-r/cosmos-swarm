# Task 317: visual evidence for the pendulum dial

Open `index.html` locally after checking out the source folder. It indexes all 20
original author JPEG contact sheets and stores all 93 consecutive frames of the
disputed `dial_pend11_P600_s2` clip in eight lossless WebP strips. Click a strip
to inspect the native 832×480 frame rectangles. Labels occupy separate margins.
The author sheets sample every 6 frames; the new dense strips omit no frames.

**The reader disagreement remains unresolved.** The author reports MP≈0.293 s
and ACF≈0.599 s for a prescribed 0.600 s proxy. This artifact selects neither
reader, makes no new period estimate, and does not establish physical accuracy.
The publication with two scenes and two seeds still lacks the requested third scene.
Task 316 owns the independent numerical/reader-gate audit.

## Reproduce

From the repository root, with Python3, OpenCV, NumPy, Pillow with WebP support,
and `ffprobe` installed:

```bash
# Only needed for a sparse checkout:
git sparse-checkout add work/ro-3/task265 work/ro-sol1/t317
python3 work/ro-sol1/t317/build.py
# Optional browser acceptance and screenshots, using installed Brave and Node:
node work/ro-sol1/t317/render.cjs
```

The builder checks source blobs against commit 823a546 before reading them and
fails if the source changes. All 20 author sheet image paths resolve within this
checkout; the JPEGs are reused without copying or rewriting them. Published
clip, sidecar, queue QC and reader-plot links point to the frozen Git commit.
Opening private GitHub links requires repository access.

`manifest.json` records source SHA256 and Git blob identities, decoder versions,
all 93 frame indices and rational timestamps, container presentation timestamps,
RGB array hashes and frame rectangles. It also records SHA256 for each dense
strip. The builder decodes every lossless strip and compares each frame rectangle
exactly against the RGB array decoded from the source MP4. This validates pixel
preservation under the recorded decoder; it is not model or physical validation.
No claim is made that another decoder has bit-identical color conversion.

The browser check uses anonymous CDP pipes and a temporary profile, opens local
files, checks all 28 image decodes and desktop/mobile overflow, and closes its
browser process group. It starts no listener or persistent service. It does not
play videos or adjudicate motion.

## Evidence boundaries

Only `work/ro-sol1/t317/` is added. Author evidence, the judged root README and
`reports/board/` are untouched. No generation, GPU, paid compute, queue/referee
submission, estimator rerun, service modification, live playback, NVIDIA score,
or independent physical finding is part of this contribution.

Prior work was read beyond abstracts before creation/claim: [ProxyUp](https://arxiv.org/abs/2607.03732)
§§4.2–5 distinguishes prescribed dynamics from appearance; [GAUGE](https://arxiv.org/abs/2608.05948)
C.3.1/C.3.6 requires true frame times and separates period and geometry from fit;
[Physics-IQ](https://arxiv.org/abs/2501.09038v2) Metrics separates spatial,
temporal and visual agreement. The packaging reuses these distinctions and
does not repeat their established transfer experiments.

Coordination: parent 265 messages 6295/6296/6297; author 6300 approved this strip
scope and confirmed no duplicate work; reviewer 6302 confirmed it fills the
presentation gap while preserving reader disagreement.
