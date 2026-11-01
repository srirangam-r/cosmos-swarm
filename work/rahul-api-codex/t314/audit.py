#!/usr/bin/env python3
"""Independent aggregate/provenance audit, not a media or physics replication.

Stdlib only. Read immutable git objects from a33fc5a; never import author code.
Exact six-scene bootstrap uses all 6**6 ordered draws via 462 multisets.
"""
import collections
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics as st
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REV = "a33fc5a"
BASE = "work/dk2/t276/"
manifest = {}
checks = []


def read(path):
    raw = subprocess.check_output(["git", "show", f"{REV}:{path}"], cwd=REPO)
    manifest[path] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    return raw


def load(path):
    return json.loads(read(path))


def check(label, value):
    checks.append({"check": label, "pass": bool(value)})
    if not value:
        raise AssertionError(label)


def close(a, b, eps=1e-12):
    return (a is None and b is None) or (a is not None and b is not None and abs(a-b) < eps)


def percentile_weighted(values, weights, q):
    """Linear percentile of the explicitly expanded finite distribution."""
    z = sorted(zip(values, weights))
    n = sum(weights)
    p = (n-1)*q
    low, high = math.floor(p), math.ceil(p)
    found = {}
    cumulative = 0
    for v, w in z:
        for rank in (low, high):
            if cumulative <= rank < cumulative+w:
                found[rank] = v
        cumulative += w
    return found[low] + (p-low)*(found[high]-found[low])


def ci(values, weights):
    return [percentile_weighted(values, weights, q) for q in (.025, .975)]


def main():
    res = load(BASE + "out/t276_results.json")
    frames = {x["id"]: x for x in load(BASE + "frames.json")}
    rows = res["rows"]
    scenes = sorted(frames)
    expected = {(f, a, s) for f in scenes for a in ("plain", "nphys", "nphys_x17")
                for s in ((1,) if a == "nphys_x17" else (1, 2, 3))}
    check("exact42scene_arm_seed_slots", len(rows) == len(expected) == 42 and
          {(r["frame"], r["arm"], r["seed"]) for r in rows} == expected)
    for name in ("README.md", "analyze_t276.py", "build_jobs.py", "jobs_plain.jsonl",
                 "jobs_nphys.jsonl", "jobs_nphys_x17.jsonl", "out/t276_table.md"):
        read(BASE + name)
    acf_source = read("tools/pend_acf/pend_acf.py").decode()
    check("acf_has_no_short_clip_flag", "short_clip" not in acf_source)
    rebuilt = []
    native = []
    prompts = set()
    full_grids = []
    plain_grids = []
    for r in rows:
        pa, pm = r["P_acf_s"], r["P_mp_s"]
        finite = lambda x: isinstance(x, (float, int)) and math.isfinite(x) and x > 0
        agree = finite(pa) and finite(pm) and abs(pm/pa-1) <= .10
        clean = r["flag_acf"] == "ok" and r["flicker"] < .08 and agree
        pr = frames[r["frame"]]["P_real_s"]
        ratio = pa/pr if clean else None
        ratio_mp = pm/pr if clean else None
        check(r["clip"] + ":gate", clean == r["clean"])
        check(r["clip"] + ":ratio", close(ratio, r["ratio"]) and close(ratio_mp, r["ratio_mp"]))
        rr = dict(r, clean=clean, ratio=ratio, ratio_mp=ratio_mp)
        rebuilt.append(rr)
        sc = load(BASE + "clips/" + r["clip"] + ".json")
        sv = load(BASE + "clips/" + r["clip"] + ".server.json")
        qc = load(BASE + "clips/" + r["clip"] + ".qc.json")
        prompts.add(sc["prompt_text"])
        check(r["clip"] + ":request_constants", sc["seed"] == r["seed"] == sv["seed"] and
              sc["num_frames"] == sv["num_frames"] == r["n_frames"] == 93 and
              sc["width"] == 832 and sc["height"] == 480 and sv["size"] == "832x480" and
              sc["fps"] == sv["fps"] == 24 and sc["steps"] == sv["num_inference_steps"] == 35 and
              sc["guidance"] == sv["guidance_scale"] == 6 and sc["flow_shift"] == sv["flow_shift"] == 10 and
              sc["extra_params"]["noise"]["device"] == sv["extra_params"]["noise"]["device"] == "cpu")
        check(r["clip"] + ":prompt_and_image_label", sc["prompt_text"] == sv["prompt"] and
              sc["image"] == "f0_" + r["frame"] + ".png")
        lat = sv.get("latent")
        sig = sv["sigmas_used"]
        suffix_ok = None
        if lat:
            k = lat["start_step"]
            grid = lat["sigmas_request"]
            full_grids.append(grid)
            check(r["clip"] + ":native_start", k == 19 and len(grid) == 36 and
                  grid[k] == lat["sigma_start"] == .89844)
            suffix_ok = sig == grid[k:]
            check(r["clip"] + ":recorded_suffix", suffix_ok)
        else:
            plain_grids.append(sig)
        native.append({"clip": r["clip"], "arm": r["arm"], "queue_id": sc["queue_id"],
                       "endpoint": sc["endpoint"], "server_rev": sv["server_rev"],
                       "sigmas_used_count": len(sig), "recorded_latent_suffix_matches": suffix_ok,
                       "sigma_start": lat["sigma_start"] if lat else None})

    check("one_prompt_across42", len(prompts) == 1)
    check("42unique_queue_ids", len({r["queue_id"] for r in native}) == 42)
    check("24identical_latent_full_grids", len(full_grids) == 24 and all(g == full_grids[0] for g in full_grids))
    check("nine_plain36entry_grids_match_latent_grid", sum(g == full_grids[0] for g in plain_grids) == 9)
    check("nine_plain1000entry_arrays_retained", sum(len(g) == 1000 for g in plain_grids) == 9)

    by = {a: [r for r in rebuilt if r["arm"] == a] for a in ("plain", "nphys", "nphys_x17")}
    arms = {}
    for a, z in by.items():
        good = [r for r in z if r["clean"]]
        summary = dict(n=len(z), clean=len(good), within10=sum(abs(r["ratio"]-1) <= .1 for r in good),
                       median_ratio=st.median(r["ratio"] for r in good) if good else None,
                       median_ratio_mp=st.median(r["ratio_mp"] for r in good) if good else None,
                       median_flicker=st.median(r["flicker"] for r in z),
                       flicker_range=[min(r["flicker"] for r in z), max(r["flicker"] for r in z)],
                       acf_flags=dict(collections.Counter(r["flag_acf"] for r in z)))
        for key in ("n", "clean", "within10", "median_ratio", "median_ratio_mp", "median_flicker"):
            check(a + ":author_summary:" + key, close(summary[key], res["arms"][a][key]))
        arms[a] = summary

    scene_rows = []
    for f in scenes:
        s = {"frame": f}
        for a, z in by.items():
            zz = [r for r in z if r["frame"] == f]
            good = [r for r in zz if r["clean"]]
            ratios = [r["ratio"] for r in good]
            s[a] = {"n": len(zz), "clean": len(good),
                    "within10": sum(abs(v-1) <= .1 for v in ratios),
                    "clean_ratios": ratios,
                    "clean_ratio_seed_sample_sd": st.stdev(ratios) if len(ratios) >= 2 else None}
        scene_rows.append(s)

    clean_delta = [(s["nphys"]["clean"]-s["plain"]["clean"])/3 for s in scene_rows]
    success_delta = [(s["nphys"]["within10"]-s["plain"]["within10"])/3 for s in scene_rows]
    weighted = []
    for ix in itertools.combinations_with_replacement(range(6), 6):
        counts = collections.Counter(ix)
        weight = math.factorial(6)//math.prod(math.factorial(c) for c in counts.values())
        weighted.append((ix, weight))
    check("exact_bootstrap_weight", sum(w for _, w in weighted) == 6**6)
    boot = {}
    for name, vals in (("clean_rate_delta", clean_delta), ("within10_all_slots_delta", success_delta)):
        v = [sum(vals[i] for i in ix)/6 for ix, _ in weighted]
        w = [w for _, w in weighted]
        expanded = sorted(sum(vals[i] for i in ix)/6 for ix in itertools.product(range(6), repeat=6))
        expanded_ci = []
        for q in (.025, .975):
            p = (len(expanded)-1)*q
            lo, hi = math.floor(p), math.ceil(p)
            expanded_ci.append(expanded[lo]+(p-lo)*(expanded[hi]-expanded[lo]))
        interval = ci(v, w)
        check(name + ":weighted_vs_direct46656", all(close(x, y) for x, y in zip(interval, expanded_ci)))
        effects = [sum(sign*x for sign, x in zip(signs, vals))/6
                   for signs in itertools.product((-1, 1), repeat=6)]
        observed = st.mean(vals)
        boot[name] = {"estimate": observed, "ci95": interval, "scene_deltas": vals,
                      "two_sided_scene_sign_flip_p": sum(abs(v) >= abs(observed)-1e-12 for v in effects)/64}
    for a in ("plain", "nphys"):
        v, w, empty = [], [], 0
        for ix, weight in weighted:
            pool = [x for i in ix for x in scene_rows[i][a]["clean_ratios"]]
            if pool:
                v.append(st.median(pool)); w.append(weight)
            else:
                empty += weight
        boot[a+"_conditional_clean_median"] = {"ci95": ci(v, w),
                                                 "empty_draws_excluded": empty,
                                                 "nonempty_draws": sum(w)}

    control = []
    for r in by["nphys_x17"]:
        pr = frames[r["frame"]]["P_real_s"]
        control.append({"frame": r["frame"], "seed": r["seed"], "clean": r["clean"],
                        "acf_flag": r["flag_acf"], "mp_flag": r["flag_mp"],
                        "ratio_unfiltered_acf": r["P_acf_s"]/pr if r["P_acf_s"] else None,
                        "ratio_unfiltered_mp": r["P_mp_s"]/pr if r["P_mp_s"] else None})
    numeric = [r["ratio_unfiltered_acf"] for r in control if r["ratio_unfiltered_acf"] is not None]
    for f in frames.values():
        check(f["id"]+":reference_rounding", abs(f["P_real_frames_mp"]/25-f["P_real_s"]) <= .00005)
        read(BASE+f["image"])
        for arm in ("nphys", "nphys_x17"):
            read(BASE+f"proxies/proxy_{f['id']}_{arm}.mp4")
    report = {"review_type": "Independent aggregate/provenance audit only; no media remeasurement",
              "source_commit": subprocess.check_output(["git", "rev-parse", REV], cwd=REPO, text=True).strip(),
              "arms": arms, "scenes": scene_rows, "paired_scene_bootstrap": boot,
              "bootstrap_method": "Resample six scenes with replacement, retain all paired seeds/arms. Exact6**6 via462multisets; independently checked against46656 ordered draws. Percentile95%; descriptive fixed-dev-set uncertainty, no correction for outcome-conditioned survival.",
              "x17_controls": control, "x17_numeric_only_median": st.median(numeric),
              "x17_numeric_only_denominator": len(numeric), "native_receipts": native,
              "checks": {"passed": len(checks), "total": len(checks), "details": checks},
              "limitations": ["Input reader scalars and rounded flicker reused; no independent planted or media measurement.",
                              "Reference periods come from measure_pend on real videos at25Hz, not a separately supplied mocap table.",
                              "Supplied real-video-derived period is a diagnostic input, not inference of period from frame0+prompt.",
                              "Only seed1 has wrong-period control; cannot satisfy charter's3seed cause gate.",
                              "All42 server receipts identify historical04e8e0de81; nine plain receipts contain1000sigma entries. Post-call metadata cannot certify actual step calls.",
                              "Reviewedgit snapshot contains126JSON sidecars and contact strips but no generatedMP4s; image basenames/request metadata do not authenticate media or exact loaded checkpoint bytes.",
                              "No DOVER, motion fidelity, plausibility or robot-prediction nonregression tested here."]}
    (HERE/"audit_results.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    (HERE/"source_manifest.json").write_text(json.dumps({"commit": report["source_commit"], "files": manifest}, indent=2)+"\n")
    print(json.dumps({"checks": len(checks), "source_files": len(manifest), "arms": arms,
                      "paired_scene_bootstrap": boot, "x17_numeric_only_median": st.median(numeric)}, indent=2))


if __name__ == "__main__":
    main()
