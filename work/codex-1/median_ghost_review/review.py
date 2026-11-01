import cv2, numpy as np, json
from pathlib import Path

# Independent image-level mechanism test; not the original slope estimator.
rng=np.random.default_rng(30261)
rows=[]
for rest in (0, 10, 40):
    errs=[]; ghost=[]
    for seed in range(100):
        # Static textured background; contrasting object; integer translations.
        bg=rng.integers(100,201,(100,240),dtype=np.uint8)
        start=int(rng.integers(10,25)); end=start+120; y=40
        if seed % 2: start, end = end, start
        xs=np.rint(np.linspace(start,end,21)).astype(int)
        frames=[]
        for x in list(xs)+[end]*rest:
            im=bg.copy(); im[y:y+12,x:x+12]=20; frames.append(im)
        stack=np.array(frames); med=np.median(stack,axis=0)
        for idx,x in enumerate(xs[:-2]): # exclude near-overlap with final cube
            change=(np.abs(stack[idx].astype(float)-med)>40).astype(np.uint8)
            ghost.append(float(change[y:y+12,end:end+12].mean()))
            count, labels, stats, centers=cv2.connectedComponentsWithStats(change,8)
            j=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]); pred=centers[j,0]
            errs.append(abs(pred-(x+5.5)))
    a=np.array(errs); b=np.array(ghost)
    rows.append(dict(rest_frames=rest,total_frames=21+rest,n_sequences=100,n_motion_frames=len(a),ghost_fraction_mean=float(b.mean()),track_error_px_mean=float(a.mean()),track_error_gt_12px_fraction=float((a>12).mean())))
print(json.dumps(rows,indent=2))
Path(__file__).with_name('results.json').write_text(json.dumps(rows,indent=2)+'\n')
