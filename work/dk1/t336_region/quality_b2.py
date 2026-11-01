#!/usr/bin/env python3
"""Task 336b quality readout, Amendment 2 (written 21:05 UTC 2026-11-01, BEFORE any t336b clip exists).
Why: dk2 #6951 showed score.py's DOVER draws depend on batch position (per-draw fused SD ~0.008), so a 3-rep
paired delta vs t319's stored scores carries ~±0.007 of sampling noise and my "-0.008 rig drift" was not an offset.
Change: arms AND refs (t276 plain/nphys, same 4 scenes, seeds 1-3, sha-matched to t319) are scored on the same
4060 with `score.py --per_clip_seed --dover_reps 10` (db5698e). Same statistics, same decision rule
(Delta_fused vs plain >= -0.020) as quality_b.py; only the baseline file changes. This is the PRIMARY quality
readout from now on; quality_b.py (3-rep vs t319) is reported alongside as the original frozen readout.
usage: python3 quality_b2.py <t336b scores pcs10.json> <refs scores pcs10.json> <out.json>
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import quality_b

if __name__ == "__main__":
    quality_b.BASE = json.load(open(sys.argv[2]))
    sys.argv = [sys.argv[0], sys.argv[1], sys.argv[3]]
    quality_b.main()
