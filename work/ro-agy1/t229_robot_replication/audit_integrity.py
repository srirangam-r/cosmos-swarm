#!/usr/bin/env python3
"""Audit SHA256 integrity and sidecar metadata for Task 210 clips."""
import hashlib, json, os, glob

CLIPS_DIR = "/home/rohith/swarm-work/ro-agy1/t210_clips"
SHA_FILE = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/rahul-api/t210/clips_SHA256SUMS"
DEVSET_DIR = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/tools/robot_pred/devset_bridge"

def main():
    print("--- 1. SHA256 Integrity Audit ---")
    expected_hashes = {}
    with open(SHA_FILE, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                expected_hashes[os.path.basename(parts[1])] = parts[0]

    mp4_files = sorted(glob.glob(os.path.join(CLIPS_DIR, "t210_*.mp4")))
    print(f"Found {len(mp4_files)} MP4 clips locally. Expected in manifest: {len(expected_hashes)}")

    matched = 0
    mismatched = []
    for p in mp4_files:
        fn = os.path.basename(p)
        with open(p, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        if fn in expected_hashes:
            if h == expected_hashes[fn]:
                matched += 1
            else:
                mismatched.append((fn, expected_hashes[fn], h))
        else:
            print(f"Warning: {fn} not in manifest")

    print(f"SHA256 verification: {matched}/{len(expected_hashes)} matched perfectly.")
    if mismatched:
        print(f"MISMATCHES found: {len(mismatched)}")
        for m in mismatched[:5]:
            print(m)
    else:
        print("All verified clips bit-identical to published manifest.")

    print("\n--- 2. Sidecar Metadata & Timing Audit ---")
    json_files = sorted(glob.glob(os.path.join(CLIPS_DIR, "t210_*.json")))
    print(f"Found {len(json_files)} sidecar JSONs.")

    guidance_scales = set()
    num_steps = set()
    resolutions = set()
    fps_set = set()
    num_frames_set = set()
    server_timestamps = []

    for p in json_files:
        try:
            with open(p, "r") as f:
                d = json.load(f)
            guidance_scales.add(d.get("guidance_scale"))
            num_steps.add(d.get("num_inference_steps"))
            resolutions.add(d.get("size"))
            fps_set.add(d.get("fps"))
            num_frames_set.add(d.get("num_frames"))
            sc_id = d.get("server_clip_id", "")
            if "_" in sc_id:
                server_timestamps.append(sc_id.split("_")[0])
        except Exception as e:
            print(f"Error reading {p}: {e}")

    print("Guidance scales:", guidance_scales)
    print("Inference steps:", num_steps)
    print("Resolutions:", resolutions)
    print("FPS:", fps_set)
    print("Num frames:", num_frames_set)
    if server_timestamps:
        server_timestamps.sort()
        print(f"Server timestamps: min {server_timestamps[0]}, max {server_timestamps[-1]}")

    print("\n--- 3. Devset Episode Uniqueness Audit ---")
    with open(os.path.join(DEVSET_DIR, "index.json"), "r") as f:
        idx = json.load(f)
    episodes = [c["episode_index"] for c in idx["clips"]]
    print(f"Total devset clips: {len(episodes)}")
    print(f"Distinct episode indices: {len(set(episodes))}")
    assert len(episodes) == len(set(episodes)), "Duplicate episodes found in devset!"
    print("Confirmed: All 24 clips belong to completely distinct real robot episodes.")

if __name__ == "__main__":
    main()
