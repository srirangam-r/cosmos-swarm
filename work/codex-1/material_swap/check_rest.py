import cv2, json, numpy as np, sys
cap=cv2.VideoCapture(sys.argv[1]); pts=[]
while True:
    ok,frame=cap.read()
    if not ok: break
    i=len(pts); roi=frame[210:310,360:470]; gray=cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY)
    mask=(gray<90).astype('uint8'); n,lab,stats,c=cv2.connectedComponentsWithStats(mask,8)
    k=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]) if n>1 else None
    pts.append(None if k is None else [round(float(c[k,0]+360),3),round(float(c[k,1]+210),3),int(stats[k,cv2.CC_STAT_AREA])])
a=np.array(pts[40:189]); d=a[:,:2]-a[0,:2]; print(json.dumps({'frames':len(pts),'window':'40-188 inclusive','roi_xyxy':[360,210,470,310],'threshold_gray_lt':90,'first':pts[40],'last':pts[188],'centroid_x_range_px':np.ptp(a[:,0]),'centroid_y_range_px':np.ptp(a[:,1]),'max_displacement_from_frame40_px':float(np.max(np.linalg.norm(d,axis=1))),'area_range_px': [int(a[:,2].min()),int(a[:,2].max())]},indent=2))
