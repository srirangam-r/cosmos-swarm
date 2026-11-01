"""E6-W donor builder (dk2): wrong-period donors for the E6 tlo/all arms.
Same transform as codex-api-4 t8 (read_distinct: content-dedup by 0.1*median pair-MAE, nominal 25 Hz, 832x468 INTER_AREA
+ 6 px black padding), but we read up to 600 container frames and resample the distinct-frame sequence by SPEED=10/7
(nearest frame): out[k] = F[93 + round(k*SPEED)], k=0..92. Frame 0 == real_XX frame 0. Real period ~29.4 f -> ~20.6 f.
Usage: python -I build_warp.py RAW_DIR OUT_DIR id [id ...]   (RAW_DIR holds GAUGE pendulum video/<id>.mp4)
"""
import json, sys, hashlib
from pathlib import Path
import numpy as np, cv2

SPEED = 10 / 7


def read_distinct(path, nmax=600):
    cap = cv2.VideoCapture(str(path)); diffs = []; frames = []; prev = None
    for k in range(nmax):
        ok, frame = cap.read()
        if not ok: break
        if prev is not None: diffs.append(float(np.abs(frame.astype(np.float32) - prev).mean()))
        prev = frame.astype(np.float32)
        lb = np.zeros((480, 832, 3), np.uint8); lb[6:474] = cv2.resize(frame, (832, 468), interpolation=cv2.INTER_AREA)
        frames.append(lb)
    cap.release(); cut = 0.1 * np.median(diffs[:299])  # same cut as t8 (median over the first 300 container frames)
    keep = np.r_[0, 1 + np.flatnonzero(np.array(diffs) >= cut)]
    return np.array(frames)[keep]


raw, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
for i in map(int, sys.argv[3:]):
    F = read_distinct(raw / f"{i}.mp4")
    idx = [93 + int(round(k * SPEED)) for k in range(93)]
    assert idx[-1] < len(F), (i, len(F), idx[-1])
    p = out / f"realw_{i:02}.mp4"
    vw = cv2.VideoWriter(str(p), cv2.VideoWriter_fourcc(*"mp4v"), 25, (832, 480))
    for j in idx: vw.write(F[j])
    vw.release()
    (out / f"realw_{i:02}.json").write_text(json.dumps(dict(
        kind="real GAUGE dev-video derivative, time-warped (wrong-period donor control, E6-W); measurement/inversion only",
        source_video=f"InternRobotics/GAUGE-Dataset@f95bb06e data/rigid/pendulum/video/{i}.mp4",
        source_sha256=hashlib.sha256((raw / f"{i}.mp4").read_bytes()).hexdigest(),
        transform="t8 read_distinct (600 container frames, cut from first 300) ; distinct frames 93 + round(k*10/7), k<93",
        speed=SPEED, n_distinct=len(F), fps=25, num_frames=93), indent=1))
    print(i, "distinct", len(F), "->", p, flush=True)
