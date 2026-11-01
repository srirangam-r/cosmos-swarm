"""Same-clip image-difference check; run from repository root."""
import json
import cv2
import numpy as np
p = 'work/ro-1/fps_sweep/ballF/ball_F_ball1_fps24_93f_s1.mp4'
c = cv2.VideoCapture(p)
frames = []
while True:
    ok, frame = c.read()
    if not ok:
        break
    frames.append(cv2.cvtColor(frame[260:390, 240:360], cv2.COLOR_BGR2GRAY).astype(np.float32))
f = np.asarray(frames)
assert len(f) == 93
out = {}
for start, end in [(18, 50), (52, 93)]:
    out[f'{start}:{end}'] = {str(k): round(float(np.mean(np.abs(f[start:end-k] - f[start+k:end]))), 4) for k in range(1, 13)}
print(json.dumps(out, indent=2))
