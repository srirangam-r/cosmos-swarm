"""Known-answer range check for the FAST arm: does measure_pend v1 recover short periods (down to ~0.33 s = 8 f/cycle)?
Draws a black rod + bob swinging about the pend10 pivot (322,127), L 132 px, bob r 11 px, on the real input frame
(the static real pendulum stays put, so it is not in the temporal-median difference). theta(t) = A cos(2 pi t / T),
light damping, 5-subframe motion blur, gaussian noise sigma 2, mp4v encode, 93 f @ 24 fps.
v1 (SYNTH_BLUR=0) drew over the real pendulum; v2 (default) blurs the real pendulum region first.
Usage: python -I synth_fast.py INPUT_PNG OUT_DIR"""
import sys, os, json
import numpy as np, cv2

PIV = (322.0, 127.0); L = 132.0; RB = 11
BLUR = os.environ.get('SYNTH_BLUR', '1') == '1'


def render(bg, th):
    im = bg.copy()
    x = PIV[0] + L * np.sin(th); y = PIV[1] + L * np.cos(th)
    cv2.line(im, (int(PIV[0]), int(PIV[1])), (int(round(x)), int(round(y))), (25, 25, 25), 3, cv2.LINE_AA)
    cv2.circle(im, (int(round(x)), int(round(y))), RB, (15, 15, 15), -1, cv2.LINE_AA)
    return im


def main(inp, out):
    os.makedirs(out, exist_ok=True)
    bg = cv2.imread(inp).astype(np.float32); rng = np.random.default_rng(0); truth = {}
    if BLUR:  # v2: hide the real static pendulum (a drawn dark bob over the real dark bob gives no difference signal)
        yy, xx = np.mgrid[0:bg.shape[0], 0:bg.shape[1]]
        m = ((xx - PIV[0]) ** 2 + (yy - PIV[1]) ** 2) <= 165 ** 2
        bg[m] = cv2.GaussianBlur(bg, (0, 0), 25)[m]
    for T in (0.33, 0.5, 1.0, 1.8):
        for Adeg in (15, 40):
            name = f'synth_T{T:.2f}_A{Adeg}'; p = os.path.join(out, name + '.mp4')
            vw = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*'mp4v'), 24, (bg.shape[1], bg.shape[0]))
            for k in range(93):
                acc = np.zeros_like(bg)
                for j in range(5):
                    t = (k + (j - 2) / 10.0) / 24.0
                    acc += render(bg, np.deg2rad(Adeg) * np.exp(-0.05 * t) * np.cos(2 * np.pi * t / T))
                f = acc / 5 + rng.normal(0, 2, bg.shape)
                vw.write(np.clip(f, 0, 255).astype(np.uint8))
            vw.release(); truth[name] = dict(T=T, A_deg=Adeg)
    json.dump(truth, open(os.path.join(out, 'truth.json'), 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
