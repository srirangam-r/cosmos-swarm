#!/usr/bin/env python3
"""Post-hoc measurement sensitivity check, never a physical-release estimator."""
import argparse,json
from pathlib import Path
import cv2
import numpy as np

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--clips',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    out={'description':'same 93 decoded frames; whole image vs visible-content columns x218:614, excluding input black letterbox; fixed author threshold 3.5 gray levels; unvalidated','crop_xyxy':[218,0,614,480],'clips':{}}
    for p in sorted(a.clips.glob('t140_pend_rest_*.mp4')):
        cap=cv2.VideoCapture(str(p));fs=[]
        while True:
            ok,f=cap.read()
            if not ok:break
            fs.append(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY).astype(np.float64))
        cap.release();g=np.asarray(fs);delta=np.abs(g-g[0]);full=float(delta.mean((1,2)).max());crop=float(delta[:,:,218:614].mean((1,2)).max())
        out['clips'][p.stem]={'full_max_diff':full,'content_max_diff':crop,'full_gt3_5':full>3.5,'content_gt3_5':crop>3.5}
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
