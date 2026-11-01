# rog1 kap: write each cut as dedup'd 25.16 fps-content mp4 (encoded at 25 fps), letterboxed 1280x720 -> 832x468 + 6 px pad = 832x480.
import json, cv2, subprocess, numpy as np, os, sys
src = sys.argv[1]; od = sys.argv[2]; os.makedirs(od, exist_ok=True)
man = json.load(open('manifest.json')); T = json.load(open('tracks.json'))
cache = {}
for m in man:
    c = m['clip']
    if c not in cache:
        cap = cv2.VideoCapture(f'{src}/video/{c}.mp4'); fr = []
        while True:
            ok, f = cap.read()
            if not ok: break
            fr.append(f)
        cache = {c: fr}
    fr = cache[c]; dup = T[c]['dup']
    idx = [i for i in range(m['start_f'], m['end_f'] + 1) if not dup[i]]
    m['n_out_frames'] = len(idx); m['out_fps'] = 25; m['src_frames_kept'] = [idx[0], idx[-1]]
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '832x480', '-r', '25', '-i', '-',
                          '-c:v', 'libx264', '-crf', '28', '-pix_fmt', 'yuv420p', f"{od}/{m['cut_id']}.mp4"], stdin=subprocess.PIPE)
    for i in idx:
        im = cv2.resize(fr[i], (832, 468), interpolation=cv2.INTER_AREA)
        p.stdin.write(cv2.copyMakeBorder(im, 6, 6, 0, 0, cv2.BORDER_CONSTANT, value=0).tobytes())
    p.stdin.close(); p.wait()
json.dump(man, open('manifest.json', 'w'), indent=1)
