#!/usr/bin/env python3
"""Save compact visual-review copies; quantitative metrics use original videos."""
import subprocess,sys
from pathlib import Path
src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=True)
for p in sorted(src.glob('t170_*.mp4')):
    subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(p),'-vf','trim=start_frame=48:end_frame=93,setpts=PTS-STARTPTS,crop=290:326:190:100',
        '-an','-c:v','libx264','-threads','1','-crf','18','-pix_fmt','yuv420p','-y',str(out/(p.stem+'_f48-92_crop.mp4'))],check=True)
print('24 native-scale late review crops saved')
