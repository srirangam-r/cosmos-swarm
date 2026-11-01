#!/usr/bin/env python
"""Before/after and seed-noise statistics for score.py outputs (NVIDIA scoreboard: DOVER + dynamic degree).

  python compare.py noise  SCORES.json [--real REAL.json]
      Groups clips that share everything but the seed (same input image, prompt, negative prompt,
      settings) and reports the pooled within-group seed sd per metric.

  python compare.py paired BEFORE.json AFTER.json [--real REAL.json] [--pair_by image,seed]
      Pairs clips across the two runs (default: same input image + same seed; a fix may change the
      prompt, settings or checkpoint, so those are not part of the key). Reports per metric the
      scene-weighted mean difference AFTER-BEFORE with a bootstrap 95% CI over scenes, and,
      with --real, a descriptive per-clip gap |dd - dd_real(task)|; this is
      not NVIDIA's motion-fidelity score, which also requires motion control.

Pairing/grouping keys come from each clip's JSON sidecar (client.py or server.py format:
image/input_image/source_frame, seed, prompt_text/prompt, negative_prompt_text/negative_prompt,
num_frames, fps, steps/num_inference_steps, guidance/guidance_scale, flow_shift). A stable image_id or image_sha256 is preferred; otherwise the full image path is used.
Missing metadata is rejected. The task (for the real reference) is the first regex group of --task_re
on the clip basename (default matches ball / pend / slope). Missing or ambiguous pairing keys
are errors. CIs are descriptive; they do not establish non-inferiority.
"""
import argparse, hashlib, json, os, re, sys
import numpy as np

METRICS = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_norm", "dd_frac", "dd_binary"]
DD = ["dd_norm", "dd_frac", "dd_binary"]
# Additional recorded generation context. An absent field is unknown, not an
# asserted default. Never group an explicit value with an unknown value.
NOISE_CONTEXT = ("model", "checkpoint", "inference_stack", "use_duration_template",
                 "use_resolution_template", "use_system_prompt", "negative_metadata_mode",
                 "noise_context", "cond_fps", "play_fps")


def noise_context(meta):
    extra = meta.get("extra_params") or {}
    if not isinstance(extra, dict):
        sys.exit("extra_params must be an object when grouping seed noise")
    result = []
    for key in NOISE_CONTEXT:
        values = [d[key] for d in (meta, extra) if key in d]
        encoded = [json.dumps(v, sort_keys=True, separators=(",", ":")) for v in values]
        if len(set(encoded)) > 1:
            sys.exit(f"conflicting {key} in sidecar and extra_params")
        result.append((key, encoded[0] if encoded else None))
    return tuple(result)


def load(path):
    d = json.load(open(path))
    base = os.path.dirname(os.path.abspath(path))
    out = {}
    for name, r in d.items():
        side = r.get("sidecar")
        meta = r.get("metadata") or {}
        for cand in ([side, os.path.join(base, side)] if side else []) + \
                    [os.path.splitext(r.get("clip", ""))[0] + ".json"]:
            if not meta and cand and os.path.exists(cand):
                meta = json.load(open(cand)); break
        out[name] = dict(r, meta=meta)
    return out


def g(meta, *keys):
    for k in keys:
        if meta.get(k) not in (None, ""):
            return meta[k]
    return None


def field(r, what):
    m, name = r["meta"], os.path.splitext(os.path.basename(r.get("clip", "")))[0]
    if what == "image":
        # A stable, explicitly assigned ID is preferred across machines.  Never
        # reduce paths to basenames: two different scenes can share one.
        v = g(m, "image_id", "image_sha256", "image", "input_image", "source_frame")
        return str(v) if v is not None else None
    if what == "seed":
        return g(m, "seed")
    if what == "prompt":
        v = g(m, "prompt_text", "prompt")
        return hashlib.sha256(str(v).encode()).hexdigest() if v is not None else None
    if what == "neg":
        # Explicit null is a real request value, distinct from an absent key or
        # an empty string. Its interpretation is specific to the inference stack.
        for k in ("negative_prompt_text", "negative_prompt"):
            if k in m:
                return hashlib.sha256(json.dumps(m[k], sort_keys=True).encode()).hexdigest()
        return None
    if what == "settings":
        return tuple(g(m, *ks) for ks in (("num_frames",), ("fps",), ("steps", "num_inference_steps"),
                                          ("guidance", "guidance_scale"), ("flow_shift",), ("width",), ("height",)))
    if what == "name":
        return name
    raise KeyError(what)


def task_of(r, task_re):
    m = re.search(task_re, os.path.basename(r.get("clip", "")))
    return m.group(1) if m else None


def boot_ci(x, n=4000, seed=0):
    x = np.asarray(x, float)
    if len(x) < 2:
        return (None, None)
    rng = np.random.default_rng(seed)
    bs = x[rng.integers(0, len(x), (n, len(x)))].mean(1)
    return (float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))


def real_ref(path, task_re):
    if not path:
        return {}
    R = load(path)
    by = {}
    for r in R.values():
        t = task_of(r, task_re)
        if t is not None:  # clips whose name matches no task (e.g. a synthetic sanity clip) are skipped
            by.setdefault(t, []).append(r)
    return {t: {m: float(np.mean([r[m] for r in rs if m in r])) for m in METRICS if any(m in r for r in rs)}
            for t, rs in by.items()}


def cmd_noise(a):
    S = load(a.scores)
    groups = {}
    for name, r in S.items():
        key = (field(r, "image"), field(r, "prompt"), field(r, "neg"), field(r, "settings"), noise_context(r["meta"]),
               (r.get("fps"), r.get("fps_source")))
        if any(v is None for v in key[:3]) or any(v is None for v in key[3]) or field(r, "seed") is None:
            sys.exit(f"missing image, prompt, negative prompt, complete settings, or seed: {name}")
        groups.setdefault(key, []).append(r)
    rep = dict(n_clips=len(S), n_groups=len(groups), groups=[], pooled_seed_sd={}, across_all_sd={},
               context_note="Unknown generation context is not proof of identical settings. Verify checkpoint, stack, templates and other conditioning before interpreting seed noise.")
    for key, rs in groups.items():
        seeds = [field(r, "seed") for r in rs]
        if len(set(seeds)) != len(seeds):
            sys.exit(f"duplicate seed within noise group: {key[0]}")
        context = {k: json.loads(v) for k, v in key[4] if v is not None}
        unknown = [k for k, v in key[4] if v is None]
        rep["groups"].append(dict(image=key[0], neg=key[2], context=context, unknown_context=unknown, scored_fps=key[5][0], fps_source=key[5][1], n=len(rs), seeds=[field(r, "seed") for r in rs],
                                  **{m: [round(r[m], 4) for r in rs] for m in METRICS if all(m in r for r in rs)}))
    for m in METRICS:
        num, df = 0.0, 0
        for rs in groups.values():
            v = [r[m] for r in rs if m in r]
            if len(v) > 1:
                num += np.var(v, ddof=1) * (len(v) - 1); df += len(v) - 1
        if df:
            rep["pooled_seed_sd"][m] = dict(sd=float(np.sqrt(num / df)), df=df)
        allv = [r[m] for r in S.values() if m in r]
        if len(allv) > 1:
            rep["across_all_sd"][m] = dict(mean=float(np.mean(allv)), sd=float(np.std(allv, ddof=1)), n=len(allv))
    ref = real_ref(a.real, a.task_re)
    if ref:
        rep["real_reference"] = ref
    print(json.dumps(rep, indent=1))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)


def cmd_paired(a):
    A, B = load(a.before), load(a.after)
    keys = a.pair_by.split(",")
    kf = lambda r: tuple(field(r, k) for k in keys)
    if "image" not in keys:
        sys.exit("pair_by must include image for scene-level resampling")
    def index(rows, label):
        result = {}
        for name, r in rows.items():
            k = kf(r)
            if any(v is None for v in k):
                sys.exit(f"missing pairing key in {label}: {name}")
            if k in result:
                sys.exit(f"duplicate pairing key in {label}: {k}")
            result[k] = r
        return result
    ia, ib = index(A, "before"), index(B, "after")
    if ia.keys() != ib.keys():
        sys.exit(f"unmatched pairing keys: {len(ia.keys() - ib.keys())} before, {len(ib.keys() - ia.keys())} after")
    pairs = [(ia[k], ib[k]) for k in ia]
    if not pairs:
        sys.exit("no pairs: check --pair_by and sidecars")
    ref = real_ref(a.real, a.task_re)
    rep = dict(n_pairs=len(pairs), pair_by=keys, n_before=len(A), n_after=len(B), metrics={},
               inference_note="Scene-weighted bootstrap; descriptive only, not a non-inferiority test. Real-reference uncertainty is excluded.")
    for m in METRICS:
        P = [(field(x, "image"), x[m], y[m]) for x, y in pairs if m in x and m in y]
        if not P:
            continue
        scenes = {}
        for scene, x, y in P:
            scenes.setdefault(scene, []).append((x, y))
        scene_means = np.array([np.mean(v, axis=0) for v in scenes.values()])
        xa, xb = scene_means.T
        d = xb - xa
        e = dict(n=len(P), before=float(xa.mean()), after=float(xb.mean()), delta=float(d.mean()),
                 n_scenes=len(scenes), delta_ci95=boot_ci(d), delta_sd=float(d.std(ddof=1)) if len(d) > 1 else None)
        if m in DD and ref:
            gaps = [(abs(x[m] - ref[task_of(x, a.task_re)][m]), abs(y[m] - ref[task_of(x, a.task_re)][m]))
                    for x, y in pairs if m in x and m in y and task_of(x, a.task_re) == task_of(y, a.task_re)
                    and m in ref.get(task_of(x, a.task_re), {})]
            if gaps:
                ga, gb = np.array(gaps).T
                e.update(gap_to_real_before=float(ga.mean()), gap_to_real_after=float(gb.mean()),
                         gap_change=float((gb - ga).mean()), gap_n_pairs=len(gaps))
        rep["metrics"][m] = e
    print(json.dumps(rep, indent=1))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    n = sp.add_parser("noise"); n.add_argument("scores")
    p = sp.add_parser("paired"); p.add_argument("before"); p.add_argument("after")
    p.add_argument("--pair_by", default="image,seed")
    for x in (n, p):
        x.add_argument("--real"); x.add_argument("--out")
        x.add_argument("--task_re", default=r"(ball|pend|slope)")
    a = ap.parse_args()
    cmd_noise(a) if a.cmd == "noise" else cmd_paired(a)


if __name__ == "__main__":
    main()
