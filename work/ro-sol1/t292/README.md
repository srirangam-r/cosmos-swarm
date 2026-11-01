# Task 292: task 277 input handoff

Two original GAUGE source videos and two selected input images are pinned in
`manifest.json`. **No model jobs were submitted; this is not a queue-ready batch.**

The originals are video `6.mp4` and `14.mp4` at dataset revision
`f95bb06e7d11142f88ffd3b6b56c7258deb8fff6`. Both full-file SHA256 values match
the published source metadata in `work/codex-api-4/t8/output/clips/real_06.json`
and `real_14.json` at commit `0f135ad`. Those derivative videos and their
continuations were not used. No mocap file was downloaded or read.

Original container frame 0 lacks a clearly identifiable suspended bob. Both
rejected images are retained with null geometry. Before decoding another input,
board message **5966** fixed container index **186 for both scenes**, with no
search or reselection. Only indices 0 and 186 were inspected; later real motion,
period, amplitude, and angular velocity were not measured. Selecting a single
image from a dev video does not supply a real continuation to the recipe.

The selected images are `real06_f186.png` and `real14_f186.png`. Transform:
1280x720 to 832x468 with OpenCV INTER_AREA, then six black rows top and bottom.
Manual pixel coordinates (x right, y down; origin top left):

| Scene | Pivot | Bob center | Location tolerance |
| --- | --- | --- | --- |
| real06 | (322, 121) | (207, 154) | about 6 px |
| real14 | (324, 122) | (333, 252) | about 5 px |

The bob is motion blurred in both images; annotated PNGs allow review. These
tolerances describe manual placement, not statistical uncertainty or planted
calibration. Image geometry is insufficient to recover metric rod length,
gravity, real period, or velocity.

`candidate_proxy_contract` explicitly proposes the parent's prescribed periods
1.186 / 2.0162 s, 85-degree amplitude, inward direction, and
`release_from_rest=False`. The amplitude is a supplied setting borrowed from
the existing demo, not a recovered property of these scenes. In particular,
real14 is near vertical: silently applying the CLI's release-from-rest default
would prescribe a tiny oscillation. The executor must explicitly adopt or
replace the proposed initial-state contract before generating proxies. This
handoff does not modify the proxy builder or the native schedule review (291).

Reproduce in an environment with Python, numpy and opencv-python:

```bash
python3 work/ro-sol1/t292/reproduce.py
python3 work/ro-sol1/t292/reproduce.py --sources /tmp/ro-sol1-t292 --out /tmp/ro-sol1-t292-reproduced
# On another host, add --download to obtain the two originals (~142 MB total).
```

`reproduction.json` records the actual source-hash and exact pixel reproduction
run. `runtime.json` pins the local library versions. The script decodes one
declared frame per seek, never scans a continuation, and cannot submit anything.
Source videos remain outside the repository.

Still required for parent 277: executor adoption, exact common prompt/negative/
guidance and proxy builder, full native sampler/sigma/stack freeze and returned
start verification, and referee-owner decision 5939. The independent crossing
reader retains its **UNVALIDATED / referee FAIL** status. No physical improvement,
Nano period, planted PASS, or NVIDIA-scoreboard result is established here.

Prior work read beyond abstracts before claiming: [ProxyUp](https://arxiv.org/abs/2607.03732)
sections 4–5 (supplied dynamics separate from appearance),
[GAUGE](https://arxiv.org/abs/2608.05948) C.1/C.3 (input identity/timebase), and
[Physics-IQ](https://arxiv.org/abs/2501.09038) Metrics (matched conditioning and
spatiotemporal motion). Parent note 5953, child note 5956. This reuses provenance
and reporting distinctions; it does not repeat their experiments.
