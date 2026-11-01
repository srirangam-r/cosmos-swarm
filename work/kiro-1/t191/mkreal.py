import sys, json, numpy as np, cv2
sys.path.insert(0, '../cosmos-swarm/tools/trk_ballfall')
import measure_ball as mb
def lbvid(path):
    c = cv2.VideoCapture(path); R = []
    while len(R) < 300:
        ok, f = c.read()
        if not ok: break
        R.append(f)
    Fd, fac = mb.dedup(np.array(R).astype(np.float32)); fps = 30.0 * fac
    LB = []
    for f in Fd:
        L = np.zeros((480, 832, 3), np.uint8); L[6:474] = cv2.resize(f.clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA); LB.append(L)
    return LB, fps
for N, k in [(10, 93), (12, 101)]:
    LB, fps = lbvid(f'../gauge/{N}.mp4'); W = LB[k:k + 93]
    vw = cv2.VideoWriter(f'real_pend{N}_f{k}.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (832, 480))
    for f in W: vw.write(f)
    vw.release(); json.dump(dict(fps=fps, src=f'GAUGE pendulum {N}', start=k), open(f'real_pend{N}_f{k}.json', 'w')); print(N, fps, len(W))
