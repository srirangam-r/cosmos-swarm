import sys, json, numpy as np, torch, cv2, glob, os, time
torch.set_num_threads(12)
model = torch.hub.load('facebookresearch/co-tracker','cotracker3_offline',trust_repo=True)
dev = sys.argv[1]; model = model.to(dev)
out = sys.argv[2]; os.makedirs(out, exist_ok=True)
seeds = {'b1dd33':(290,185),'b3dd35':(290,180)}
for p in sys.argv[3:]:
    name=os.path.basename(p)[:-4]; o=f'{out}/{name}.npz'
    if os.path.exists(o): continue
    cx,cy = seeds[name.split('_')[0]]
    cap=cv2.VideoCapture(p); fr=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        fr.append(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))
    v=torch.from_numpy(np.stack(fr)).permute(0,3,1,2)[None].float().to(dev)
    pts=[(cx+dx,cy+dy) for dx in (-6,0,6) for dy in (-6,0,6)]
    q=torch.tensor([[0.,x,y] for x,y in pts])[None].to(dev)
    t=time.time()
    with torch.no_grad(): tr,vis=model(v,queries=q)
    np.savez(o,tracks=tr[0].cpu().numpy(),vis=vis[0].cpu().numpy().astype(float))
    print(name,time.time()-t,flush=True)
