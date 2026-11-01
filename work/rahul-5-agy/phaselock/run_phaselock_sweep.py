#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
from pathlib import Path
import requests

SWARM_DIR = Path("/home/sha/devel/cosmos-swarm")
WORK_DIR = Path("/home/sha/swarm-work/rahul-5-agy/phaselock")
OUT_DIR = WORK_DIR / "out"
JOBS_FILE = WORK_DIR / "jobs_phaselock.jsonl"
PYTHON_VENV = "/home/sha/swarm-work/rahul-3/.venv/bin/python3"
FIRSTFALL_PY = str(SWARM_DIR / "tools/realball/firstfall.py")

ENDPOINTS = [
    "http://100.77.182.40:8021",
    "http://100.122.219.51:8011"
]

OUT_DIR.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def make_contact_sheet(mp4_path, out_sheet_path):
    try:
        import cv2
        import numpy as np
        cap = cv2.VideoCapture(str(mp4_path))
        frames = []
        target_indices = [0, 2, 4, 6, 8, 10, 14, 18, 22, 26, 30, 38, 46, 54, 62, 70, 80, 90]
        cur_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if cur_idx in target_indices:
                # Add frame index overlay
                h, w = frame.shape[:2]
                cv2.putText(frame, f"f{cur_idx}", (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
                frames.append(cv2.resize(frame, (w // 2, h // 2)))
            cur_idx += 1
        cap.release()
        if len(frames) >= 6:
            # Arrange in grid of 6 columns
            cols = 6
            rows = (len(frames) + cols - 1) // cols
            grid_h = rows * frames[0].shape[0]
            grid_w = cols * frames[0].shape[1]
            grid = np.zeros((grid_h, grid_w, 3), dtype=np.uint8)
            for i, f in enumerate(frames):
                r = i // cols
                c = i % cols
                grid[r*f.shape[0]:(r+1)*f.shape[0], c*f.shape[1]:(c+1)*f.shape[1]] = f
            cv2.imwrite(str(out_sheet_path), grid)
            log(f"Contact sheet saved to {out_sheet_path}")
    except Exception as e:
        log(f"Error making contact sheet: {e}")

def run_job(job):
    name = job["name"]
    mp4_file = OUT_DIR / f"{name}.mp4"
    json_file = OUT_DIR / f"{name}.json"
    qc_file = OUT_DIR / f"{name}_firstfall_qc.png"
    res_file = OUT_DIR / f"{name}_firstfall.json"
    sheet_file = OUT_DIR / f"{name}_sheet.jpg"

    if mp4_file.exists() and json_file.exists():
        log(f"Job {name} already generated, skipping inference.")
    else:
        log(f"Starting generation for {name} (steps={job['steps']}, guidance={job['guidance']}, seed={job['seed']})...")
        data = dict(
            prompt=job["prompt"],
            size=f"{job['width']}x{job['height']}",
            num_frames=str(job["num_frames"]),
            fps=str(job["fps"]),
            num_inference_steps=str(job["steps"]),
            guidance_scale=str(job["guidance"]),
            flow_shift=str(job["flow_shift"]),
            seed=str(job["seed"]),
            extra_params=json.dumps({"client": "rahul-5-agy", **job.get("extra_params", {})})
        )
        if job.get("negative_prompt"):
            data["negative_prompt"] = job["negative_prompt"]

        files = {"input_reference": (os.path.basename(job["image"]), open(job["image"], "rb").read(), "image/png")}

        generated = False
        t0 = time.time()
        for endpoint in ENDPOINTS:
            log(f"Trying endpoint {endpoint} for {name}...")
            for attempt in range(3):
                try:
                    r = requests.post(f"{endpoint.rstrip('/')}/v1/videos/sync", data=data, files=files, timeout=7200)
                    r.raise_for_status()
                    mp4_file.write_bytes(r.content)
                    meta = {
                        **job,
                        "endpoint": endpoint,
                        "server_clip_id": r.headers.get("X-Clip-Id"),
                        "seconds": float(r.headers.get("X-Seconds", 0)),
                        "wall_seconds": round(time.time() - t0, 1)
                    }
                    with open(json_file, "w") as f:
                        json.dump(meta, f, indent=1)
                    log(f"Generated {name} in {time.time()-t0:.1f}s via {endpoint}")
                    generated = True
                    break
                except Exception as e:
                    log(f"Attempt {attempt+1} on {endpoint} failed for {name}: {e}")
                    time.sleep(10)
            if generated:
                break

        if not generated:
            log(f"FAILED to generate {name} on all endpoints.")
            return

    # Now evaluate with firstfall.py
    if not res_file.exists():
        log(f"Measuring {name} with firstfall.py...")
        cmd = [
            PYTHON_VENV,
            FIRSTFALL_PY,
            str(mp4_file),
            "--fps", "24",
            "--ppm", "539.8",
            "--point", "282,117",
            "--qc", str(qc_file)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        try:
            res = json.loads(proc.stdout)
            with open(res_file, "w") as f:
                json.dump(res, f, indent=2)
            log(f"Measured {name}: flag={res.get('flag')} fall_px={res.get('fall_px')} fall_time={res.get('fall_time_s')}")
        except Exception as e:
            log(f"Error parsing firstfall output for {name}: {e}\nstdout: {proc.stdout}\nstderr: {proc.stderr}")

    if not sheet_file.exists() and mp4_file.exists():
        make_contact_sheet(mp4_file, sheet_file)

def main():
    log("Starting PhaseLock inference step sweep...")
    with open(JOBS_FILE) as f:
        jobs = [json.loads(line) for line in f if line.strip()]

    for job in jobs:
        run_job(job)

    # Summarize all results
    log("Compiling final summary...")
    summary = []
    for job in jobs:
        name = job["name"]
        res_file = OUT_DIR / f"{name}_firstfall.json"
        entry = {
            "name": name,
            "steps": job["steps"],
            "guidance": job["guidance"],
            "seed": job["seed"],
            "flag": "pending",
            "fall_px": None,
            "fall_m": None,
            "fall_time_s": None,
            "g": None
        }
        if res_file.exists():
            try:
                r = json.load(open(res_file))
                entry.update({
                    "flag": r.get("flag"),
                    "fall_px": r.get("fall_px"),
                    "fall_m": r.get("fall_m"),
                    "fall_time_s": r.get("fall_time_s"),
                    "g": r.get("g")
                })
            except Exception:
                pass
        summary.append(entry)

    with open(WORK_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    log("Sweep complete!")
    for s in summary:
        log(f"  {s['name']:25s} | steps={s['steps']:2d} cfg={s['guidance']:3.1f} s={s['seed']} | flag={s['flag']:12s} fall_px={s['fall_px']}")

if __name__ == "__main__":
    main()
