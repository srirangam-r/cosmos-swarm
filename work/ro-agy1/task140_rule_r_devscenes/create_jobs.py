import json, os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUTS_DIR = BASE_DIR / "inputs"

RULE_R = " By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy and come to rest, staying completely still for the rest of the video."
CONTROL_N = " The camera stays fixed and the lighting remains constant and even throughout the whole video."

scenes = {
    "slope_wood": {
        "image": str(INPUTS_DIR / "frame(wood).png"),
        "prompt": "Static frontal camera view: A 90g wood cube sits near the upper end of a 477g fixed wooden plank. The steep incline of the blank is 30 degree. A linear ruler and digital protractor are placed beside the assembly, all resting on a black perforated optical table. Coefficient of friction between wood and wood is 0.27; coefficient of restitution for the cube is 0.22. Upon release, the cube slides down the inclined surface, and finally lands on the table surface. The wooden plank remains fully stationary for the entire duration of the motion. Maintain structural integrity and object consistency throughout: no changing shapes, no blending, and no flashing background."
    },
    "slope_plastic": {
        "image": str(INPUTS_DIR / "frame(plastic).png"),
        "prompt": "Static frontal camera view: A 147g black plastic cube sits near the upper end of a 477g fixed wooden plank. The steep incline of the blank is 30 degree. A linear ruler and digital protractor are placed beside the assembly, all resting on a black perforated optical table. Coefficient of friction between plastic and wood is 0.28; coefficient of restitution for the cube is 0.32. Upon release, the cube slides down the inclined surface, and finally lands on the table surface. The wooden plank remains fully stationary for the entire duration of the motion. Maintain structural integrity and object consistency throughout: no changing shapes, no blending, and no flashing background."
    },
    "pend_rest": {
        "image": str(INPUTS_DIR / "frame.png"),
        "prompt": "Static frontal camera view: A 318g black metal ball is fixed to the tip of a lightweight rigid rod, which rotates freely about a stationary horizontal axle mounted between two vertical posts atop a black perforated optical table. Initially, the rod angle is 10 degree, with the ball extending out to one side. Upon release, the ball follows pendulum motion: it accelerates downward past the black vertical posts, ascends on the opposite side, and continues oscillating back and forth over numerous cycles, its amplitude slowly and gradually diminishing due to friction. Maintain structural integrity and object consistency throughout: no changing shapes, no blending, and no flashing background."
    },
    "pend_mid": {
        "image": str(INPUTS_DIR / "pend10_mid_f93.png"),
        "prompt": "Static frontal camera view: A 318g black metal ball is fixed to the tip of a lightweight rigid rod, which rotates freely about a stationary horizontal axle mounted between two vertical posts atop a black perforated optical table. Initially, the rod angle is 10 degree, with the ball extending out to one side. Upon release, the ball follows pendulum motion: it accelerates downward past the black vertical posts, ascends on the opposite side, and continues oscillating back and forth over numerous cycles, its amplitude slowly and gradually diminishing due to friction. Maintain structural integrity and object consistency throughout: no changing shapes, no blending, and no flashing background."
    }
}

arms = {
    "base": lambda p: p,
    "r": lambda p: p + RULE_R,
    "n": lambda p: p + CONTROL_N
}

jobs = []
for scene_name, sinfo in scenes.items():
    assert os.path.exists(sinfo["image"]), f"Missing image: {sinfo['image']}"
    for arm_name, prompt_fn in arms.items():
        for seed in (1, 2, 3):
            job_name = f"t140_{scene_name}_{arm_name}_s{seed}"
            jobs.append({
                "name": job_name,
                "image": sinfo["image"],
                "prompt": prompt_fn(sinfo["prompt"]),
                "negative_prompt": None,
                "width": 832,
                "height": 480,
                "num_frames": 93,
                "fps": 24,
                "steps": 35,
                "guidance": 6.0,
                "flow_shift": 10.0,
                "seed": seed,
                "extra_params": {
                    "task": 140,
                    "scene": scene_name,
                    "arm": arm_name,
                    "seed": seed,
                    "rule_r": bool(arm_name == "r"),
                    "control_n": bool(arm_name == "n")
                }
            })

out_jsonl = BASE_DIR / "jobs.jsonl"
with open(out_jsonl, "w") as f:
    for j in jobs:
        f.write(json.dumps(j) + "\n")

print(f"Generated {len(jobs)} jobs in {out_jsonl}")
