import sys, json, numpy as np
sys.path.insert(0, sys.argv[1]); import trk
for i in range(1, 23):
    F = trk.load(f'video/{i}.mp4'); B = trk.blobs(F, mode='ball'); del F
    json.dump([list(map(float, b)) if b else None for b in B], open(f'tracks/{i}.json', 'w')); print(i, flush=True)
