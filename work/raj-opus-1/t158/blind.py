"""Task 158: fetch clips, make w-blinded eye-coding material.
Usage: python3 blind.py <workdir> [O|A]   (optional arm filter: blind one arm at a time; w stays blind within the arm)
- fetches queue clips (owner raj-opus-1) into <workdir>/clips (t158_*), uses task-139 w=6 ball1 clips from <t139 clips dir>
- assigns random IDs (secrets) per clip; KEY.json (id -> clip) written to <workdir>/KEY.json, NOT to the repo until codes are frozen
- per ID writes <workdir>/blind/<id>_corr.jpg (f0-40 every frame, then every 4th) and <id>_full.jpg (every 8th) and <id>.mp4 symlink
Arm (robot visible or not) is not blindable; w is."""
import sys, os, glob, json, secrets, subprocess, cv2, numpy as np
W = sys.argv[1]; ARM = sys.argv[2] if len(sys.argv) > 2 else None; T139 = '/home/nail/swarm-work/raj-opus-1/t139/clips'
Q = '/home/nail/swarm/agentic_colab/scripts/cosmos_queue.py'
os.makedirs(f'{W}/clips', exist_ok=True); os.makedirs(f'{W}/blind', exist_ok=True)
subprocess.run(['python3', Q, 'fetch', '--owner', 'raj-opus-1', '--out', f'{W}/clips'], capture_output=True)
src = sorted(glob.glob(f'{W}/clips/t158_*.mp4')) + [f'{T139}/t139_{a}_ball1_s{s}.mp4' for a in 'OA' for s in range(1, 9)]
if ARM: src = [p for p in src if f'_{ARM}_' in os.path.basename(p)]
keyp = f'{W}/KEY.json'; key = json.load(open(keyp)) if os.path.exists(keyp) else {}
done = set(key.values())
def frames(p):
    c = cv2.VideoCapture(p); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    return F
for p in src:
    if p in done or not os.path.exists(p): continue
    F = frames(p)
    if len(F) < 90: continue
    i = 'b' + secrets.token_hex(3)
    idx = list(range(0, 41)) + list(range(44, len(F), 4)); th = []
    for k in idx:
        c = cv2.resize(F[k][60:420, 180:380], (100, 180)); cv2.putText(c, str(k), (2, 12), 0, 0.4, (0, 255, 255), 1); th.append(c)
    while len(th) % 9: th.append(np.zeros_like(th[0]))
    cv2.imwrite(f'{W}/blind/{i}_corr.jpg', np.vstack([np.hstack(th[k:k + 9]) for k in range(0, len(th), 9)]))
    full = [cv2.resize(F[k], (277, 160)) for k in range(0, len(F), 8)]
    for k, f in zip(range(0, len(F), 8), full): cv2.putText(f, str(k), (3, 14), 0, 0.45, (0, 255, 255), 1)
    while len(full) % 4: full.append(np.zeros_like(full[0]))
    cv2.imwrite(f'{W}/blind/{i}_full.jpg', np.vstack([np.hstack(full[k:k + 4]) for k in range(0, len(full), 4)]))
    if not os.path.exists(f'{W}/blind/{i}.mp4'): os.link(p, f'{W}/blind/{i}.mp4')  # hard link: no name leak
    key[i] = p
json.dump(key, open(keyp, 'w'), indent=1)
for f in os.listdir(f'{W}/blind'): os.utime(f'{W}/blind/{f}', (1e9, 1e9), follow_symlinks=False)  # no order leak via mtime
print(len(key), 'clips blinded in total;', len(src), 'in this batch (expect 32 for O, 24 for A)')
