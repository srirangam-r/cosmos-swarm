import sys, numpy as np
sys.path.insert(0, sys.argv[1]); import trk
F = trk.load(sys.argv[2]); B = trk.blobs(F, mode='ball')
for i, b in enumerate(B):
    if b: print(i, 'cx=%.0f cy=%.0f area=%d long=%.0f short=%.0f' % b)
    else: print(i, None)
