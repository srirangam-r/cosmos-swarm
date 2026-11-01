# ro-1: scale-free late-motion energy in the ball corridor (x220-360, y130-360): mean |frame_t - frame_{t-1}| (gray levels)
# over f2-45 (early) and f46-92 (late). A ball at rest -> late ~ noise floor; perpetual bouncing -> late ~ early.
import av, numpy as np, sys, os, json
out = {}
for f in sys.argv[1:]:
    g = np.stack([x.to_ndarray(format='gray').astype(np.float32)[130:360, 220:360] for x in av.open(f).decode(video=0)])
    d = np.abs(np.diff(g, axis=0)).mean((1, 2))
    out[os.path.basename(f)] = dict(early=round(float(d[1:45].mean()), 3), late=round(float(d[45:].mean()), 3), late_last20=round(float(d[-20:].mean()), 3))
    print(os.path.basename(f), out[os.path.basename(f)])
json.dump(out, open('fps_sweep/cause_meas/late_motion.json', 'w'), indent=1)
