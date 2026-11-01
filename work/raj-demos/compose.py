"""Side-by-side demo clips for the slides (Raj via Claude). usage: compose.py OUT_BASENAME HEADER FOOTER path|title|sub ...
Each panel 416x240 with a caption bar; writes OUT.mp4 (H.264, yuv420p, 24 fps) and OUT.gif (looping, 12 fps)."""
import sys, subprocess, cv2, numpy as np
out, header, footer, specs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
PW, PH, CAP = 416, 240, 44
def read(p):
    cap = cv2.VideoCapture(p); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(cv2.resize(f, (PW, PH), interpolation=cv2.INTER_AREA))
    return F
panels = [(read(s.split("|")[0]), s.split("|")[1], s.split("|")[2]) for s in specs]
n = min(len(p[0]) for p in panels)
W = PW * len(panels) + 8 * (len(panels) - 1); H = 40 + CAP + PH + 30
tmp = out + ".raw.mp4"; vw = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*"mp4v"), 24, (W, H))
def text(img, s, org, scale, color, thick=1):
    cv2.putText(img, s, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick, cv2.LINE_AA)
for i in range(n):
    canvas = np.full((H, W, 3), 24, np.uint8)
    text(canvas, header, (10, 27), 0.62, (255, 255, 255), 1)
    for k, (F, title, sub) in enumerate(panels):
        x = k * (PW + 8)
        cv2.rectangle(canvas, (x, 40), (x + PW, 40 + CAP), (48, 48, 48), -1)
        text(canvas, title, (x + 8, 40 + 19), 0.55, (255, 255, 255), 1)
        text(canvas, sub, (x + 8, 40 + 38), 0.45, (170, 220, 255), 1)
        canvas[40 + CAP:40 + CAP + PH, x:x + PW] = F[i]
    text(canvas, footer, (10, H - 10), 0.42, (190, 190, 190), 1)
    vw.write(canvas)
vw.release()
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                "-movflags", "+faststart", out + ".mp4"], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-vf",
                "fps=12,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer", "-loop", "0", out + ".gif"], check=True)
import os; os.remove(tmp); print("wrote", out + ".mp4", out + ".gif", n, "frames", W, "x", H)
