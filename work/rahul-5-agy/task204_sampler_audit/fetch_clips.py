#!/usr/bin/env python3
"""Fetch the 12 task-204 clips from the queue server."""
import json
import urllib.request
import hashlib
from pathlib import Path

QUEUE_URL = "http://100.111.167.68:8030"
OUT_DIR = Path("/home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/clips")

JOBS = [
    ("123736-20f70e", "ms_pend10_midB_nv_s1"),
    ("123736-d64f90", "ms_pend10_midB_nv_s2"),
    ("123737-248add", "ms_pend10_midB_nv_s3"),
    ("123738-3780c1", "ms_pend11_midB_nv_s1"),
    ("123738-65901c", "ms_pend11_midB_nv_s2"),
    ("123738-2d2a4f", "ms_pend11_midB_nv_s3"),
    ("123739-71fd88", "ms_pend10_midB_kar_s1"),
    ("123739-0799f4", "ms_pend10_midB_kar_s2"),
    ("123740-19b9a9", "ms_pend10_midB_kar_s3"),
    ("123740-88a457", "ms_pend11_midB_kar_s1"),
    ("123741-86dfc5", "ms_pend11_midB_kar_s2"),
    ("123741-7a1b02", "ms_pend11_midB_kar_s3"),
]

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for qid, name in JOBS:
        mp4_path = OUT_DIR / f"{name}.mp4"
        json_path = OUT_DIR / f"{name}.json"
        
        # Download metadata
        meta_url = f"{QUEUE_URL}/jobs/{qid}"
        print(f"Fetching metadata for {name} ({qid})...")
        with urllib.request.urlopen(meta_url) as r:
            meta = json.loads(r.read())
        with open(json_path, "w") as f:
            json.dump(meta, f, indent=2)
            
        # Download MP4
        mp4_url = f"{QUEUE_URL}/jobs/{qid}/mp4"
        print(f"Fetching video for {name} ({qid})...")
        with urllib.request.urlopen(mp4_url) as r:
            data = r.read()
        with open(mp4_path, "wb") as f:
            f.write(data)
            
        sha = hashlib.sha256(data).hexdigest()
        manifest[name] = {
            "queue_id": qid,
            "sha256": sha,
            "bytes": len(data),
            "endpoint": meta.get("endpoint"),
            "sampler": meta.get("params", {}).get("extra_params", {}).get("sampler")
        }
        print(f"  {name}: {len(data)} bytes, sha256={sha[:12]}...")

    with open(OUT_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print("Done! All 12 clips and sidecars downloaded.")

if __name__ == "__main__":
    main()
