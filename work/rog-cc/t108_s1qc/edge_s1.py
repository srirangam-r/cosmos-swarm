# Unvalidated rest screen, t108 seed 1 (both arms; NOT blinded). Ball's right edge over the light plank:
# rows y 315-335 (native 832x480), x 250-370 where the plank is the only background, dark = gray < 50.
import json, numpy as np, av
out = {}
for a in ("F", "QT"):
    fr = np.stack([f.to_ndarray(format="gray") for f in av.open(f"t108_hue/clips/cause_{a}_ball3_fps24_93f_s1.mp4").decode(video=0)]).astype(np.float32)
    band = fr[:, 315:336, 250:371] < 50
    re = []; le = []
    for t in range(len(band)):
        cols = np.nonzero(band[t].sum(0) >= 5)[0]
        re.append(float(cols.max() + 250) if len(cols) else np.nan); le.append(float(cols.min() + 250) if len(cols) else np.nan)
    re = np.array(re); out[a] = {"right_edge_x": re.tolist(), "left_edge_x": le}
    print(a, " ".join(f"f{t}:{re[t]:.0f}" for t in range(18, 93, 6)))
    for w in ((30, 60), (60, 92), (76, 92)):
        s = re[w[0]:w[1] + 1]; print(f"   f{w[0]}-{w[1]}: right-edge range {np.nanmax(s)-np.nanmin(s):.0f}px, net {s[-1]-s[0]:+.0f}px, mean |step| {np.nanmean(np.abs(np.diff(s))):.2f}px/f")
json.dump(out, open("t108_s1qc/edge_s1.json", "w"))
