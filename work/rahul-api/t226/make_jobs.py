"""Task 226 job builder: where does text control of motion end? (rahul-api)
3 real GAUGE first frames x 4 prompt arms (EVENT slot swapped) x 6 seeds, noise.device=cpu, a6k only."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
INTEG = ("Maintain structural integrity and object consistency throughout: no changing shapes, no blending, "
         "and no flashing background.")
SCENE_P = ("Static frontal camera view: A 318g black metal ball is fixed to the tip of a lightweight rigid rod, which "
           "rotates freely about a stationary horizontal axle mounted between two vertical posts atop a black perforated "
           "optical table. Initially, the rod angle is 10 degree, with the ball extending out to one side.")
SCENE_B = ("Static frontal camera view: A 121g black ball is suspended high above a wooden plank, which is fixed on a "
           "black perforated optical table. Coefficient of friction is 0.81; coefficient of restitution is 0.58.")
EV = {
  # pendulum EVENT slot (base = t193/k185 GAUGE sentence verbatim)
  "P_base": ("Upon release, the ball follows pendulum motion: it accelerates downward past the black vertical posts, "
             "ascends on the opposite side, and continues oscillating back and forth over numerous cycles, its amplitude "
             "slowly and gradually diminishing due to friction."),
  "P_neutral": ("The scene is lit by soft, even overhead light: the metal surfaces show faint gray reflections, the "
                "posts have a matte black finish, and the regular grid of small holes in the table is sharp and clearly "
                "visible."),
  "P_still": ("The pendulum is locked in place: the rod and the ball stay completely still at this exact angle for the "
              "entire video, never swinging, never rotating and never moving at all, like a photograph of a stopped "
              "pendulum."),
  "P_fast": ("Upon release, the ball swings extremely fast: it whips rapidly downward past the black vertical posts and "
             "back again, completing about three full quick oscillations every single second, with no slowing at all "
             "over the whole video."),
  # ball EVENT slot (base = GAUGE ball-1 sentence verbatim); same counter sentences for mid-fall and held frames
  "B_base": ("When released, the ball undergoes free fall, followed by a sequence of successive bounces with "
             "diminishing peak heights, before finally coming to rest on the plank."),
  "B_neutral": ("The lighting is soft and even: the black ball has a faint gray highlight, the plank shows warm wood "
                "grain, and the table holes are sharply visible."),
  "B_up": ("The ball shoots straight upward: it rises quickly toward the top of the frame and flies out of view above, "
           "never falling down to the plank."),
  "B_still": ("The ball stays exactly where it is: it hangs motionless in the air for the entire video, never falling, "
              "never bouncing and never touching the plank."),
}
SCENES = {  # scene id: (input image, scene sentence, event prefix, arms)
  "P": ("inp_pend10_mid_f93.png", SCENE_P, "P", ["base", "neutral", "still", "fast"]),
  "F": ("inp_ball1_midfall_dd33.png", SCENE_B, "B", ["base", "neutral", "up", "still"]),
  "H": ("inp_ball1_f0_held.png", SCENE_B, "B", ["base", "neutral", "up", "still"]),
}
SEEDS = [101, 102, 103, 104, 105, 106]
ENDPOINTS = "a6k-0,a6k-1,a6k-2,a6k-3"

def prompt(scene, arm):
    img, sc, pre, arms = SCENES[scene]
    return f"{sc} {EV[pre + '_' + arm]} {INTEG}"

def jobs():
    out = []
    for seed in SEEDS:
        for scene, (img, sc, pre, arms) in SCENES.items():
            for arm in arms:
                out.append({"name": f"t226_{scene}_{arm}_s{seed}", "image": os.path.join(HERE, img),
                            "prompt": prompt(scene, arm), "negative_prompt": None, "width": 832, "height": 480,
                            "num_frames": 93, "fps": 24, "steps": 35, "guidance": 6.0, "flow_shift": 10.0,
                            "seed": seed,
                            "extra_params": {"noise": {"device": "cpu"}, "task": "t226 rahul-api",
                                             "scene": scene, "arm": arm, "seed": seed}})
    return out

if __name__ == "__main__":
    js = jobs()
    with open(os.path.join(HERE, "jobs.jsonl"), "w") as f:
        for j in js:
            f.write(json.dumps(j) + "\n")
    for k, v in EV.items():
        print(f"{k:10s} words={len(v.split()):3d} chars={len(v)}")
    print(len(js), "jobs")
