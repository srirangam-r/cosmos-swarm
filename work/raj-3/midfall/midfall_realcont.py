"""raj-3: real continuation of the mid-fall first frames (control for task 15 and a tool check): GAUGE real ball video,
dedup, letterboxed to 832x480 exactly like the I2V input, starting at the chosen mid-fall frame, written at the distinct-frame rate.
Usage: python3 -I midfall_realcont.py <gauge_real_dir> <repo_root> <outdir> <clip> <frame> [<clip> <frame> ...]"""
import sys, json, numpy as np, cv2
root, repo, outd = sys.argv[1:4]; args = list(map(int, sys.argv[4:]))
sys.path.insert(0, repo + '/tools/trk_ballfall'); import trk, measure_ball as mb
for clip, fr in zip(args[::2], args[1::2]):
    F = trk.load(f'{root}/video/{clip}.mp4'); F, fac = mb.dedup(F); fps = 30.0 * fac
    name = f'real_ball{clip}_from_dd{fr}'; w = cv2.VideoWriter(f'{outd}/{name}.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (832, 480))
    for f in F[fr:fr + 75]:
        L = np.zeros((480, 832, 3), np.uint8); L[6:474] = cv2.resize(f.clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA); w.write(L)
    w.release(); json.dump(dict(fps=fps, source=f'GAUGE ball {clip} dedup frames {fr}..{fr+74}, letterboxed'), open(f'{outd}/{name}.json', 'w'))
