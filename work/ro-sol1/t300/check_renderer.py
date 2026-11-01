#!/usr/bin/env python3
"""CPU-only acceptance fixture. No model import, network or queue submission."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import socket
import subprocess
import sys
from unittest.mock import patch

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.nano_phys import proxy

SOURCE_SHA = "1e7cbdff3ba78348ec13c21d329e8c0ce6d59afe1d1c7c0034f244572c670ff5"
CONTRACT_SHA = "62e6c8345aaf5d2ebedc43003355d5271edf1049371ff751cb1f2919b0d684a7"
SAMPLES = [0, 1, 7, 14, 28, 46, 70, 92]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def diff(a, b):
    d = np.abs(a.astype(np.int16) - b.astype(np.int16))
    return dict(mae_8bit=float(d.mean()), max_channel_error=int(d.max()),
                changed_pixels=int(np.any(d != 0, axis=2).sum()),
                pixels_over_10=int(np.any(d > 10, axis=2).sum()),
                pixel_identical=bool(np.array_equal(a, b)))


def forbidden(*args, **kwargs):
    raise RuntimeError("Network disabled in this CPU-only acceptance fixture")


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, ok, details=None):
        checks.append(dict(name=name, passed=bool(ok), details=details))
        if not ok:
            raise AssertionError(name)

    source = ROOT / "tools/nano_phys/proxy.py"
    cp = ROOT / "work/ro-sol1/t296/state_contract.json"
    check("pinned unmodified shipped renderer", sha(source) == SOURCE_SHA)
    check("pinned unmodified296 state contract", sha(cp) == CONTRACT_SHA)
    contract = json.loads(cp.read_text())
    check("pinned292 input manifest", sha(ROOT / contract["input_manifest_path"]) == contract["input_manifest_sha256"])
    native_writer = cv2.VideoWriter
    native_rotation = cv2.getRotationMatrix2D
    native_warp = cv2.warpAffine
    native_fill = cv2.fillPoly
    records = []
    for scene in contract["records"]:
        image_path = ROOT / "work/ro-sol1/t292" / scene["image"]
        check(scene["scene"] + " input hash", sha(image_path) == scene["image_sha256"])
        im = cv2.imread(str(image_path))
        pivot = np.array(scene["pivot_xy"])
        bob = np.array(scene["bob_xy"])
        for state in scene["prescribed_states"]:
            name = scene["scene"] + "_P" + str(state["period_s"])
            folder = out / name
            folder.mkdir(exist_ok=True)
            raw = {}
            matrices = []
            masks = []
            alpha_stats = []

            class Writer:
                def __init__(self, *args, **kwargs):
                    self.writer = native_writer(*args, **kwargs)
                    assert self.writer.isOpened()
                    self.n = 0

                def write(self, frame):
                    if self.n in SAMPLES:
                        raw[self.n] = frame.copy()
                    self.writer.write(frame)
                    self.n += 1

                def release(self):
                    self.writer.release()

            def rotation(*args, **kwargs):
                m = native_rotation(*args, **kwargs)
                matrices.append(m.copy())
                return m

            def fill(mask, *args, **kwargs):
                result = native_fill(mask, *args, **kwargs)
                masks.append(result.copy())
                return result

            def warp(src, *args, **kwargs):
                result = native_warp(src, *args, **kwargs)
                if src.dtype == np.float32 and (src.ndim == 2 or src.shape[-1] == 1):
                    a = result.reshape(result.shape[:2])
                    ys, xs = np.where(a > 1e-4)
                    alpha_stats.append(dict(mass=float(a.sum()), bounds_xyxy=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                                            active_border_pixels=int((a[0] > 1e-4).sum() + (a[-1] > 1e-4).sum() + (a[:, 0] > 1e-4).sum() + (a[:, -1] > 1e-4).sum())))
                return result

            kwargs = dict(image_path=str(image_path), out_path=str(folder / "proxy.mp4"),
                          pivot=tuple(map(int, pivot)), bob=tuple(map(int, bob)), period=state["period_s"],
                          amplitude_deg=85, release_from_rest=False, direction="inward",
                          num_frames=93, fps=24, width=832, height=480)
            with patch.object(cv2, "VideoWriter", Writer), patch.object(cv2, "getRotationMatrix2D", rotation), patch.object(cv2, "warpAffine", warp), patch.object(cv2, "fillPoly", fill):
                meta = proxy.generate_pendulum_proxy(**kwargs)
            check(name + " captured93 affine/composed/alpha frames", len(matrices) == 93 and len(alpha_stats) == 93 and len(raw) == 8)
            centers = np.array([m @ np.r_[bob, 1] for m in matrices])
            times = np.arange(93) / 24
            w = 2 * math.pi / state["period_s"]
            theta = state["theta0_right_rad"] * np.cos(w * times) + (state["omega0_right_rad_s"] / w) * np.sin(w * times)
            radius = float(np.linalg.norm(bob - pivot))
            expected = pivot + radius * np.stack([np.sin(theta), np.cos(theta)], axis=1)
            error = np.linalg.norm(centers - expected, axis=1)
            check(name + " all93 centers match independent296 harmonic state", error.max() < 1e-10, float(error.max()))
            check(name + " first-step pinned center", np.linalg.norm(centers[1] - state["frame1_expected_bob_center_px"]) < 1e-10)
            check(name + " affine frame0 identity", np.max(np.abs(matrices[0] - [[1, 0, 0], [0, 1, 0]])) < 1e-10)
            check(name + " fixed radius", np.max(np.abs(np.linalg.norm(centers-pivot, axis=1)-radius)) < 1e-10)
            # Transform the actual source alpha support, including feathered edges.
            alpha = cv2.GaussianBlur(masks[0], (0, 0), 2).astype(np.float32) / 255
            yy, xx = np.where(alpha > 1e-4)
            points = np.stack([xx, yy, np.ones_like(xx)])
            support_bounds = []
            for m in matrices:
                q = m @ points
                support_bounds.append([float(q[0].min()), float(q[1].min()), float(q[0].max()), float(q[1].max())])
            sb = np.array(support_bounds)
            check(name + " all93 transformed feathered supports inside frame", (sb[:, :2] > 0).all() and (sb[:, 2:] < [831, 479]).all())
            check(name + " all93 rendered alpha borders empty", all(a["active_border_pixels"] == 0 for a in alpha_stats))
            cap = cv2.VideoCapture(str(folder / "proxy.mp4"))
            fps = cap.get(cv2.CAP_PROP_FPS)
            decoded = {}
            n = 0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                assert frame.shape == (480, 832, 3)
                if n in SAMPLES:
                    decoded[n] = frame.copy()
                n += 1
            cap.release()
            check(name + " complete93-frame decode24fps", n == 93 and fps == 24)
            check(name + " first two decoded frames differ", not np.array_equal(decoded[0], decoded[1]))
            # Observations, deliberately not converted into a pixel-identity PASS.
            observations = dict(raw_composition_vs_input=diff(raw[0], im), encoded_frame0_vs_input=diff(decoded[0], im),
                                encoded_frame0_vs_raw=diff(decoded[0], raw[0]))
            cv2.imwrite(str(folder / "raw_frame0.png"), raw[0])
            cv2.imwrite(str(folder / "encoded_frame0.png"), decoded[0])
            delta = np.max(np.abs(raw[0].astype(np.int16) - im.astype(np.int16)), axis=2)
            cv2.imwrite(str(folder / "composition_difference_x8.png"), np.minimum(delta*8, 255).astype(np.uint8))
            cv2.imwrite(str(folder / "source_mask.png"), masks[0])
            # Fixed-index decoded contact sheet, with geometric-center overlays.
            tiles = []
            for i in SAMPLES:
                f = decoded[i].copy()
                cv2.circle(f, tuple(np.rint(centers[i]).astype(int)), 8, (0, 255, 255), 2)
                cv2.circle(f, tuple(pivot.astype(int)), 4, (0, 255, 255), 1)
                cv2.putText(f, f"f{i} t={i/24:.3f}s", (12, 25), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 255), 1, cv2.LINE_AA)
                tiles.append(cv2.resize(f, (416, 240)))
            sheet = np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])])
            cv2.imwrite(str(folder / "contact_sheet.jpg"), sheet)
            trace = [dict(frame=i, time_s=i/24, affine=matrices[i].tolist(), traced_bob_xy=centers[i].tolist(),
                          expected_theta_right_rad=float(theta[i]), transformed_source_alpha_bounds=support_bounds[i], rendered_alpha=alpha_stats[i]) for i in range(93)]
            (folder / "trace.json").write_text(json.dumps(trace, indent=2) + "\n")
            record = dict(name=name, source_image=scene["image"], source_image_sha256=sha(image_path), supplied_state=state,
                          renderer_sha256=sha(source), state_contract_sha256=sha(cp),
                          generation_kind="ANALYTICAL_CPU_PROXY; model inference not run",
                          model=None, checkpoint=None, prompt=None, negative_prompt=None, seed=None,
                          steps=None, guidance=None, flow_shift=None,
                          builder_kwargs={k: str(v) if isinstance(v, Path) else v for k, v in kwargs.items()}, builder_metadata=meta,
                          status="CPU PROXY ACCEPTANCE CANDIDATE; NOT NANO OUTPUT; EXECUTOR ADOPTION REQUIRED",
                          physical_state="Supplied harmonic A85; no inferred real period, velocity, g or metric length",
                          decoded_frames=n, fps=fps, duration_s=n/fps, max_center_contract_error_px=float(error.max()),
                          support_bounds_union=[float(sb[:,0].min()), float(sb[:,1].min()), float(sb[:,2].max()), float(sb[:,3].max())],
                          frame0_observations=observations,
                          files={p.name: dict(sha256=sha(p), bytes=p.stat().st_size) for p in sorted(folder.iterdir()) if p.name != "sidecar.json"})
            (folder / "sidecar.json").write_text(json.dumps(record, indent=2) + "\n")
            records.append(record)
    result = dict(status="GEOMETRY/DECODE CHECKS PASS; FRAME0 COMPOSITION NOT PIXEL IDENTICAL; NOT QUEUE READY",
                  source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  source_sha256=sha(source), contract_sha256=sha(cp),
                  versions=dict(python=platform.python_version(), opencv=cv2.__version__, numpy=np.__version__),
                  controls=dict(socket_connections_forbidden=True, model_calls=0, queue_submissions=0, referee_calls=0),
                  check_count=len(checks), checks=checks, records=records,
                  inherited296_gates=contract["remaining_gates"], reader_status=contract["reader_status"],
                  remaining_gates=["Executor must adopt exact292 images, supplied296 state, builder and prompts.",
                                   "Exact raw proxy frame0 identity is false; renderer owner must address/explicitly evaluate this before treating that gate as passed.",
                                   "Semantic mask/rig artifacts require executor visual acceptance; bounds alone do not certify segmentation.",
                                   "Native endpoint/full-grid/start/suffix/identity acceptance is outside this task.",
                                   "Reader289 remains raw FAIL/UNVALIDATED pending human5939; no277 jobs submitted."],
                  limits=["Centers trace the actual affine transform; not independent bob tracking.", "Mask/crop checks establish image bounds, not semantic rod/bob segmentation quality.",
                          "No frame0 pixel-identity criterion has been waived; compositing and encoding differences are recorded separately.",
                          "Proxy builder's g=9.81 default is unused for explicit P; it is not a real calibrated value."])
    (out / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(checks=len(checks), passed=sum(c["passed"] for c in checks), records=[dict(name=r["name"], frame0=r["frame0_observations"]) for r in records]), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "evidence")
    args = parser.parse_args()
    with patch.object(socket.socket, "connect", forbidden), patch.object(socket, "create_connection", forbidden):
        run(args.out.resolve())
