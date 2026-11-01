import json, random, secrets
pre = "Static frontal camera view: A 121g black ball is suspended high above a wooden plank, which is fixed on a black perforated optical table. Coefficient of friction is 0.81; coefficient of restitution is 0.58. When released, the ball undergoes free fall, "
post = " Maintain structural integrity and object consistency throughout: no changing shapes, no blending, and no flashing background."
arms = {"F": "followed by a sequence of successive bounces with diminishing peak heights, before finally coming to rest on the plank.",
        "QT": "bounces only twice with rapidly diminishing heights, and comes to rest on the plank within about one and a half seconds, staying still for the rest of the video."}
jobs, key = [], {}
for img in ["gauge_ball1_dd35_832x480.png", "gauge_ball2_dd33_832x480.png"]:
    for seed in (21, 22, 23):
        for arm, mid in arms.items():
            n = "r60_" + secrets.token_hex(3)
            key[n] = {"arm": arm, "image": img, "seed": seed}
            jobs.append({"name": n, "image": img, "prompt": pre + mid + post, "negative_prompt": None, "width": 832, "height": 480,
                         "num_frames": 93, "fps": 24, "steps": 35, "guidance": 6.0, "flow_shift": 10.0, "seed": seed,
                         "extra_params": {"client": "rog1"}})
random.shuffle(jobs)
open("jobs.jsonl", "w").write("".join(json.dumps(j) + "\n" for j in jobs))
json.dump(key, open("KEY_DO_NOT_OPEN_UNTIL_CODED.json", "w"), indent=1)
print(len(jobs))
