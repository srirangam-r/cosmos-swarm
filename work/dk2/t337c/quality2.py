#!/usr/bin/env python3
"""Task 337c quality readout, Amendment 1 (written 21:10 UTC 2026-11-01, BEFORE any t337c clip exists).
Mirrors dk1 work/dk1/t336_region/quality_b2.py @04b80a5 (t336b Amendment 2).
Why: score.py's DOVER draws depended on batch position (#6951), so 3-rep deltas vs t319's stored scores carry ~±0.007 noise.
Change: arms AND refs (t276 plain/nphys/nphys_x17, real_12/17/18/19 [+real_09 for arm B], seeds 1-3, the t319/gen clips)
are scored on dk2's RTX 4060 rig (t319/venv_gpu, t319/ext/DOVER) with `score.py --per_clip_seed --dover_reps 10` (db5698e).
Same statistics and decision rule (Delta_fused vs plain >= -0.020) as quality.py; only the baseline file changes.
PRIMARY quality readout from now on; quality.py (vs t319 3-rep) is reported alongside.
usage: python3 quality2.py <t337c scores pcs10.json> <refs scores pcs10.json> <out.json>
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import quality

if __name__ == "__main__":
    quality.BASE = json.load(open(sys.argv[2]))
    sys.argv = [sys.argv[0], sys.argv[1], sys.argv[3]]
    quality.main()
