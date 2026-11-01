"""Task 152: per-clip PhyFPS with Visual Chronometer (taco-group/Visual_Chronometer, vc_common_10_60fps.ckpt).
Usage: venv/bin/python run_vc.py <vc_inference_dir> <out.json> <video> [<video> ...]
Uses predict.py's own load_model/predict_video (30-frame windows, stride 4, 216x216), from vc_inference_dir.
Stores per-window PhyFPS so the window over the fall can be read separately from the whole-clip mean.
Safety: the checkpoint is a pickle from the Hub. It is loaded with weights_only=True; any non-tensor globals it needs
are listed WITHOUT executing them (torch.serialization.get_unsafe_globals_in_checkpoint) and allow-listed only if they
come from benign modules (omegaconf containers, builtins, collections, typing, numpy dtypes, pathlib). Otherwise abort."""
import sys, os, json, importlib
vc, out, vids = sys.argv[1], sys.argv[2], sys.argv[3:]
sys.path.insert(0, vc); os.chdir(vc)
import torch  # noqa: E402
CK = 'ckpts/vc_common_10_60fps.ckpt'
SAFE = ('omegaconf.', 'builtins.', 'collections.', 'typing.', 'numpy.', 'pathlib.', '_codecs.', 'enum.', 'argparse.Namespace')
bad = torch.serialization.get_unsafe_globals_in_checkpoint(CK)
print('non-tensor globals in ckpt:', bad, flush=True)
objs = []
for g in bad:
    if not g.startswith(SAFE): sys.exit(f'refusing to load: global {g} not allow-listed')
    mod, _, name = g.rpartition('.')
    o = importlib.import_module(mod)
    for part in name.split('.'): o = getattr(o, part)
    objs.append(o)
torch.serialization.add_safe_globals(objs)
_load = torch.load
torch.load = lambda f, map_location=None, **k: _load(f, map_location=map_location, weights_only=True)
import predict  # noqa: E402  (predict.py from the cloned repo; its load_model calls torch.load(ckpt, map_location='cpu'))
model = predict.load_model('configs/config_fps.yaml', CK, 'cuda:0')
res = json.load(open(out)) if os.path.exists(out) else {}
for v in vids:
    n = os.path.splitext(os.path.basename(v))[0]
    if n in res: continue
    segs, avg, T = predict.predict_video(model, v, 'cuda:0', 30, 4, 216)
    res[n] = {'path': v, 'avg_phyfps': float(avg), 'frames': T,
              'segments': [(s['start_frame'], s['predicted_phyfps']) for s in segs]}
    print(n, avg, flush=True)
    json.dump(res, open(out, 'w'), indent=1)
