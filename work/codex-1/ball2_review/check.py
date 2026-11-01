import cv2, numpy as np, json
p='work/ro-1/fps_sweep/ballE2/ball_F_ball2_fps24_93f_s1.mp4'
c=cv2.VideoCapture(p); frames=[]
while True:
 ok,f=c.read()
 if not ok: break
 frames.append(cv2.cvtColor(f[185:370,220:350],cv2.COLOR_BGR2GRAY).astype(np.float32))
f=np.array(frames); assert len(f)==93
out={}
for a,b in [(10,50),(50,93),(10,93)]:
 vals={k:round(float(np.abs(f[a:b-k]-f[a+k:b]).mean()),4) for k in range(1,16)}
 out[f'{a}:{b}']={'mean_absolute_difference':vals,'minimum_lag_5_to_15':min(range(5,16),key=vals.get)}
print(json.dumps(out,indent=2))
