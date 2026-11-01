"""Program N job files (owner raj-noise). All use CPU-drawn noise so a seed is the same noise on every GPU type."""
import json, os
D = os.path.dirname(os.path.abspath(__file__)); I = f"{D}/inputs"
txt = lambda n: open(f"{I}/{n}.txt").read().strip()
F, R, N, QT, PB = txt("ball_F"), txt("ball_R"), txt("ball_N"), txt("ball_QT"), txt("pend_base")
R_SENT = "By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy and come to rest, staying completely still for the rest of the video."
N_SENT = "The scene is lit by soft, even lighting that stays constant throughout the video, and the colours remain natural and true to life, with realistic textures and fine surface detail on every object."
T_SENT = "Each full back-and-forth swing takes about 1.2 seconds, so the pendulum completes many swings during the video."
BASE = dict(width=832, height=480, num_frames=93, fps=24, steps=35, guidance=6.0, flow_shift=10.0)

def job(name, prompt, seed, image=None, noise=None, **meta):
    j = dict(BASE, name=name, prompt=prompt, seed=seed,
             extra_params={"client": "raj-noise", "noise": noise or {"device": "cpu"}, "prog": "N", **meta})
    if image: j["image"] = f"{I}/{image}"
    return j

def write(fname, jobs):
    with open(f"{D}/jobs/{fname}", "w") as f:
        for j in jobs: f.write(json.dumps(j) + "\n")
    print(fname, len(jobs))

# E0: does a seed carry across GPU types once the noise is drawn on the CPU?
for cls in ("q8", "l40s", "a6k"):
    js = [job(f"N_E0_{cls}_cpu_s{s}", F, s, "ball1_dd33.png", exp="E0", cls=cls) for s in range(101, 109)]
    if cls in ("q8", "l40s"):
        js += [job(f"N_E0_{cls}_cuda_s{s}", F, s, "ball1_dd33.png", noise={"device": "cuda"}, exp="E0", cls=cls) for s in range(101, 105)]
    if not (os.environ.get("E3") or os.environ.get("E5")): write(f"E0_{cls}.jsonl", js)

# E4: which part of the noise carries the motion? A = seed s, B = seed s+100; one part of the noise from B.
BOX = [0.28, 0.25, 0.44, 0.85]  # the ball's fall path in ball1_dd33
arms = {"A": None, "B": {"band": "all"},
        "tlo": {"band": "temporal_low", "cut": 0.25}, "thi": {"band": "temporal_high", "cut": 0.25},
        "slo": {"band": "spatial_low", "cut": 0.25}, "shi": {"band": "spatial_high", "cut": 0.25},
        "reg": {"band": "region", "box": BOX}}
e4 = []
for s in range(401, 413):
    for arm, mix in arms.items():
        nz = {"device": "cpu"} | ({"mix": dict(mix, seed=s + 100)} if mix else {})
        e4.append(job(f"N_E4_{arm}_s{s}", F, s, "ball1_dd33.png", noise=nz, exp="E4", arm=arm))
if not (os.environ.get("E3") or os.environ.get("E5")): write("E4.jsonl", e4)

# E1: text vs motion in T2V. Colour words should set the bob's colour; do speed words set the period, or the seed?
T2V = ("Static camera view: a simple pendulum, a thin rigid rod with a {c} metal ball at its tip, hangs from a horizontal "
       "axle mounted between two vertical posts on a table, in front of a plain grey wall. The pendulum swings back and "
       "forth {v}, under gravity, for the whole video.")
COL = {"red": "bright red", "blue": "bright blue"}
SPD = {"slow": "slowly, each full back-and-forth swing taking about three seconds",
       "fast": "quickly, each full back-and-forth swing taking about half a second"}
if not (os.environ.get("E3") or os.environ.get("E5")): write("E1.jsonl", [job(f"N_E1_{c}_{v}_s{s}", T2V.format(c=COL[c], v=SPD[v]), s, exp="E1", color=c, speed=v)
                   for s in range(201, 217) for c in COL for v in SPD])

# E2: fresh-seed variance split on real frames: seed vs prompt vs input.
cells = {("ball", "F"): ("ball1_dd33.png", F), ("ball", "R"): ("ball1_dd33.png", R), ("ball", "N"): ("ball1_dd33.png", N),
         ("ball", "QT"): ("ball1_dd33.png", QT),
         ("held", "F"): ("ball1_O.png", F), ("held", "R"): ("ball1_O.png", R), ("held", "N"): ("ball1_O.png", N),
         ("held", "QT"): ("ball1_O.png", QT),
         ("pend", "F"): ("pend10_mid_f93.png", PB), ("pend", "R"): ("pend10_mid_f93.png", PB + " " + R_SENT),
         ("pend", "N"): ("pend10_mid_f93.png", PB + " " + N_SENT), ("pend", "QT"): ("pend10_mid_f93.png", PB + " " + T_SENT)}
if not (os.environ.get("E3") or os.environ.get("E5")): write("E2.jsonl", [job(f"N_E2_{inp}_{p}_s{s}", prompt, s, img, exp="E2", input=inp, arm=p)
                   for s in range(301, 317) for (inp, p), (img, prompt) in cells.items()])

# E3: pendulum seed bank. Does a seed's period carry across three different real pendulum frames?
if __name__ == "__main__" and os.environ.get("E3"):
    e3 = [job(f"N_E3_{fr.split('_')[0]}_s{s}", PB, s, fr, exp="E3", frame=fr)
          for s in range(601, 625) for fr in ("pend10_mid_f93.png", "pend11_mid_f81.png", "pend14_mid_f81.png")]
    write("E3_part0.jsonl", e3[:36]); write("E3_part1.jsonl", e3[36:])

# E5: does the band result hold on other scenes? Held ball (ball1_O) and pendulum (pend10_mid_f93), 8 pairs each.
if __name__ == "__main__" and os.environ.get("E5"):
    arms5 = {k: v for k, v in arms.items() if k != "reg"}
    e5 = []
    for inp, img, pr in (("held", "ball1_O.png", F), ("pend", "pend10_mid_f93.png", PB)):
        for s in range(701, 709):
            for arm, mix in arms5.items():
                nz = {"device": "cpu"} | ({"mix": dict(mix, seed=s + 100)} if mix else {})
                e5.append(job(f"N_E5_{inp}_{arm}_s{s}", pr, s, img, noise=nz, exp="E5", input=inp, arm=arm))
    write("E5_part0.jsonl", e5[:48]); write("E5_part1.jsonl", e5[48:])
