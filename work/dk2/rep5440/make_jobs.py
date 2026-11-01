"""Independent replication of finding #5440 (dk1, task 255 E2): fresh seeds 11-13, own code.
Arms per Bridge dev clip (24, chunk 0): OWN = clip's real chunk-0 actions; ZERO = physical stand-still
(translation 0, rot6d identity [1,0,0,0,1,0], gripper held at the clip's t0 normalised value), mapped
to model space with q01/q99 of tools/robot_pred/bridge_orig_lerobot_stats.json: 2(a-q01)/(q99-q01)-1.
Settings = model-card FD: 17 f @ 5 fps, 256^2, 30 steps, CFG 1; noise on CPU (charter rule 11).
Usage: python3 make_jobs.py <devset_dir> <stats.json> > jobs.jsonl
"""
import json, sys
from pathlib import Path

dev, stats = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())
lo, hi = stats["q01"], stats["q99"]
FALLBACK = "A robot arm performs a manipulation task on a tabletop."

def to_model_space(vec):
    return [2.0 * (v - l) / max(h - l, 1e-8) - 1.0 for v, l, h in zip(vec, lo, hi)]

for seed in (11, 12, 13):
    for c in json.loads((dev / "index.json").read_text())["clips"]:
        cid = c["id"]
        meta = json.loads((dev / cid / "action_chunks.json").read_text())
        own = meta["action_chunks"][0]
        still = to_model_space([0, 0, 0, 1, 0, 0, 0, 1, 0, 0])
        still[9] = own[0][9]
        for arm, act in (("own", own), ("zero", [list(still) for _ in own])):
            print(json.dumps({
                "name": f"rep5440_{cid}_{arm}_s{seed}", "prompt": meta["prompt"].strip() or FALLBACK,
                "image": str((dev / cid / "first_frame.png").resolve()),
                "width": 256, "height": 256, "num_frames": meta["action_chunk_size"] + 1, "fps": meta["fps"],
                "steps": 30, "guidance": 1.0, "flow_shift": 10.0, "seed": seed,
                "extra_params": {"action_mode": "forward_dynamics", "domain_name": meta["domain_name"],
                                 "action_chunk_size": meta["action_chunk_size"], "image_size": meta["image_size"],
                                 "view_point": meta["view_point"], "action": act, "guardrails": True,
                                 "noise": {"device": "cpu"}},
                "meta": {"clip": cid, "arm": arm, "seed": seed, "task": 255, "exp": "rep5440"}}))
