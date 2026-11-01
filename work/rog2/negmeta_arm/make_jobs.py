"""Build the negmeta 2x2 jobs so they run on ANY existing cosmos_local / vLLM-Omni-style server (no restart needed).
SAME arms: templates off (use_duration_template/use_resolution_template=False) and the metadata sentences appended to
BOTH prompt and negative client-side, with diffusers' own _append rule (rstrip('.') + '. ' + add). INVERSE arms: server
defaults (templates on). verify() checks the emulated texts equal what diffusers @86ef420b builds via neg_meta 'same'."""
import json, sys
from pathlib import Path
HERE = Path(__file__).parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools/cosmos_local"))
import neg_meta

DUR = "The video is {duration:.1f} seconds long and is of {fps:.0f} FPS."
RES = "This video is of {height}x{width} resolution."
NF, FPS, W, H = 93, 24, 832, 480


def app(base, add):
    base = base.rstrip(".")
    return f"{base}. {add}" if base else add


def meta(text):
    return app(app(text, DUR.format(duration=NF / FPS, fps=FPS)), RES.format(height=H, width=W))


def main():
    src = [json.loads(l) for l in open(ROOT / "tools/cosmos_local/example_jobs_gauge_ball.jsonl")]
    P = src[0]["prompt"]
    nv = neg_meta.nvidia_default_negative()
    arms = [("inv_empty", "inverse", None), ("same_nvneg", "same", nv), ("same_empty", "same", ""), ("inv_nvneg", "inverse", nv)]
    with open(HERE / "jobs_negmeta_ball93.jsonl", "w") as out:
        for arm, mode, neg in arms:
            for seed in (1, 2):
                for b in (1, 2):
                    j = dict(name=f"negmeta_{arm}_ball{b}_s{seed}", image=f"work/raj-2/task9_duration/gauge_ball{b}_f0_832x480.png",
                             width=W, height=H, num_frames=NF, fps=FPS, steps=35, guidance=6.0, flow_shift=10.0, seed=seed,
                             arm=arm, negative_metadata_mode=mode, negative_kind=("nvidia_default" if neg else "empty"))
                    if mode == "same":
                        j.update(prompt=meta(P), negative_prompt=meta(neg),
                                 extra_params={"client": "rog2-negmeta", "use_duration_template": False, "use_resolution_template": False})
                    else:
                        j.update(prompt=P, negative_prompt=(neg or None), extra_params={"client": "rog2-negmeta"})
                    out.write(json.dumps(j) + "\n")
    print("wrote 16 jobs")


if __name__ == "__main__":
    main()
