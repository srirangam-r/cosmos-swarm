"""Saturation / blockiness of the proxy mp4 itself (outside dk1's box) vs its frame 0, to see if nphys inherits them.
usage: python -I proxy_feats.py <prox_dir> <rev6767_out> <bg_features.py dir>"""
import sys, json, os, importlib.util
prox, rdir, bdir = sys.argv[1:4]
sys.argv = ['x', '/nonexistent', rdir, '/dev/null']
src = open(os.path.join(bdir, 'bg_features.py')).read().split('rows = {}')[0]
ns = {}; exec(src, ns)
meta = json.load(open(os.path.join(rdir, 'swap_meta.json')))['clips']
for sc in ['09', '12', '16', '17', '18', '19']:
    p = os.path.join(prox, f'proxy_real_{sc}_nphys.mp4')
    if not os.path.exists(p): print(sc, 'missing'); continue
    f = ns['feats'](ns['read'](p), meta[f'{sc}_s1']['box'])
    print(sc, {k: round(v, 3) for k, v in f.items()})
