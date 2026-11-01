#!/usr/bin/env python3
import glob, os, sys, json, subprocess
from concurrent.futures import ProcessPoolExecutor

CLIPS = sorted(glob.glob("/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/ro-agy1/task140_rule_r_devscenes/clips/t140_*.mp4"))
OUT_DIR = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/ro-agy1/task140_rule_r_devscenes/nv_shards"
FINAL_OUT = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/ro-agy1/task140_rule_r_devscenes/nv_scores.json"
os.makedirs(OUT_DIR, exist_ok=True)

PYTHON = "/home/rohith/swarm-work/ro-1/py312/bin/python3"
SCORE_PY = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/tools/nv_scoreboard/score.py"
DOVER_DIR = "/home/rohith/swarm-work/ro-1/scoreboard/DOVER"

def score_clip(clip_path):
    base = os.path.basename(clip_path)
    shard_out = os.path.join(OUT_DIR, f"{base}.json")
    if os.path.exists(shard_out):
        try:
            with open(shard_out) as f:
                d = json.load(f)
                if base in d:
                    print(f"Already done: {base}")
                    return shard_out
        except Exception:
            pass
    cmd = [
        PYTHON, SCORE_PY, clip_path,
        "--dover_dir", DOVER_DIR,
        "--device", "cpu",
        "--out", shard_out
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error scoring {base}: {res.stderr}")
        return None
    print(f"Scored {base}")
    return shard_out

def main():
    print(f"Total clips to score: {len(CLIPS)}")
    # Run 8 concurrent workers
    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(score_clip, CLIPS))
    
    # Merge shards
    merged = {}
    for shard in glob.glob(os.path.join(OUT_DIR, "*.mp4.json")):
        with open(shard) as f:
            d = json.load(f)
            merged.update(d)
    
    with open(FINAL_OUT, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"Successfully wrote {len(merged)} clips to {FINAL_OUT}")

if __name__ == "__main__":
    main()
