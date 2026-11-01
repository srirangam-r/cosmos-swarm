"""Blind coding sheets for task 174 (blur dial).

python blind.py make   -> assigns each clips_blur/hrb_*.mp4 a random 4-letter id (key in blind_key.json,
                          do not open before codes are frozen), writes sheets_blind/<id>.jpg:
                          row 1: spot crop (start position) every 4th frame; rows 2+: full-frame context every 6th frame.
python blind.py unblind codes_blind.json -> writes codes_blur.json keyed by clip name.
"""
import json
import os
import random
import string
import sys

import cv2
import numpy as np

CL = 'clips_blur'
OUT = 'sheets_blind'
KEY = 'blind_key.json'


def frames(p):
    cap = cv2.VideoCapture(p)
    fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        fr.append(f)
    return fr


def sheet(fr, bid):
    sp = []
    for k in range(0, len(fr), 4):
        x = cv2.resize(np.clip(fr[k][85:145, 247:307].astype(float) * 2.0, 0, 255).astype(np.uint8), None, fx=1.4, fy=1.4)
        cv2.putText(x, str(k), (2, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        sp.append(x)
    row = np.hstack(sp)
    W = row.shape[1]
    cx = []
    for k in range(0, len(fr), 6):
        t = cv2.resize(fr[k][0:430, 150:500], None, fx=0.5, fy=0.5)
        cv2.putText(t, str(k), (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        cx.append(t)
    per = W // cx[0].shape[1]
    rows = []
    for i in range(0, len(cx), per):
        r = cx[i:i + per]
        while len(r) < per:
            r.append(np.zeros_like(cx[0]))
        rows.append(np.hstack(r))
    ctx = np.vstack(rows)
    ctx = np.pad(ctx, ((0, 0), (0, W - ctx.shape[1]), (0, 0)))
    cr = []
    for k in range(0, 24):
        t = fr[k][60:390, 207:347].copy()
        cv2.line(t, (0, 53), (6, 53), (0, 0, 255), 1)
        t = cv2.resize(t, (84, 198))
        cv2.putText(t, str(k), (2, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        cr.append(t)
    corr = np.hstack(cr)
    corr = np.pad(corr, ((0, 0), (0, max(0, W - corr.shape[1])), (0, 0)))[:, :W]
    hdr = np.zeros((18, W, 3), np.uint8)
    cv2.putText(hdr, bid, (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    return np.vstack([hdr, row, corr, ctx])


if sys.argv[1] == 'make':
    key = json.load(open(KEY)) if os.path.exists(KEY) else {}
    used = set(key.values())
    rng = random.SystemRandom()
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(os.listdir(CL)):
        if not f.endswith('.mp4'):
            continue
        n = f[:-4]
        if n in key and '--force' not in sys.argv:
            continue
        fr = frames(os.path.join(CL, f))
        if len(fr) < 93:
            continue
        if n in key:
            cv2.imwrite(os.path.join(OUT, key[n] + '.jpg'), sheet(fr, key[n]), [cv2.IMWRITE_JPEG_QUALITY, 88])
            continue
        while True:
            b = ''.join(rng.choice(string.ascii_uppercase) for _ in range(4))
            if b not in used:
                break
        used.add(b)
        key[n] = b
        cv2.imwrite(os.path.join(OUT, b + '.jpg'), sheet(fr, b), [cv2.IMWRITE_JPEG_QUALITY, 88])
    json.dump(key, open(KEY, 'w'), indent=1)
    print('sheets:', len(key))
elif sys.argv[1] == 'unblind':
    key = json.load(open(KEY))
    inv = {v: k for k, v in key.items()}
    codes = json.load(open(sys.argv[2]))
    out = {inv[b]: v for b, v in codes.items()}
    json.dump(dict(sorted(out.items())), open('codes_blur.json', 'w'), indent=1)
    print('unblinded', len(out))
