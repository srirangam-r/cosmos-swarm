#!/usr/bin/env python3
"""
Independent replication and review of Finding #4962 (Program N, E4 noise component decomposition).
Evaluates whether low-frequency temporal (29%) and spatial (6%) initial noise components
govern Cosmos3-Nano's generative trajectory and late motion across all 9 complete seed pairs.
"""
import glob, json, os, sys
import numpy as np, cv2

CLIPS_DIR = "/home/nail/swarm-work/agy-2/t249_e4_review/clips"
OUT_DIR = "/home/nail/swarm-work/agy-2/t249_e4_review"

def load_frames(path):
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if f.shape[:2] != (480, 832):
            f = cv2.resize(f, (832, 480))
        frames.append(f)
    cap.release()
    return frames

def to_gray_lowres(frames):
    gray_list = []
    for f in frames:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        # 1/8 scale: (832//8, 480//8) = (104, 60)
        g_small = cv2.resize(g, (104, 60), interpolation=cv2.INTER_AREA)
        g_blur = cv2.GaussianBlur(g_small, (3, 3), 0)
        gray_list.append(g_blur)
    return np.array(gray_list)

def extract_features(path):
    frames = load_frames(path)
    G = to_gray_lowres(frames)
    diff = np.abs(np.diff(G, axis=0))
    e = diff.mean(axis=(1, 2)) # 92 values
    lm = float(np.log(e[-24:].mean() + 0.05))
    return dict(G=G, e=e, LM=lm, n_frames=len(frames))

def mae(a, b):
    return float(np.abs(a - b).mean())

def corr(a, b):
    a = a - a.mean()
    b = b - b.mean()
    denom = np.sqrt((a * a).sum() * (b * b).sum()) + 1e-12
    return float((a * b).sum() / denom)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    all_mp4s = sorted(glob.glob(os.path.join(CLIPS_DIR, "N_E4_*.mp4")))
    print(f"Total E4 mp4s: {len(all_mp4s)}")

    # Load sidecars and check specs
    sidecars = {}
    for p in all_mp4s:
        name = os.path.basename(p)[:-4]
        json_p = p[:-4] + ".json"
        if os.path.exists(json_p):
            with open(json_p) as f:
                sidecars[name] = json.load(f)

    print(f"Loaded {len(sidecars)} sidecars.")

    # Extract features for all clips
    feat_map = {}
    for p in all_mp4s:
        name = os.path.basename(p)[:-4]
        print(f"Extracting features for {name}...")
        feat_map[name] = extract_features(p)

    # Identify complete seed sets
    seeds = [401, 402, 403, 404, 408, 409, 410, 411, 412]
    arms = ["tlo", "thi", "slo", "shi", "reg"]

    results = {
        "n_seed_pairs": len(seeds),
        "seeds": seeds,
        "arms": arms,
        "metrics_per_arm": {},
        "per_seed_data": {},
        "sidecar_audits": {}
    }

    # Audit sidecars
    for s in seeds:
        for arm in ["A", "B"] + arms:
            name = f"N_E4_{arm}_s{s}"
            sc = sidecars.get(name, {})
            nz = sc.get("extra_params", {}).get("noise", {})
            results["sidecar_audits"][name] = {
                "device": nz.get("device"),
                "mix": nz.get("mix"),
                "seed": sc.get("seed"),
                "endpoint": sc.get("endpoint")
            }

    # Compute metrics per seed and arm
    for arm in arms:
        sv = []   # whole-clip video toward B
        se = []   # motion course toward B
        slm = []  # late motion toward B (filtered)
        slm_seeds = []
        raw_rows = []

        for s in seeds:
            A = feat_map.get(f"N_E4_A_s{s}")
            B = feat_map.get(f"N_E4_B_s{s}")
            X = feat_map.get(f"N_E4_{arm}_s{s}")
            if not (A and B and X):
                continue

            dA = mae(X["G"], A["G"])
            dB = mae(X["G"], B["G"])
            frac_v = dA / (dA + dB + 1e-9)
            sv.append(frac_v)

            eA = 1.0 - corr(X["e"], A["e"])
            eB = 1.0 - corr(X["e"], B["e"])
            frac_e = eA / (eA + eB + 1e-9)
            se.append(frac_e)

            dlm_BA = B["LM"] - A["LM"]
            dlm_XA = X["LM"] - A["LM"]
            frac_lm = None
            if abs(dlm_BA) > 0.3:
                frac_lm = dlm_XA / dlm_BA
                slm.append(frac_lm)
                slm_seeds.append(s)

            raw_rows.append({
                "seed": s,
                "dA": round(dA, 4),
                "dB": round(dB, 4),
                "frac_video_toward_B": round(frac_v, 4),
                "eA": round(eA, 4),
                "eB": round(eB, 4),
                "frac_motion_toward_B": round(frac_e, 4),
                "LM_A": round(A["LM"], 4),
                "LM_B": round(B["LM"], 4),
                "LM_X": round(X["LM"], 4),
                "dlm_BA": round(dlm_BA, 4),
                "frac_LM_toward_B": round(frac_lm, 4) if frac_lm is not None else None
            })

        def stats(arr):
            n = len(arr)
            if n == 0:
                return None
            m = float(np.mean(arr))
            se = float(np.std(arr, ddof=1) / np.sqrt(n)) if n > 1 else 0.0
            return {
                "mean": round(m, 4),
                "se": round(se, 4),
                "std": round(float(np.std(arr, ddof=1)), 4),
                "n": n,
                "values": [round(float(x), 4) for x in arr]
            }

        results["metrics_per_arm"][arm] = {
            "video_toward_B": stats(sv),
            "motion_course_toward_B": stats(se),
            "late_motion_toward_B": stats(slm),
            "late_motion_seeds": slm_seeds,
            "raw": raw_rows
        }

    # Summary table output
    print("\n" + "="*80)
    print("E4 REPLICATION SUMMARY (Finding #4962)")
    print("="*80)
    print(f"{'Arm':<6} | {'Video Toward B (mean ± SE)':<28} | {'Motion Course (mean ± SE)':<28} | {'Late Motion (n=5)':<20}")
    print("-" * 88)
    for arm in arms:
        m = results["metrics_per_arm"][arm]
        v_str = f"{m['video_toward_B']['mean']:.3f} ± {m['video_toward_B']['se']:.3f} (n={m['video_toward_B']['n']})"
        e_str = f"{m['motion_course_toward_B']['mean']:.3f} ± {m['motion_course_toward_B']['se']:.3f} (n={m['motion_course_toward_B']['n']})"
        lm_str = f"{m['late_motion_toward_B']['mean']:.2f} ± {m['late_motion_toward_B']['se']:.2f} (n={m['late_motion_toward_B']['n']})" if m['late_motion_toward_B'] else "N/A"
        print(f"{arm:<6} | {v_str:<28} | {e_str:<28} | {lm_str:<20}")
    print("="*80)

    # Save detailed JSON results
    out_json = os.path.join(OUT_DIR, "replicate_finding_4962_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {out_json}")

if __name__ == "__main__":
    main()
