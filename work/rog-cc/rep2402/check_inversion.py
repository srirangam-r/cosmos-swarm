"""rog-cc rep2402: are ro-agy1 task90 clips colour-inverted? Compares clip f0 with the input frame and with its negative.
Also writes true-colour (255-x) sheets: full frame (f0..f92) and gripper zoom (x200-380, y40-220).
Usage: python3 -I check_inversion.py RESULTS_DIR INPUT_PNG OUTDIR"""
import sys, os, glob, cv2, numpy as np
R, inp, od = sys.argv[1:4]; os.makedirs(od, exist_ok=True)
a = cv2.imread(inp)
full, grip = [], []
for p in sorted(glob.glob(R + "/*.mp4")):
    c = cv2.VideoCapture(p); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    print(os.path.basename(p), "MAE f0 vs input %.1f, vs inverted input %.1f" % (np.abs(F[0].astype(int) - a.astype(int)).mean(), np.abs(F[0].astype(int) - (255 - a).astype(int)).mean()))
    T = [255 - f for f in F]
    full.append(np.hstack([cv2.resize(T[i], (208, 120)) for i in [0, 4, 8, 12, 16, 24, 32, 44, 56, 68, 80, 92]]))
    grip.append(np.hstack([cv2.resize(T[i][40:220, 200:380], (180, 180)) for i in [0, 8, 16, 24, 32, 48, 64, 80, 92]]))
cv2.imwrite(od + "/sheet_true_full.jpg", np.vstack(full)); cv2.imwrite(od + "/sheet_true_gripper.jpg", np.vstack(grip))
