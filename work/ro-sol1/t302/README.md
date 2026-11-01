# Original first frame in analytical proxies

Task302 fixes task300's observed raw composition defect in both Nano-Phys
builders: feathered blending with the inpainted background altered the first
image even at an identity affine transform. The builder now copies the resized
input into frame0 immediately before the existing MP4 writer. It changes no
mask, trajectory, resize, state, sampler, queue or model behavior.

**59/59 CPU checks pass on eight fixtures.** Baseline `d185781` reproduces the
defect in every fixture. Patched raw frame0 is pixel-identical to the resized
input in all eight; every one of the **576 subsequent raw frames** has the
same SHA256 as the baseline. Builder metadata is unchanged. All **1168 encoded
frames** across before/after clips decode at their requested dimensions/fps.

| Fixture | Frames per version | Baseline changed pixels in raw frame0 | Patched changed pixels |
| --- | --- | --- | --- |
| real06, P1.186 / P2.0162 | 93 each | 1868 each | 0 |
| real14, P1.186 / P2.0162 | 93 each | 2062 each | 0 |
| Synthetic pendulum, rest + resize | 25 | 437 | 0 |
| Synthetic ball, hold / no hold | 93 each | 336 each | 0 |
| Synthetic ball, one frame + resize | 1 | 160 | 0 |

**MP4 frame0 remains lossy.** Real06/14 patched decoded-vs-input mean absolute
channel differences are 3.54258/3.55665 on the 8-bit scale. We guarantee exact
raw pixels only after the existing resize and before encoding. Later encoded
bytes/pixels may differ because the codec predicts across frames; the unchanged
later-frame statement applies to the captured raw writer inputs. No new
flicker, semantic-mask, physical or endpoint-conditioning acceptance is claimed.
The ball's later stationary hold frames retain their baseline composition,
consistent with the narrow first-frame correction.

Run from a shared-repo clone with Python, numpy and opencv-python:

```bash
python3 work/ro-sol1/t302/check_frame0.py --out /tmp/ro-sol1-t302-recheck
```

The script loads the SHA256-pinned, unmodified `baseline_proxy.py` from d185781
and the current installed builder. It forwards the actual OpenCV raw frames
to the real encoder, records every raw-frame hash and fully decodes both
versions. Network connections are forbidden. The four real candidates reuse
the exact292 images and proposed296 harmonic state; the other four are clearly
synthetic software fixtures. Versions, source/input/media hashes, raw/decoded
first-frame PNGs, before/after MP4s, full comparisons and acceptance are under
`evidence/`. These clips are analytical proxies, **not Nano outputs**.

The original task300 archive remains unchanged and documents the previous
builder. Its checker is pinned to that historical source and should be rerun
from d185781, rather than against this changed builder. Any adoption for277
must pin the new builder and newly rendered proxy hashes explicitly. Proposed
state/prompt/input acceptance, mask/rig texture, native full-grid/start/suffix/
identity provenance and human5939's reader coverage decision remain separate.
Reader289 is still raw FAIL / UNVALIDATED; this change supplies no physics or
NVIDIA-score result and submits no model/queue/referee jobs.

Prior-work methods read before task create/claim, parent6089/child6091:
[ProxyUp](https://arxiv.org/abs/2607.03732) sections4.2–4.4 distinguishes
foreground dynamics from compositing/coherence with region noising and SFR;
[GAUGE](https://arxiv.org/abs/2608.05948) section3.3.1 fixes the shared first
image/prompt and evaluates calibrated trajectories separately;
[Physics-IQ](https://arxiv.org/abs/2501.09038) Metrics separates spatial from
framewise temporal agreement and visual realism. This is implementation
boundary acceptance using those distinctions, without rerunning published
motion-transfer experiments.

`availability.json` records gallery HTTP200 at17:38:34UTC with the same HTML
SHA256 as task299's browser acceptance. It is a point-in-time availability
check; no new browser or continuous-uptime claim is made.
