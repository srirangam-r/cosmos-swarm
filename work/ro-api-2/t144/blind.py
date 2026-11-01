"""Usage: python blind.py <fetched_dir> <blind_out_dir>
Copies t144 clips to opaque hex ids (key written to <blind_out_dir>/../KEY_DO_NOT_OPEN.json, gitignored until codes committed),
and writes per-clip strips: ball corridor crop x 200-360, y 30-430, frames 0-40 every 2, then 44..92 every 4."""
import sys, os, json, glob, secrets, shutil, cv2
import numpy as np
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
keyp = os.path.join(os.path.dirname(os.path.abspath(out)), 'KEY_DO_NOT_OPEN.json')
key = json.load(open(keyp)) if os.path.exists(keyp) else {}
inv = {v: k for k, v in key.items()}
FR = list(range(0, 41, 2)) + list(range(44, 93, 4))
for mp4 in sorted(glob.glob(os.path.join(src, 't144_*.mp4'))):
    name = os.path.basename(mp4)[:-4]
    if name not in inv:
        h = secrets.token_hex(3); key[h] = name; inv[name] = h
    h = inv[name]
    if os.path.exists(os.path.join(out, h + '_strip.jpg')): continue
    shutil.copy(mp4, os.path.join(out, h + '.mp4'))
    cap = cv2.VideoCapture(mp4); v = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        v.append(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    tiles = [Image.fromarray(v[f, 30:430, 200:360]) for f in FR if f < len(v)]
    cols = 12; rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (160 * cols, 400 * rows))
    for i, t in enumerate(tiles): sheet.paste(t, (160 * (i % cols), 400 * (i // cols)))
    sheet.save(os.path.join(out, h + '_strip.jpg'), quality=90)
json.dump(key, open(keyp, 'w'), indent=1)
print(len(key), 'clips blinded ->', out)
