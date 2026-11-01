#!/usr/bin/env python3
"""Blind Pack Generator for Swarm Tasks 225 & 226.
Randomizes clip filenames to opaque IDs ('blind_001.mp4', ...),
interleaves known-answer planted controls,
creates a blank coding sheet, and pre-commits to the SHA256 of KEY_DO_NOT_OPEN.json.
"""
import argparse, glob, hashlib, json, os, random, shutil
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Create blinded coding pack with planted controls")
    parser.add_argument("--candidate_clips_dir", required=True, help="Directory containing candidate generated clips")
    parser.add_argument("--planted_clips_dir", default=None, help="Directory containing known-answer planted clips")
    parser.add_argument("--planted_labels_json", default=None, help="JSON file mapping planted clip filenames to ground truth outcome")
    parser.add_argument("--out_dir", required=True, help="Output directory for blinded pack")
    parser.add_argument("--seed", type=int, default=20261101, help="Random seed for shuffling")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    clips_out = os.path.join(args.out_dir, "blinded_clips")
    os.makedirs(clips_out, exist_ok=True)

    rng = random.Random(args.seed)

    records = []
    # 1. Candidate clips
    cand_files = sorted(glob.glob(os.path.join(args.candidate_clips_dir, "*.mp4")))
    for p in cand_files:
        fn = os.path.basename(p)
        records.append({
            "orig_filename": fn,
            "orig_path": p,
            "is_planted": False,
            "ground_truth": None
        })

    # 2. Planted clips
    if args.planted_clips_dir and args.planted_labels_json:
        with open(args.planted_labels_json, "r") as f:
            planted_map = json.load(f)
        planted_files = sorted(glob.glob(os.path.join(args.planted_clips_dir, "*.mp4")))
        for p in planted_files:
            fn = os.path.basename(p)
            if fn in planted_map:
                records.append({
                    "orig_filename": fn,
                    "orig_path": p,
                    "is_planted": True,
                    "ground_truth": planted_map[fn]
                })

    rng.shuffle(records)

    key_data = {}
    sheet_rows = []

    for idx, rec in enumerate(records):
        blind_id = f"blind_{idx+1:04d}"
        target_mp4 = os.path.join(clips_out, f"{blind_id}.mp4")
        shutil.copyfile(rec["orig_path"], target_mp4)

        key_data[blind_id] = {
            "orig_filename": rec["orig_filename"],
            "is_planted": rec["is_planted"],
            "ground_truth": rec["ground_truth"]
        }

        sheet_rows.append({
            "blind_id": blind_id,
            "outcome": "",
            "rest_frame": "",
            "ball_size_end_px": "",
            "notes": ""
        })

    # Save key
    key_path = os.path.join(args.out_dir, "KEY_DO_NOT_OPEN.json")
    with open(key_path, "w") as f:
        json.dump(key_data, f, indent=2)

    # Compute key SHA256
    with open(key_path, "rb") as f:
        key_sha = hashlib.sha256(f.read()).hexdigest()

    with open(os.path.join(args.out_dir, "KEY_SHA256.txt"), "w") as f:
        f.write(f"{key_sha}  KEY_DO_NOT_OPEN.json\n")

    # Save blank coding sheet
    sheet_df = pd.DataFrame(sheet_rows)
    sheet_path = os.path.join(args.out_dir, "coding_sheet_blank.csv")
    sheet_df.to_csv(sheet_path, index=False)

    print(f"Blinded pack staged at: {args.out_dir}")
    print(f"Total blinded clips: {len(records)} (Candidates: {len(cand_files)}, Planted: {len(records)-len(cand_files)})")
    print(f"KEY_DO_NOT_OPEN.json SHA256: {key_sha}")
    print(f"Blank sheet: {sheet_path}")

if __name__ == "__main__":
    main()
