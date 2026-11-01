#!/usr/bin/env python3
"""CPU-only before/after renderer check; no model, queue or referee calls."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import socket
import sys
from unittest.mock import patch

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.nano_phys import proxy

BASELINE_SHA = "1e7cbdff3ba78348ec13c21d329e8c0ce6d59afe1d1c7c0034f244572c670ff5"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def difference(a, b):
    d = np.abs(a.astype(np.int16) - b.astype(np.int16))
    return dict(changed_pixels=int(np.any(d != 0, axis=2).sum()),
                mae_8bit=float(d.mean()), max_channel_error=int(d.max()),
                identical=bool(np.array_equal(a, b)))


def forbidden(*args, **kwargs):
    raise RuntimeError("Network disabled for CPU-only renderer check")


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, value):
        checks.append(dict(name=name, passed=bool(value)))
        if not value:
            raise AssertionError(name)

    baseline_path = HERE / "baseline_proxy.py"
    check("immutable d185781 baseline source", sha(baseline_path.read_bytes()) == BASELINE_SHA)
    spec = importlib.util.spec_from_file_location("baseline_proxy", baseline_path)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    contract = json.loads((ROOT / "work/ro-sol1/t296/state_contract.json").read_text())
    cases = []
    for scene in contract["records"]:
        image = ROOT / "work/ro-sol1/t292" / scene["image"]
        check(scene["scene"] + " pinned image", sha(image.read_bytes()) == scene["image_sha256"])
        for state in scene["prescribed_states"]:
            cases.append((scene["scene"] + "_P" + str(state["period_s"]), "pendulum", dict(
                image_path=str(image), pivot=tuple(scene["pivot_xy"]), bob=tuple(scene["bob_xy"]),
                period=state["period_s"], amplitude_deg=85, release_from_rest=False,
                direction="inward", num_frames=93, fps=24, width=832, height=480)))
    pendulum = ROOT / "work/ro-sol1/t297/evidence/pendulum fixture/synthetic input.png"
    ball = ROOT / "work/ro-sol1/t297/evidence/ball fixture/synthetic input.png"
    cases.extend([
        ("synthetic_rest_resized", "pendulum", dict(image_path=str(pendulum), pivot=(161,61),
          bob=(135,124), period=1.186, release_from_rest=True, num_frames=25,
          fps=24, width=416, height=240)),
        ("synthetic_ball_hold", "ball", dict(image_path=str(ball), center=(280,118),
          hold=.25, num_frames=93, fps=24, width=832, height=480)),
        ("synthetic_ball_no_hold", "ball", dict(image_path=str(ball), center=(280,118),
          hold=0, num_frames=93, fps=24, width=832, height=480)),
        ("synthetic_ball_one_frame_resized", "ball", dict(image_path=str(ball), center=(140,59),
          floor_y=170, radius=7, ppm=269.9, hold=.25, num_frames=1,
          fps=24, width=416, height=240)),
    ])
    native_writer = cv2.VideoWriter
    records = []
    for name, kind, kwargs in cases:
        folder = out / name
        folder.mkdir(exist_ok=True)
        im = cv2.imread(kwargs["image_path"])
        if im.shape[:2] != (kwargs["height"], kwargs["width"]):
            im = cv2.resize(im, (kwargs["width"], kwargs["height"]), interpolation=cv2.INTER_AREA)
        trace = {}
        for label, module in [("before", baseline), ("after", proxy)]:
            hashes = []
            raw0 = None

            class Writer:
                def __init__(self, *args, **kw):
                    self.writer = native_writer(*args, **kw)
                    assert self.writer.isOpened()

                def write(self, frame):
                    nonlocal raw0
                    if not hashes:
                        raw0 = frame.copy()
                    hashes.append(sha(frame.tobytes()))
                    self.writer.write(frame)

                def release(self):
                    self.writer.release()

            mp4 = folder / (label + ".mp4")
            with patch.object(cv2, "VideoWriter", Writer):
                meta = getattr(module, "generate_" + kind + "_proxy")(**kwargs, out_path=mp4)
            cv2.imwrite(str(folder / (label + "_raw_frame0.png")), raw0)
            cap = cv2.VideoCapture(str(mp4))
            frames = 0
            fps = cap.get(cv2.CAP_PROP_FPS)
            decoded0 = None
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                assert frame.shape == im.shape
                if frames == 0:
                    decoded0 = frame.copy()
                frames += 1
            cap.release()
            check(name + " " + label + " full frame count/fps decode", frames == kwargs["num_frames"] and fps == kwargs["fps"])
            cv2.imwrite(str(folder / (label + "_decoded_frame0.png")), decoded0)
            trace[label] = dict(raw_frame_sha256=hashes, raw_frame0_vs_input=difference(raw0, im),
                decoded_frame0_vs_input=difference(decoded0, im), decoded_frame0_vs_raw=difference(decoded0, raw0),
                decoded_frames=frames, fps=fps, mp4_sha256=sha(mp4.read_bytes()),
                builder_metadata={k:v for k,v in meta.items() if k != "proxy_path"})
        check(name + " baseline reproduces raw frame0 defect", not trace["before"]["raw_frame0_vs_input"]["identical"])
        check(name + " patched raw frame0 exactly equals resized input", trace["after"]["raw_frame0_vs_input"]["identical"])
        check(name + " every raw frame after zero unchanged", trace["before"]["raw_frame_sha256"][1:] == trace["after"]["raw_frame_sha256"][1:])
        check(name + " builder metadata unchanged", trace["before"]["builder_metadata"] == trace["after"]["builder_metadata"])
        check(name + " codec differences explicitly remain", not trace["after"]["decoded_frame0_vs_input"]["identical"])
        record = dict(name=name, physics=kind, input=str(Path(kwargs["image_path"]).relative_to(ROOT)),
            input_sha256=sha(Path(kwargs["image_path"]).read_bytes()),
            kwargs={k:v for k,v in kwargs.items() if k != "image_path"}, trace=trace,
            status="ANALYTICAL CPU FIXTURE; NOT NANO OUTPUT OR EXECUTOR ADOPTION")
        (folder / "comparison.json").write_text(json.dumps(record, indent=2) + "\n")
        records.append(record)
    result = dict(status="RAW FRAME0 FIX VERIFIED; LOSSY CODEC AND EXISTING EXECUTOR GATES REMAIN",
        baseline_commit="d185781", baseline_source_sha256=BASELINE_SHA,
        patched_source_sha256=sha((ROOT / "tools/nano_phys/proxy.py").read_bytes()),
        versions=dict(python=platform.python_version(), opencv=cv2.__version__, numpy=np.__version__),
        check_count=len(checks), checks=checks, cases=records,
        controls=dict(socket_connections_forbidden=True, model_calls=0, queue_submissions=0, referee_calls=0),
        limits=["Exactness applies only before MP4 encoding and after existing input resize.",
                "Later raw frames are unchanged; interframe codec bytes/pixels may change.",
                "No new mask, physical, native schedule, endpoint or measurement validation.",
                "Frozen300 outputs remain unchanged; newly rendered proxies have different hashes.",
                "277 requires explicit builder/state/prompt adoption;289 raw FAIL/UNVALIDATED remains."])
    (out / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(checks=len(checks), passed=sum(c["passed"] for c in checks),
        cases=[dict(name=r["name"], before=r["trace"]["before"]["raw_frame0_vs_input"],
                    after=r["trace"]["after"]["raw_frame0_vs_input"],
                    codec_mae=r["trace"]["after"]["decoded_frame0_vs_input"]["mae_8bit"]) for r in records]), indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=HERE / "evidence")
    args = ap.parse_args()
    with patch.object(socket.socket, "connect", forbidden), patch.object(socket, "create_connection", forbidden):
        run(args.out.resolve())
