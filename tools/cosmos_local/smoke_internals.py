#!/usr/bin/env python
"""GPU smoke test for the internals hooks. Run it ONLY against a server you started yourself on a free GPU
(never a live swarm endpoint): python smoke_internals.py --url http://HOST:PORT --image first_frame.png [--reference plain_pre_change.mp4]

Small and fast: 416x240, 17 frames (5 latent frames), 6 steps, guidance 6. One plain request, then one per hook, each
with the property it must satisfy. Prints PASS / FAIL / INFO per check and exits 1 if a hard check fails.
 hard checks (bit-exact unless stated):
   plain twice -> identical mp4;  plain == --reference (an mp4 from the pre-change server, same request) if given
   rope scale 1.0, conditioning noise 0, steering alpha 0, capture (read-only) -> identical to plain
   attention factor 1.0 -> near-identical (mean |frame diff| < 1/255; a bias of zeros may pick another SDPA kernel)
   rope 0.5 / noise 0.6 / attention 0.2 / steer alpha 8 -> different from plain
   capture: artifact id header, download, shapes [T,D] and [T,S,D], same arrays on a repeat run
   steer from the capture artifact; wrong-shape vector -> HTTP 400 with the expected shape in the message
   probe: JSON, rows, per-frame length T, forward-vs-forward delta exactly 0, identical-input preflight
 info (read, don't assert): how much each hook moves the output; probe forward vs reverse loss.
"""
import argparse, io, json, sys
import numpy as np
import requests

ap = argparse.ArgumentParser()
ap.add_argument("--url", required=True); ap.add_argument("--image", required=True)
ap.add_argument("--reference"); ap.add_argument("--layers", default="12,24", help="blocks to capture/steer (model has 36)")
ap.add_argument("--hidden", type=int, default=4096, help="transformer hidden_size (4096 for Cosmos3-Nano)")
a = ap.parse_args()
URL = a.url.rstrip("/")
IMG = open(a.image, "rb").read()
NF, STEPS, T, D = 17, 6, 5, a.hidden
L1, L2 = (int(x) for x in a.layers.split(","))
fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg, flush=True)
    if not ok:
        fails.append(msg)


def gen(internals=None, files=None, expect=200):
    extra = {"client": "smoke", **({"internals": internals} if internals else {})}
    data = dict(prompt="A ball falls onto a wooden plank and bounces.", size="416x240", num_frames=str(NF), num_inference_steps=str(STEPS),
                guidance_scale="6.0", seed="1", extra_params=json.dumps(extra))
    r = requests.post(f"{URL}/v1/videos/sync", data=data, files=[("input_reference", ("f.png", IMG, "image/png")), *(files or [])], timeout=7200)
    assert r.status_code == expect, f"HTTP {r.status_code}: {r.text[:400]}"
    return r


def frames(mp4):
    import av
    with av.open(io.BytesIO(mp4)) as c:
        return np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)]).astype(np.float32)


def diff(a_, b_):
    return float(np.abs(frames(a_) - frames(b_)).mean())


plain = gen().content
check(gen().content == plain, "plain request twice -> identical mp4 (determinism)")
if a.reference:
    check(open(a.reference, "rb").read() == plain, "plain == pre-change server output at the same seed (--reference)")

same = {"rope scale 1.0": {"rope": {"temporal_scale": 1.0}}, "conditioning noise 0": {"conditioning": {"noise": {"level": 0.0}}},
        "capture is read-only": {"capture": {"layers": [L1], "step_range": [0, 3]}}}
for name, spec in same.items():
    check(gen(spec).content == plain, f"{name} -> identical to plain")
d = diff(gen({"conditioning": {"attention_scale": {"factor": 1.0}}}).content, plain)
check(d < 1.0, f"attention factor 1.0 -> near-identical (mean abs frame diff {d:.4f}/255)")

for name, spec in {"rope temporal 0.5": {"rope": {"temporal_scale": 0.5}}, "rope j=0,3 x0.5 (gen92 'fast05')": {"rope": {"temporal_scale": {"0": 0.5, "3": 0.5}}},
                   "cond noise 0.6": {"conditioning": {"noise": {"level": 0.6}}},
                   "cond attention x0.2 steps 0-6": {"conditioning": {"attention_scale": {"factor": 0.2}}},
                   "cond attention x0.2 steps 0-2 only": {"conditioning": {"attention_scale": {"factor": 0.2, "step_range": [0, 2]}}}}.items():
    d = diff(gen(spec).content, plain)
    check(d > 0.0, f"{name} -> output differs from plain")
    print(f"INFO {name}: mean abs frame diff vs plain {d:.3f}/255")

# capture
cap = {"capture": {"layers": [L1, L2], "step_range": [0, 6], "every": 3, "passes": ["cond", "uncond"], "full": True}}
r = gen(cap)
aid = r.headers.get("X-Artifact-Ids")
check(bool(aid), f"capture returns an artifact id ({aid})")
z = np.load(io.BytesIO(requests.get(f"{URL}/v1/artifacts/{aid}").content))
keys = sorted(k for k in z.files if k.endswith("_mean"))
check(keys == sorted(f"s{s:03d}_{p}_L{l:02d}_mean" for s in (0, 3) for p in ("cond", "uncond") for l in (L1, L2)), f"capture keys {keys}")
m, f = z[keys[0]], z[keys[0].replace("_mean", "_full")]
check(m.shape == (T, D) and f.ndim == 3 and f.shape[0] == T and f.shape[2] == D, f"shapes mean {m.shape}, full {f.shape} (expect [{T},{D}], [{T},S,{D}])")
check(np.isfinite(m).all() and np.abs(m).max() > 0, "captured means are finite and nonzero")
aid2 = gen(cap).headers["X-Artifact-Ids"]
z2 = np.load(io.BytesIO(requests.get(f"{URL}/v1/artifacts/{aid2}").content))
check(all(np.array_equal(z[k], z2[k]) for k in keys), "capture repeat run -> identical arrays")
print(f"INFO per-frame norms of {keys[0]}: {np.linalg.norm(m, axis=1).round(1).tolist()}")

# steering
vec = {"layer": L1, "artifact": aid, "key": f"s000_cond_L{L1:02d}_mean", "average_frames": True}
check(gen({"steer": {"alpha": 0.0, "vectors": [vec]}}).content == plain, "steer alpha=0 -> identical to plain")
d = diff(gen({"steer": {"alpha": 8.0, "vectors": [vec]}}).content, plain)
check(d > 0.0, f"steer alpha=8 from capture artifact -> differs (mean abs frame diff {d:.3f}/255)")
prof = gen({"steer": {"alpha": 8.0, "vectors": [vec], "frame_profile": [0, 0, 0, 1, 1], "step_range": [0, 3]}})
check(prof.status_code == 200, "steer with frame_profile and step_range runs")
npy = io.BytesIO(); np.save(npy, np.zeros(D - 1, np.float32))
try:
    gen({"steer": {"alpha": 1.0, "vectors": [{"layer": L1, "file": "v.npy"}]}}, files=[("internals_files", ("v.npy", npy.getvalue(), "application/octet-stream"))], expect=400)
    check(True, "wrong-shape upload -> HTTP 400")
except AssertionError as e:
    check(False, f"wrong-shape upload should be 400: {e}")
rr = requests.post(f"{URL}/v1/videos/sync", data=dict(prompt="x", size="416x240", num_frames=str(NF), num_inference_steps=str(STEPS), extra_params=json.dumps(
    {"internals": {"steer": {"alpha": 1.0, "vectors": [{"layer": L1, "file": "v.npy"}]}}})),
    files=[("internals_files", ("v.npy", npy.getvalue(), "application/octet-stream"))])
check(rr.status_code == 400 and f"[{D}]" in rr.text and f"[{T}, {D}]" in rr.text, f"400 message names the expected shapes: {rr.text[:160]}")

# probe: the plain mp4 is not a real clip but is a fine fixed input (416x240, 17 frames)
st = {"sigmas": [0.3, 0.7], "seeds": [1], "variants": ["forward", "reverse"], "fps": 24}
pr = requests.post(f"{URL}/v1/probe/loss", data={"prompt": "A ball falls onto a wooden plank.", "settings": json.dumps(st)},
                   files={"video": ("c.mp4", plain, "video/mp4"), "image": ("f.png", IMG, "image/png")}, timeout=3600)
check(pr.status_code == 200, f"probe/loss HTTP {pr.status_code}")
j = pr.json()
check(len(j["rows"]) == 4 and all(len(x["per_frame"]) == T and x["per_frame"][0] is None for x in j["rows"]), "probe rows: 4, per_frame length T, conditioning frame null")
check(abs(j["determinism_preflight"][0] - j["determinism_preflight"][1]) < 1e-6, f"probe identical-input preflight {j['determinism_preflight']}")
st2 = {**st, "variants": ["forward", "forward"]}
pr2 = requests.post(f"{URL}/v1/probe/loss", data={"prompt": "x", "settings": json.dumps(st2)}, files={"video": ("c.mp4", plain, "video/mp4")})
check(pr2.status_code == 400, "duplicate variants -> 400")
print("INFO probe summary:", json.dumps(j["paired"]))
print("INFO loss by sigma, forward:", j["summary"]["forward"]["by_sigma"])
h = requests.get(f"{URL}/health").json()
check(not h["busy"], f"server idle afterwards: {h}")
print("\nALL HARD CHECKS PASSED" if not fails else f"\n{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
