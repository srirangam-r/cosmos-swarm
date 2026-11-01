"""Task 152: per-clip PhyFPS with Visual Chronometer (taco-group/Visual_Chronometer, vc_common_10_60fps.ckpt).
Usage: venv/bin/python run_vc.py <vc_inference_dir> <out.json> <video> [<video> ...]
Uses predict.py's own load_model/predict_video (30-frame windows, stride 4, 216x216), unmodified, from vc_inference_dir.
Stores per-window PhyFPS so the window over the fall can be read separately from the whole-clip mean."""
import sys, os, json, hashlib
vc, out, vids = sys.argv[1], sys.argv[2], sys.argv[3:]
sys.path.insert(0, vc); os.chdir(vc)
import torch, predict  # noqa: E402  (predict.py from the cloned repo)
model = predict.load_model('configs/config_fps.yaml', 'ckpts/vc_common_10_60fps.ckpt', 'cuda:0')
res = json.load(open(out)) if os.path.exists(out) else {}
for v in vids:
    n = os.path.splitext(os.path.basename(v))[0]
    if n in res: continue
    segs, avg, T = predict.predict_video(model, v, 'cuda:0', 30, 4, 216)
    res[n] = {'path': v, 'avg_phyfps': float(avg), 'frames': T,
              'segments': [(s['start_frame'], s['predicted_phyfps']) for s in segs]}
    print(n, avg, flush=True)
    json.dump(res, open(out, 'w'), indent=1)
