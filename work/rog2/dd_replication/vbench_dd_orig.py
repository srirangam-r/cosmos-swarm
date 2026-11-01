"""Dynamic degree with VBench's ORIGINAL code path (rog2, task 14; review of msg 159).

Logic copied line-for-line from VBench vbench/dynamic_degree.py (DynamicDegree.infer/get_score/
set_params/check_move/get_frames): cv2 decode, interval=max(1,round(fps/8)), VBench's
third_party RAFT (princeton-vl RAFT) with raft-things.pth, iters=20, InputPadder, top-5% mean,
thres=6*min(H,W)/256, count_num=round(4*n_sampled/16).
Adds dd_norm / dd_frac (same definitions as tools/nv_scoreboard) for comparison.

usage: python vbench_dd_orig.py --vbench <VBench repo> --ckpt raft-things.pth --out out.json clips...
"""
import argparse, json, os, sys, time
import cv2, numpy as np, torch

ap = argparse.ArgumentParser()
ap.add_argument("--vbench", required=True)
ap.add_argument("--ckpt", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--threads", type=int, default=8)
ap.add_argument("clips", nargs="+")
a = ap.parse_args()
torch.set_num_threads(a.threads)
sys.path.insert(0, os.path.join(a.vbench, "vbench", "third_party", "RAFT"))
from core.raft import RAFT  # noqa: E402
from core.utils_core.utils import InputPadder  # noqa: E402


class Args(dict):
    __getattr__ = dict.get

    def __contains__(self, k):  # RAFT does `'dropout' not in args`
        return dict.__contains__(self, k)


args = Args(small=False, mixed_precision=False, alternate_corr=False)
model = RAFT(args)
ck = torch.load(a.ckpt, map_location="cpu")
model.load_state_dict({k.replace("module.", ""): v for k, v in ck.items()})
model.eval()


def get_frames(path):
    fl = []
    v = cv2.VideoCapture(path)
    fps = v.get(cv2.CAP_PROP_FPS)
    interval = max(1, round(fps / 8))
    while v.isOpened():
        ok, f = v.read()
        if not ok:
            break
        f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        fl.append(torch.from_numpy(f.astype(np.uint8)).permute(2, 0, 1).float()[None])
    v.release()
    return fl[::interval], fps, interval, len(fl)


res = json.load(open(a.out)) if os.path.exists(a.out) else {}
for c in a.clips:
    k = os.path.basename(c)
    if k in res:
        continue
    t0 = time.time()
    frames, fps, interval, nraw = get_frames(c)
    scale = min(list(frames[0].shape)[-2:])
    thres = 6.0 * (scale / 256.0)
    count_num = round(4 * (len(frames) / 16.0))
    rads = []
    with torch.no_grad():
        for i1, i2 in zip(frames[:-1], frames[1:]):
            p = InputPadder(i1.shape)
            i1, i2 = p.pad(i1, i2)
            _, flo = model(i1, i2, iters=20, test_mode=True)
            fl = flo[0].permute(1, 2, 0).numpy()
            rad = np.sqrt(fl[:, :, 0] ** 2 + fl[:, :, 1] ** 2)
            h, w = rad.shape
            cut = int(h * w * 0.05)
            rads.append(float(np.mean(np.abs(np.sort(-rad.flatten()))[:cut])))
    rads = np.array(rads)
    above = int((rads > thres).sum())
    res[k] = dict(clip=c, fps=fps, n_raw=nraw, interval=interval, n_sampled=len(frames),
                  thres=thres, count_num=count_num, dd_binary=int(above >= count_num),
                  dd_norm=float(rads.mean() / (scale / 256.0)), dd_frac=above / len(rads),
                  maxrad=[round(r, 4) for r in rads.tolist()], sec=round(time.time() - t0, 1))
    print(k, {x: res[k][x] for x in ("dd_binary", "dd_norm", "dd_frac", "sec")}, flush=True)
    json.dump(res, open(a.out, "w"), indent=1)
