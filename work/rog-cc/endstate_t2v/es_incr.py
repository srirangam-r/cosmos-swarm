#!/usr/bin/env python3
"""Task 133 incremental runner (replaces run.sh, same tools, flags and analysis; PREREG unchanged).
run.sh judged only after all 144 clips arrived. This fetches every 60 s and judges/scores each new clip as it lands:
  HUE judge (hue_judge.py, offsets 0,0.5) -> endstate/res/parts/<arm>_<ts>.json, merged into res/<arm>.json(+.done) at 48 clips
  DOVER(reps 1)+DD (score.py)             -> endstate/res_nv/<arm>.json (score.py accumulates), .done at 48 clips
  analyze_es.py once base+R are done (hue+nv), and again when N is done.
Arm priority base, R, then N. It also keeps fetching the rep3082 clips (r3082_*) and runs
rep3082/analyze_rep3082.py metrics once all 40 are present (blind strips; eye-coding is manual).
Deadline: after DEADLINE_MIN, arms are closed with whatever clips are judged (analyzer keeps prompts with all 3 seeds)."""
import os, sys, json, glob, time, subprocess, re

W = "/home/nail/other_work/sclaw/swarm-work/rog-cc"
ES = W + "/endstate"; REPO = W + "/cosmos-swarm"
Q = "/home/nail/other_work/sclaw/agentic_colab/scripts/cosmos_queue.py"
JUDGE = REPO + "/tools/hue_judge/hue_judge.py"; QS = W + "/../rog1/data/hue/hue-v1p2-t2v-public.json"
NVS = REPO + "/tools/nv_scoreboard/score.py"; DOVER = W + "/ext/DOVER"; LOCK = "/tmp/rogcc_gpu.lock"
ANA = REPO + "/work/rog-cc/endstate_t2v/analyze_es.py"; REP = REPO + "/work/rog-cc/rep3082/analyze_rep3082.py"
ARMS = ["base", "R", "N"]; NEED = 48; NREP = 40
DEADLINE_MIN = float(sys.argv[1]) if len(sys.argv) > 1 else 150
END = time.time() + DEADLINE_MIN * 60
os.makedirs(ES + "/res/parts", exist_ok=True); os.makedirs(ES + "/res_nv", exist_ok=True)


def log(*a):
    print(time.strftime("%H:%M:%S", time.gmtime()), *a, flush=True)


def clips(arm):
    return sorted(glob.glob(f"{ES}/clips/es_{arm}_*.mp4"))


def judged(arm):
    offs = {}
    for p in glob.glob(f"{ES}/res/parts/{arm}_*.json"):
        try:
            R = json.load(open(p))["results"]
        except Exception:
            continue
        for r in R:
            offs.setdefault(r["clip"], set()).add(r["offset"])
    return {c for c, o in offs.items() if len(o) >= 2}


def scored(arm):
    p = f"{ES}/res_nv/{arm}.json"
    try:
        return set(json.load(open(p)).keys()) if os.path.exists(p) else set()
    except Exception:
        return set()


def sample_of(c):
    s = os.path.basename(c)[:-4]
    s = re.sub(r"^es_[A-Za-z]+_", "", s)
    return re.sub(r"_s\d+$", "", s)


def judge(arm, new):
    out = f"{ES}/res/parts/{arm}_{time.strftime('%H%M%S', time.gmtime())}.json"
    args = []
    for c in new:
        args += ["--clip", c, "--sample", sample_of(c)]
    log(f"judge {arm} {len(new)} clips -> {os.path.basename(out)}")
    with open(f"{ES}/judge_{arm}.log", "a") as lf:
        rc = subprocess.run(["flock", LOCK, "python3", JUDGE, "--questions", QS, "--offsets", "0,0.5", "--out", out] + args,
                            stdout=lf, stderr=lf).returncode
    log(f"judge {arm} rc={rc}")


def nv(arm, new):
    log(f"nv {arm} {len(new)} clips")
    with open(f"{ES}/nv_{arm}.log", "a") as lf:
        rc = subprocess.run(["flock", LOCK, "python3", NVS] + new + ["--dover_dir", DOVER, "--device", "cuda", "--dover_reps", "1",
                            "--out", f"{ES}/res_nv/{arm}.json"], stdout=lf, stderr=lf).returncode
    log(f"nv {arm} rc={rc}")


def merge(arm):
    seen = set(); res = []; meta = None
    for p in sorted(glob.glob(f"{ES}/res/parts/{arm}_*.json")):
        d = json.load(open(p)); meta = meta or d["meta"]
        for r in d["results"]:
            k = (r["clip"], r["offset"])
            if k not in seen:
                seen.add(k); res.append(r)
    json.dump({"meta": meta, "results": res}, open(f"{ES}/res/{arm}.json", "w"), indent=1)
    open(f"{ES}/res/{arm}.json.done", "w").write(time.strftime("%FT%T", time.gmtime()))
    log(f"merged {arm}: {len({r['clip'] for r in res})} clips")


def done(kind, arm):
    return os.path.exists(f"{ES}/{'res' if kind == 'hue' else 'res_nv'}/{arm}.json.done")


def analyze(tag):
    rc = subprocess.run(["python3", ANA, ES, "--out", ES + "/summary.json"], stdout=subprocess.DEVNULL,
                        stderr=open(ES + "/summary.txt", "w")).returncode
    log(f"analyze[{tag}] rc={rc}")


analyzed = set(); rep_done = os.path.exists(W + "/rep3082/out/metrics.json")
while True:
    with open(ES + "/fetch.log", "a") as fl:
        subprocess.run(["timeout", "600", "python3", Q, "fetch", "--owner", "rog-cc", "--out", ES + "/clips"], stdout=fl, stderr=fl)
    late = time.time() > END
    n_es = sum(len(clips(a)) for a in ARMS); n_rep = len(glob.glob(ES + "/clips/r3082_*.mp4"))
    log(f"fetched es {n_es}/144 r3082 {n_rep}/{NREP}")
    worked = False
    for a in ARMS:
        if done("hue", a) and done("nv", a):
            continue
        C = clips(a)
        new = [c for c in C if c not in judged(a)]
        if new:
            judge(a, new); worked = True
        new = [c for c in C if os.path.basename(c) not in scored(a)]
        if new:
            nv(a, new); worked = True
        if not done("hue", a) and (len(judged(a)) >= NEED or (late and not new)):
            merge(a)
        if not done("nv", a) and (len(scored(a)) >= NEED or (late and not new)):
            open(f"{ES}/res_nv/{a}.json.done", "w").write(time.strftime("%FT%T", time.gmtime())); log(f"nv {a} done")
        if a in ("base", "R") and worked:
            break  # re-fetch before moving to lower-priority arms
    if "BR" not in analyzed and all(done(k, a) for k in ("hue", "nv") for a in ("base", "R")):
        analyze("base+R"); analyzed.add("BR")
    if "ALL" not in analyzed and all(done(k, a) for k in ("hue", "nv") for a in ARMS):
        analyze("all"); analyzed.add("ALL")
    if not rep_done and (n_rep >= NREP or (late and n_rep > 0 and "ALL" in analyzed)):
        rc = subprocess.run(["python3", REP, "metrics", ES + "/clips", W + "/rep3082/out"],
                            stdout=open(W + "/rep3082/metrics.log", "w"), stderr=subprocess.STDOUT).returncode
        log(f"rep3082 metrics n={n_rep} rc={rc}"); rep_done = True
    if "ALL" in analyzed and rep_done:
        log("DONE"); break
    if time.time() > END + 60 * 60:
        log("hard deadline, exiting"); break
    if not worked:
        time.sleep(60)
