# independent replication of #1175 pixel stats (rog2; separate code: cv2 decode, 416x240 area downscale, RGB mean abs)
import cv2, numpy as np, json, sys, itertools
D=sys.argv[1]
def load(n):
    c=cv2.VideoCapture(f"{D}/negmeta_{n}.mp4"); fs=[]
    while True:
        ok,f=c.read()
        if not ok: break
        fs.append(cv2.resize(f,(416,240),interpolation=cv2.INTER_AREA).astype(np.float32))
    return np.stack(fs)
names=[f"{m}_{t}_ball{b}_s{s}" for m in("inv","same") for t in("empty","nvneg") for b in(1,2) for s in(1,2)]
V={n:load(n) for n in names}
mot={n:float(np.abs(np.diff(V[n],axis=0)).mean()) for n in names}
mae=lambda a,b:float(np.abs(V[a]-V[b]).mean())
out={"nframes":{n:len(V[n]) for n in names},"motion":mot,"pairs":[]}
for b in(1,2):
  for s in(1,2):
    k=f"ball{b}_s{s}"
    out["pairs"].append(dict(clip=k,
      meta_empty=mae(f"inv_empty_{k}",f"same_empty_{k}"),meta_nv=mae(f"inv_nvneg_{k}",f"same_nvneg_{k}"),
      neg_inv=mae(f"inv_empty_{k}",f"inv_nvneg_{k}"),neg_same=mae(f"same_empty_{k}",f"same_nvneg_{k}"),
      seed_inv_empty=mae(f"inv_empty_ball{b}_s1",f"inv_empty_ball{b}_s2")))
e=np.array([mot[n] for n in names if "_empty_" in n]);j=np.array([mot[n] for n in names if "_nvneg_" in n])
# paired by (meta,ball,seed)
pe=[(mot[n],mot[n.replace("_empty_","_nvneg_")]) for n in names if "_empty_" in n]
d=np.array([a-b for a,b in pe])
out["summary"]=dict(empty_mean=e.mean(),empty_se=e.std(ddof=1)/np.sqrt(len(e)),nv_mean=j.mean(),nv_se=j.std(ddof=1)/np.sqrt(len(j)),
  paired_diff_mean=d.mean(),paired_diff_se=d.std(ddof=1)/np.sqrt(len(d)),n_lower=int((d>0).sum()),n=len(d))
json.dump(out,open(sys.argv[2],"w"),indent=1)
print(json.dumps(out["summary"],indent=1))
for p in out["pairs"]:print({k:(round(v,2) if not isinstance(v,str) else v) for k,v in p.items()})
print(set(out["nframes"].values()))
