"""Task 144 V-test edits on t139's ball1_G frame (hand+fingers removed, arm kept).
Ball disk (280,116) r=12 kept pixel-identical (protected r=13 core). Arms:
 A  untouched; VD trail above ball (ball moving DOWN); VU trail below (moving UP);
 VI isotropic halo (radial ghosts); VB VD's delta translated to a background patch.
VU/VI/VB edit L2 matched to VD within 2% by scaling alpha (bisection)."""
import json, hashlib, sys
import numpy as np
from PIL import Image
SRC = sys.argv[1]
src = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float64)
H, W, _ = src.shape
CX, CY, R, RCORE = 280, 116, 12, 13
yy, xx = np.mgrid[0:H, 0:W]
core = (xx-CX)**2 + (yy-CY)**2 <= RCORE**2
# ball patch with soft disk alpha
PR = 16
patch = src[CY-PR:CY+PR+1, CX-PR:CX+PR+1].copy()
py, px = np.mgrid[-PR:PR+1, -PR:PR+1]
pm = np.clip(R + 0.5 - np.sqrt(px**2+py**2), 0, 1)  # soft disk
def ghosts(offsets, alphas, gain):
    out = src.copy()
    for (dx, dy), a in sorted(zip(offsets, alphas), key=lambda t: -abs(t[0][0])-abs(t[0][1])):
        a = min(1.0, a*gain)
        y0, x0 = CY+dy-PR, CX+dx-PR
        reg = out[y0:y0+2*PR+1, x0:x0+2*PR+1]
        al = (pm*a)[..., None]
        reg[:] = reg*(1-al) + patch*al
    out[core] = src[core]
    return out
N = 12
lin_off = [(0, 4*(k+1)) for k in range(N)]            # 4..48 px (2 diameters)
lin_a = [0.55*(1-k/N) for k in range(N)]               # decays away from ball
def VD(g): return ghosts([(0, -d) for _, d in lin_off], lin_a, g)
def VU(g): return ghosts([(0, d) for _, d in lin_off], lin_a, g)
ang = np.linspace(0, 2*np.pi, 16, endpoint=False)
iso_off = [(int(round(r*np.cos(t))), int(round(r*np.sin(t)))) for r in (4, 8, 12) for t in ang]
iso_a = [0.35*(1-(r/16)) for r in (4, 8, 12) for _ in ang]
def VI(g): return ghosts(iso_off, iso_a, g)
BX = 220  # translate VD delta horizontally to curtain at x~500
def VB_from(vd_img, g):
    d = (vd_img - src)*g
    out = src.copy()
    out[:, BX:] = np.clip(src[:, BX:] + d[:, :-BX], 0, 255)
    return out
def l2(img): return float(np.sqrt(((np.round(img)-src)**2).sum()))
target = l2(VU(1.8))  # common energy all arms can reach without opaque ghosts
def match(fn):
    lo, hi = 0.05, 4.0
    for _ in range(40):
        mid = (lo+hi)/2
        if l2(fn(mid)) < target: lo = mid
        else: hi = mid
    return fn((lo+hi)/2), (lo+hi)/2
vd, gd = match(VD); vu, gu = match(VU); vi, gi = match(VI); vb, gb = match(lambda g: VB_from(vd, g))
arms = {'A': src, 'VD': vd, 'VU': vu, 'VI': vi, 'VB': vb}
gains = {'A': 0, 'VD': gd, 'VU': gu, 'VI': gi, 'VB': gb}
def psnr(img):
    m = ((np.round(img)-src)**2).mean(); return float('inf') if m == 0 else float(10*np.log10(255**2/m))
qc = {}
for k, im in arms.items():
    u8 = np.clip(np.round(im), 0, 255).astype(np.uint8)
    p = f'inputs/G1_{k}.png'; Image.fromarray(u8).save(p)
    diff = np.abs(u8.astype(int)-src.astype(int)).sum(2) > 0
    qc[k] = dict(path=p, sha256=hashlib.sha256(open(p,'rb').read()).hexdigest(), gain=gains[k],
                 edited_px=int(diff.sum()), core_identical=bool((u8[core] == src[core].astype(np.uint8)).all()),
                 l2=l2(u8.astype(float)), l2_ratio_to_VD=l2(u8.astype(float))/target if k!='A' else 0.0,
                 l1=float(np.abs(u8.astype(float)-src).sum()), psnr=psnr(u8.astype(float)))
qc['_meta'] = dict(src=SRC, src_sha256=hashlib.sha256(open(SRC,'rb').read()).hexdigest(), ball=(CX,CY,R), core_r=RCORE)
json.dump(qc, open('inputs/edits_qc.json','w'), indent=1)
print(json.dumps(qc, indent=1))
crops = [Image.fromarray(np.clip(np.round(arms[k]),0,255).astype(np.uint8)).crop((200,30,360,230)).resize((320,400), Image.NEAREST) for k in arms]
sheet = Image.new('RGB', (320*5, 400)); [sheet.paste(c, (320*i, 0)) for i, c in enumerate(crops)]
sheet.save('inputs/preview_A_VD_VU_VI_VB.jpg')
full = Image.fromarray(np.clip(np.round(vb),0,255).astype(np.uint8)).resize((416,240)); full.save('inputs/preview_VB_full.jpg')
