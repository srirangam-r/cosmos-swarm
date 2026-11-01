#!/usr/bin/env python3
"""Non-submitting runtime checks for the fixed 292/294 input-state handoff."""
import argparse
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path

import cv2
import numpy as np

PIN = "592bf7838ecfcc7eb5b7a5e5d1f7eebd1f91928d"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    repo = base.parents[2]
    inp = base.parent / "t292"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    original = subprocess.check_output(["git", "show", f"{PIN}:work/ro-sol1/t292/manifest.json"], cwd=repo)
    current = (inp / "manifest.json").read_bytes()
    assert original == current, "292 manifest changed from its pinned handoff"
    manifest = json.loads(current)
    code = (base / "input_boundary_review.js").read_bytes()
    messages = json.loads((base / "source_messages.json").read_text())
    delivered = "\n".join(m["body"].split("```javascript\n", 1)[1].split("\n```", 1)[0] for m in messages)
    expected = (delivered + "\nconsole.log(JSON.stringify(result,null,2));").strip() + "\n"
    assert code.decode().strip() == expected.strip(), "reviewer code differs from board6010+6011"
    review = json.loads(subprocess.check_output(["node", str(base / "input_boundary_review.js")]))
    (out / "reviewer_result.json").write_text(json.dumps(review, indent=2) + "\n")
    checks = []
    def check(name, condition, **details):
        assert bool(condition), (name, details)
        checks.append(dict(name=name, passed=True, **details))

    contract = {
        "schema": "t277-input-state-clarification-v1",
        "status": "PROPOSED; EXECUTOR_ADOPTION_REQUIRED; NOT_QUEUE_READY",
        "input_manifest_commit": PIN,
        "input_manifest_path": "work/ro-sol1/t292/manifest.json",
        "input_manifest_sha256": sha(current),
        "clarification_messages": [6005, 6013],
        "review_source_messages": [6010, 6011],
        "review_source_sha256": sha(code),
        "uncertainty": {
            "model": "Independent per-coordinate +/-tolerance for BOTH pivot and bob",
            "provenance": "Conservative review interpretation agreed in6005; rough manual annotation, not calibrated hard bounds or statistical CI",
            "confidence_level": None,
            "includes_motion_blur_calibration": False,
        },
        "angle_right_rad": "atan2(bob_x-pivot_x,bob_y-pivot_y)",
        "angle_left_rad": "-angle_right_rad",
        "omega_left_rad_s": "-omega_right_rad_s",
        "opencv_rotation_deg": "degrees(theta_right(t)-theta_right(0)); negative of left-positive angular change",
        "temporal_law": "Prescribed harmonic theta(t)=theta0*cos(2*pi*t/P)+(omega0*P/(2*pi))*sin(2*pi*t/P); not nonlinear pendulum dynamics",
        "amplitude_deg": 85,
        "state_source": "SUPPLIED, not recovered real velocity/amplitude/period",
        "metric_length_m": None, "g_m_s2": None,
        "num_frames": 93, "fps": 24,
        "records": [],
        "remaining_gates": manifest["remaining_gates"] + [
            "state/builder must adopt this explicit harmonic law or explicitly replace it",
            "actual proxy rendered frame0/rod/crop/mask/codec QA remains pending",
            "native provenance follow-up295 and queue serialization5975 acceptance",
        ],
        "reader_status": "UNVALIDATED; referee5933 raw FAIL; human5939 pending",
        "queue_job_ids": [],
    }
    for rec, derived in zip(manifest["records"], review["sceneResults"], strict=True):
        label = f"real{rec['id']:02d}"
        geom = rec["geometry"]
        pivot = np.array(geom["pivot_xy"], dtype=float)
        bob = np.array(geom["bob_xy"], dtype=float)
        image_bytes = (inp / rec["image"]).read_bytes()
        img = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        check(label + " image identity", sha(image_bytes) == rec["image_sha256"], sha256=sha(image_bytes))
        check(label + " resolution", img.shape == (480, 832, 3), shape=list(img.shape))
        check(label + " fixed index", rec["frame_index"] == 186)
        check(label + " source match", label == derived["scene"])
        dx, dy = bob - pivot
        right = math.atan2(dx, dy)
        check(label + " angle convention", abs(math.degrees(right) + geom["theta0_deg_left_positive"]) < 1e-12)
        check(label + " source geometry", abs(right - derived["geometry"]["theta0"]) < 1e-14 and abs(np.linalg.norm(bob-pivot) - derived["geometry"]["radiusPx"]) < 1e-12)
        zero = cv2.getRotationMatrix2D(tuple(pivot), 0, 1)
        warped = cv2.warpAffine(img, zero, (832, 480), flags=cv2.INTER_LINEAR)
        check(label + " zero rotation pixel identity", np.array_equal(img, warped), max_abs_error=int(np.abs(img.astype(int)-warped.astype(int)).max()))
        overlay = img.copy()
        cv2.circle(overlay, tuple(pivot.astype(int)), 5, (0, 255, 0), 2)
        cv2.circle(overlay, tuple(bob.astype(int)), 7, (0, 255, 255), 2)
        records = []
        for state in derived["starts"]:
            period = state["periodS"]
            w = 2 * math.pi / period
            v0 = state["angularVelocity0"]
            theta1 = right * math.cos(w/24) + v0/w * math.sin(w/24)
            alpha_deg = math.degrees(theta1-right)
            matrix = cv2.getRotationMatrix2D(tuple(pivot), alpha_deg, 1)
            actual = matrix @ np.r_[bob, 1]
            expected_point = pivot + np.linalg.norm(bob-pivot) * np.array([math.sin(theta1), math.cos(theta1)])
            point_error = float(np.linalg.norm(actual-expected_point))
            prefix = f"{label} P{period}"
            check(prefix + " cv2 rotation sign", point_error < 1e-10, affine_error_px=point_error)
            check(prefix + " reviewer frame1", np.linalg.norm(actual-state["bobFrame1"]) < 1e-10)
            wrong = cv2.getRotationMatrix2D(tuple(pivot), -alpha_deg, 1) @ np.r_[bob, 1]
            check(prefix + " sign reversal detected", np.linalg.norm(wrong-actual) > 10, wrong_sign_distance_px=float(np.linalg.norm(wrong-actual)))
            check(prefix + " zero angle pivot invariant", np.linalg.norm(matrix @ np.r_[pivot, 1] - pivot) < 1e-10)
            records.append({
                "period_s": period, "theta0_right_rad": right,
                "theta0_left_rad": -right, "omega0_right_rad_s": v0,
                "omega0_left_rad_s": -v0,
                "absolute_omega_sign_right": 1 if v0 > 0 else -1,
                "direction_source": "Prescribed nominal inward sign; not observed motion",
                "frame1_time_s": 1/24, "frame1_theta_right_rad": theta1,
                "frame1_cv2_rotation_deg": alpha_deg,
                "frame1_expected_bob_center_px": expected_point.tolist(),
            })
            point = tuple(map(int, np.rint(actual)))
            cv2.arrowedLine(overlay, tuple(bob.astype(int)), point, (255, 80, 80), 2, tipLength=.3)
            cv2.putText(overlay, f"P{period}: supplied f1 {point}", (20, 425 + 20*len(records)), cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(overlay, f"{label}: annotation + prescribed harmonic f1; NOT observed motion", (12, 30), cv2.FONT_HERSHEY_SIMPLEX, .48, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imwrite(str(out / f"{label}_state_overlay.png"), overlay)
        contract["records"].append({
            "scene": label, "image": rec["image"], "image_sha256": rec["image_sha256"],
            "pivot_xy": pivot.tolist(), "bob_xy": bob.tolist(),
            "pivot_coordinate_tolerance_px": geom["manual_location_tolerance_px"],
            "bob_coordinate_tolerance_px": geom["manual_location_tolerance_px"],
            "theta_range_right_rad": derived["geometry"]["thetaRange"],
            "radius_range_px": derived["geometry"]["radiusRangePx"],
            "geometric_inward_sign_right": derived["geometry"]["inwardVelocitySign"],
            "geometric_direction_ambiguous": derived["geometry"]["inwardVelocitySign"] is None,
            "prescribed_states": records,
        })
    result = {
        "scope": "Input identity, reviewer-source fidelity, actual OpenCV point/zero-image transforms only; no proxy mask/clip/model validation",
        "runtime": {"python": platform.python_version(), "opencv": cv2.__version__, "numpy": np.__version__, "node": subprocess.check_output(["node", "--version"], text=True).strip()},
        "checks_passed": len(checks), "checks": checks,
        "reviewer_regression_summary": review["summary"],
        "reviewer_envelope_samples": review["envelopeSamples"],
    }
    (out / "state_contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    (out / "runtime_check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"checks_passed": len(checks), "reviewer": review["summary"], "out": str(out)}))


if __name__ == "__main__":
    main()
