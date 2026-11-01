"""Letterbox real GAUGE pendulum clips to 832x480 like raj-3's pend_pseudo_cosmos (dedup 25-in-30, 7.875 s window)."""
import sys, os, numpy as np, cv2
repo, root, outd = sys.argv[1:4]; os.makedirs(outd, exist_ok=True)
sys.path.insert(0, repo + '/tools/trk_ballfall'); import measure_ball as mb
for i in range(1, 21):
    c = cv2.VideoCapture(f'{root}/{i}.mp4'); R = []
    while len(R) < 250:
        ok, f = c.read()
        if not ok: break
        R.append(f)
    Fd, fac = mb.dedup(np.array(R).astype(np.float32)); fps = 30.0 * fac
    Fd = Fd[: int(np.floor(189 / 24 * fps)) + 1]
    w = cv2.VideoWriter(f'{outd}/pend{i}.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (832, 480))
    for f in Fd:
        L = np.zeros((480, 832, 3), np.uint8); L[6:474] = cv2.resize(f.clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA); w.write(L)
    w.release(); print(i, fps, len(Fd), flush=True)
