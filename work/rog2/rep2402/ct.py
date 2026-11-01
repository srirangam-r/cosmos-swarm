import sys, numpy as np, torch, cv2, glob, os
torch.set_num_threads(12)
model = torch.hub.load('facebookresearch/co-tracker','cotracker3_offline',trust_repo=True)
os.makedirs('out',exist_ok=True)
cx,cy=283,118
for p in sorted(glob.glob('clips/*.mp4')):
    n=os.path.basename(p)[:-4]; o=f'out/{n}.npz'
    if os.path.exists(o): continue
    cap=cv2.VideoCapture(p); fr=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        fr.append(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))
    v=torch.from_numpy(np.stack(fr)).permute(0,3,1,2)[None].float()
    q=torch.tensor([[0.,cx+dx,cy+dy] for dx in (-6,0,6) for dy in (-6,0,6)])[None]
    with torch.no_grad(): tr,vis=model(v,queries=q)
    tr=tr[0].numpy();vis=vis[0].numpy().astype(float)
    np.savez(o,tracks=tr,vis=vis)
    m=np.median(tr,axis=1)
    print(n,'vis %.2f'%vis.mean(),'y@0,8,16,32,60,92:',[int(m[i,1]) for i in (0,8,16,32,60,92)],'x:',[int(m[i,0]) for i in (0,8,16,32,60,92)],flush=True)
