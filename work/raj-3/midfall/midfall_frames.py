"""raj-3: make 'mid-fall' I2V first frames from GAUGE real ball drops: dedup (25-in-30 fps), letterbox 1280x720 -> 832x468 + 6 px pad
(same transform as raj-1's Cosmos inputs), dump frames around the release, plus a contact sheet with frame numbers.
Usage: python3 -I midfall_frames.py <gauge_real_dir> <repo_root> <outdir> <clip> <f0> <f1>"""
import sys, numpy as np, cv2
root, repo, outd, clip, f0, f1 = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
sys.path.insert(0, repo + '/tools/trk_ballfall'); import trk, measure_ball as mb
F = trk.load(f'{root}/video/{clip}.mp4'); F, fac = mb.dedup(F)
tiles = []
for k in range(f0, f1 + 1):
    L = np.zeros((480, 832, 3), np.uint8)
    L[6:474] = cv2.resize(F[k].clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA)
    cv2.imwrite(f'{outd}/gauge_ball{clip}_dd{k}_832x480.png', L)
    T = L[0:300, 150:450].copy(); cv2.putText(T, str(k), (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2); tiles.append(T)
cv2.imwrite(f'{outd}/sheet_ball{clip}.jpg', np.hstack(tiles))
print('fps', 30 * fac, 'n', len(F))
