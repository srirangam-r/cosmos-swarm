#!/usr/bin/env python3
"""Exercise shipped Nano-Phys CLI + real queue serializer without network access."""
import argparse
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from types import SimpleNamespace

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASELINE = "0596dc120705693e0ea30ee9d8f6810452a46241"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queue-client", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, condition):
        checks.append({"name": name, "pass": bool(condition)})
        if not condition:
            raise AssertionError(name)

    queue_source = args.queue_client.read_bytes()
    (out / "cosmos_queue_snapshot.py").write_bytes(queue_source)
    spec = importlib.util.spec_from_file_location("queue_under_test", args.queue_client)
    queue = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(queue)
    # This test never binds a listener or contacts a real service.
    def denied(*a, **kw):
        raise AssertionError("network forbidden in serialization smoke")
    socket.socket.connect = denied
    socket.create_connection = denied
    captured = []

    def intercept(url, method="GET", body=None, raw=False):
        check("queue post targets inert fixture URL", url == "http://queue.invalid/jobs" and method == "POST")
        captured.append(body)
        return {"id": "LOCAL-INTERCEPT-ONLY"}

    queue.call = intercept
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    source_hashes = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in (ROOT / "tools/nano_phys").glob("*.py")}
    cases = []
    child = (
        "import runpy,socket; "
        "deny=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('network forbidden')); "
        "socket.socket.connect=deny; socket.create_connection=deny; "
        "runpy.run_module('tools.nano_phys',run_name='__main__')"
    )
    with tempfile.TemporaryDirectory(prefix="ro-sol1-t297-baseline-") as temp:
        baseline_root = Path(temp)
        pkg = baseline_root / "tools/nano_phys"
        pkg.mkdir(parents=True)
        for name in ("__init__.py", "__main__.py", "cli.py", "proxy.py", "runner.py"):
            data = subprocess.check_output(["git", "show", f"{BASELINE}:tools/nano_phys/{name}"], cwd=ROOT)
            (pkg / name).write_bytes(data)
        for physics in ("pendulum", "ball"):
            folder = out / f"{physics} fixture"
            folder.mkdir(exist_ok=True)
            image = np.full((480, 832, 3), 160, np.uint8)
            if physics == "pendulum":
                cv2.line(image, (322, 122), (270, 248), (35, 40, 55), 8)
                cv2.circle(image, (270, 248), 13, (35, 85, 190), -1)
                opts = ["--pivot", "322,122", "--bob", "270,248", "--period", "1.186", "--no-release-from-rest", "--amplitude", "85"]
            else:
                cv2.circle(image, (280, 118), 13, (30, 40, 210), -1)
                cv2.line(image, (100, 340), (700, 340), (40, 40, 40), 10)
                opts = ["--center", "280,118", "--floor-y", "340", "--g", "9.81", "--e", "0.58"]
            image_path = folder / "synthetic input.png"
            cv2.imwrite(str(image_path), image)
            prompt = 'Queue fixture: "quoted" caption\nsecond line, π, and $literal'
            negative = "No blur\nno duplication"
            common = ["--image", str(image_path), "--prompt", prompt, "--negative-prompt", negative,
                      "--physics", physics, "--num-frames", "93", "--fps", "24", "--start-step", "7",
                      "--steps", "35", "--guidance", "4.25", "--flow-shift", "8.5", "--seed", "101",
                      "--emit-queue-job", *opts]
            records = {}
            for label, cwd in (("before", baseline_root), ("after", ROOT)):
                argv = [sys.executable, "-c", child, *common, "--out", str(folder / f"{label} output.mp4")]
                run = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=60)
                (folder / f"{label}.stdout").write_text(run.stdout)
                (folder / f"{label}.stderr").write_text(run.stderr)
                check(f"{physics} {label} CLI exits zero", run.returncode == 0)
                try:
                    job = json.loads(run.stdout)
                    pure = True
                except json.JSONDecodeError:
                    pure = False
                    job = next(json.loads(line) for line in run.stdout.splitlines() if line.startswith("{"))
                records[label] = {"stdout_pure_json": pure, "files_present": bool(job.get("files")),
                                  "ref_is_basename": Path(job["extra_params"]["latent"]["ref"]).name == job["extra_params"]["latent"]["ref"]}
                if label == "before":
                    check(f"{physics} baseline reproduces three defects", not any(records[label].values()))
                    continue
                check(f"{physics} after resolves three defects", all(records[label].values()))
                check(f"{physics} after exactly one JSONL record", len(run.stdout.splitlines()) == 1)
                check(f"{physics} logs on stderr", "[Nano-Phys]" in run.stderr)
                proxy = Path(job["files"][0])
                check(f"{physics} proxy attachment exists", proxy.is_file() and proxy.stat().st_size > 0)
                check(f"{physics} proxy basename ref binding", job["extra_params"]["latent"]["ref"] == proxy.name)
                cap = cv2.VideoCapture(str(proxy))
                frames = 0
                shapes = set()
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        break
                    frames += 1
                    shapes.add(frame.shape)
                fps = cap.get(cv2.CAP_PROP_FPS)
                cap.release()
                check(f"{physics} all93 proxy frames decode", frames == 93 and shapes == {(480, 832, 3)} and fps == 24)
                jsonl = folder / "after.stdout"
                stdout, stderr = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    queue.submit(SimpleNamespace(endpoints="q8-0", jobs=jsonl, owner="ro-sol1-LOCAL-ONLY", url="http://queue.invalid"))
                body = captured[-1]
                check(f"{physics} real serializer exact proxy bytes", base64.b64decode(body["files"][0]["b64"]) == proxy.read_bytes())
                check(f"{physics} real serializer exact image bytes", base64.b64decode(body["image_b64"]) == image_path.read_bytes())
                check(f"{physics} real serializer basename binding", body["files"][0]["name"] == body["extra_params"]["latent"]["ref"] == proxy.name)
                check(f"{physics} real serializer multiline caption preserved", body["prompt"] == prompt and body["negative_prompt"] == negative)
                settings = {"width": 832, "height": 480, "num_frames": 93, "fps": 24, "steps": 35,
                            "guidance": 4.25, "flow_shift": 8.5, "seed": 101}
                check(f"{physics} real serializer all sampling fields", all(body[k] == v for k, v in settings.items()))
                check(f"{physics} real serializer CPU and explicit fixture start", body["extra_params"] == job["extra_params"] and body["extra_params"]["noise"]["device"] == "cpu" and body["extra_params"]["latent"]["start_step"] == 7)
                check(f"{physics} real serializer owner/endpoints", body["owner"] == "ro-sol1-LOCAL-ONLY" and body["endpoints"] == ["q8-0"])
                check(f"{physics} no baseline files uploaded", len(body["files"]) == 1 and body["files"][0]["name"].startswith("after"))
                summary = {k: v for k, v in body.items() if k not in ("files", "image_b64")}
                summary["files"] = [{"name": body["files"][0]["name"], "bytes": proxy.stat().st_size, "sha256": sha(proxy.read_bytes())}]
                summary["image_sha256"] = sha(image_path.read_bytes())
                (folder / "intercepted_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
                records["proxy"] = {"frames": frames, "fps": fps, "width": 832, "height": 480,
                                    "bytes": proxy.stat().st_size, "sha256": sha(proxy.read_bytes())}
                # Retain only current fixture proxy media; baseline is captured by logs/hashes.
                (folder / "before output_proxy.mp4").unlink()
            cases.append({"physics": physics, **records})
    result = {"scope": "CPU serialization/upload-byte smoke only; no live submission, native sigma, renderer geometry or physics validation",
              "source_commit": current, "baseline_commit": BASELINE, "source_sha256": source_hashes,
              "queue_client_sha256": sha(queue_source), "local_intercepts": len(captured),
              "network_requests": 0, "passed": sum(c["pass"] for c in checks), "failed": sum(not c["pass"] for c in checks),
              "cases": cases, "checks": checks}
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("source_commit", "local_intercepts", "network_requests", "passed", "failed")}, indent=2))


if __name__ == "__main__":
    main()
