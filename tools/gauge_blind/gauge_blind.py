#!/usr/bin/env python3
"""gauge_blind v1.1 (ro-1): blind scorer for Cosmos clips generated from the official GAUGE bouncing-ball frame
(held ball in the Franka gripper, 832x480, 539.8 px/m). Implements rahul-3's pre-registered task-24 metrics (msg 613):

1. release (y/n): the seeded-tracker centre drops > 1 ball diameter below its frame-0 position within the clip.
   (by-eye confirmation is recorded separately from the contact sheet: column eye_call, filled by hand.)
2. first-fall g (m/s^2): bclock (referee planted PASS 12/12, msg 593) on the post-release track: curvature of the first
   flight if r2>0.98 and n>=5, else timing form g = 2 h0 / t_fall^2. Scale 539.8 px/m (GAUGE table plane).
3. bounce decay: (a) e1 = T1 / (2 t_fall) and the median flight-time ratio T_{k+1}/T_k;
   (b) time-to-rest = first frame after the first impact from which |y - y_t| < 2 px for the next 6 frames
       (right-censored at the last frame), and at_rest_by_end.
Diagnostics (not pre-registered; help the by-eye call): held_at_end_ncc (frame-0 ball patch still in the gripper at
the last frame, NCC within +-30 px; high = still held / back in gripper), rest_minus_impact_px (negative = comes to rest
above the floor, e.g. returned to the gripper), mean_ncc_post_release (low = tracker likely lost the ball).
eye_call vocabulary: released | held | substitute (a different/new ball does the fall) | ambiguous.
Settings are frozen; the clip is never looked at before scoring (arm labels are blinded by the generator).

usage: python3 -I gauge_blind.py CLIPDIR OUTDIR [--fps 24]
"""
import argparse, csv, glob, json, os, sys
import numpy as np
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bclock'))
import bclock  # noqa: E402

SEED = (281.0, 119.0)   # held-ball centre on the official GAUGE frame 0 (832x480)
PPM = 539.8
HALF = 14
SEARCH = 40
REST_PX, REST_N = 2.0, 6


def score(path, fps, sheetdir):
    F = bclock.read_frames(path)
    n = len(F)
    _, _, med = bclock.auto_seed(F, need_seed=False)
    r = bclock.ball_radius(F[0].astype(np.float32), med, *SEED)
    D = 2 * r if r and 6 < 2 * r < 60 else 22.0
    xs, ys, sc, _ = bclock.track(F, SEED[0], SEED[1], 0, HALF, SEARCH, 0.8)
    y0 = ys[0]
    drop = ys - y0
    ok = (sc >= 0.3) & ~np.isnan(ys)
    exceed = np.where(ok & (drop > D))[0]
    row = dict(clip=os.path.basename(path), n_frames=n, diam_px=round(D, 1), tracked_frac=round(float(ok.mean()), 3),
               max_drop_px=round(float(np.nanmax(drop[ok])) if ok.any() else 0.0, 1))
    # track-independent check: is the frame-0 ball patch still at the gripper in the last frame? (max NCC within +-30 px)
    G0 = cv2.cvtColor(F[0], cv2.COLOR_BGR2GRAY); GL = cv2.cvtColor(F[-1], cv2.COLOR_BGR2GRAY)
    xi, yi = int(SEED[0]), int(SEED[1])
    tpl = G0[yi - HALF:yi + HALF + 1, xi - HALF:xi + HALF + 1]
    roi = GL[yi - HALF - 30:yi + HALF + 31, xi - HALF - 30:xi + HALF + 31]
    row['held_at_end_ncc'] = round(float(cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED).max()), 3)
    res = {}
    if len(exceed) == 0:
        row.update(release=0)
    else:
        t1 = int(exceed[0])
        pre = np.where(ok[:t1] & (np.abs(drop[:t1]) < 2.0))[0]
        t_r = int(pre[-1]) if len(pre) else 0
        row.update(release=1, release_frame=t_r)
        y2 = ys.copy(); y2[:t_r] = np.nan; y2[~ok] = np.nan
        res = bclock.analyse(y2, fps, PPM, 8.0, 1)
        fl0 = (res.get('flights') or [None])[0]
        g = None
        if fl0 and fl0['r2'] > 0.98 and fl0['n'] >= 5 and fl0['c'][0] > 0:
            g = 2 * fl0['c'][0] * fps * fps / PPM; gsrc = 'curv_first'
        elif res.get('g_fall_timing'):
            g = res['g_fall_timing']; gsrc = 'fall_timing'
        else:
            gsrc = None
        ti = res.get('impact_t_frames', [])
        ers = res.get('e_ratio_seq', [])
        t_rest = None
        if ti:
            for t in range(int(np.ceil(ti[0])), n - REST_N):
                w = y2[t:t + REST_N + 1]
                if np.all(~np.isnan(w)) and np.max(np.abs(w - w[0])) < REST_PX:
                    t_rest = t; break
        row.update(g=None if g is None else round(g, 3), g_src=gsrc, first_fall_r2=None if not fl0 else round(fl0['r2'], 4),
                   n_impacts=len(ti), impacts=' '.join('%.1f' % v for v in ti),
                   e1=None if res.get('e_timing_first') is None else round(res['e_timing_first'], 3),
                   e_ratio_med=round(float(np.median(ers)), 3) if ers else None,
                   time_to_rest_frame=t_rest if t_rest is not None else n - 1, rest_censored=int(t_rest is None),
                   at_rest_by_end=int(t_rest is not None), bclock_flag=res.get('flag'),
                   rest_minus_impact_px=None if (t_rest is None or not ti) else round(float(y2[t_rest] - res['impact_level_px']), 1),
                   mean_ncc_post_release=round(float(np.mean(sc[t_r:])), 3))
    # contact sheet: every 4th frame with the tracked centre
    idx = list(range(0, n, 4))
    tiles = []
    for i in idx:
        f = F[i].copy()
        if ok[i]: cv2.circle(f, (int(xs[i]), int(ys[i])), int(D / 2 + 4), (0, 0, 255), 2)
        cv2.putText(f, str(i), (8, 34), 0, 1.2, (0, 255, 255), 3)
        tiles.append(cv2.resize(f, (277, 160)))
    while len(tiles) % 6: tiles.append(np.zeros_like(tiles[0]))
    sheet = np.vstack([np.hstack(tiles[k:k + 6]) for k in range(0, len(tiles), 6)])
    cv2.imwrite(os.path.join(sheetdir, row['clip'].rsplit('.', 1)[0] + '_sheet.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])
    full = dict(row, track_y=[None if np.isnan(v) else round(float(v), 2) for v in ys],
                track_x=[None if np.isnan(v) else round(float(v), 2) for v in xs], score=[round(float(s), 3) for s in sc],
                bclock={k: v for k, v in res.items() if k != 'flights'})
    return row, full


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clipdir'); ap.add_argument('outdir'); ap.add_argument('--fps', type=float, default=24)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    clips = sorted(glob.glob(os.path.join(a.clipdir, '**', '*.mp4'), recursive=True))
    rows, fulls = [], {}
    for p in clips:
        try:
            row, full = score(p, a.fps, a.outdir)
        except Exception as e:  # never drop a clip silently
            row, full = dict(clip=os.path.relpath(p, a.clipdir), error=repr(e)), {}
        row['clip'] = os.path.relpath(p, a.clipdir); row['eye_call'] = ''
        rows.append(row); fulls[row['clip']] = full
        print(row, file=sys.stderr)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(os.path.join(a.outdir, 'scores.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(rows)
    json.dump(fulls, open(os.path.join(a.outdir, 'scores_full.json'), 'w'))


if __name__ == '__main__':
    main()
