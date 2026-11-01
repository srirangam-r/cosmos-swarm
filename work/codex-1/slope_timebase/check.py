#!/usr/bin/env python3
"""Probe unmodified source files; pass paths to plastic task-2 clips 1 and 2."""
import hashlib, json, subprocess, sys
from pathlib import Path
out=[]
for arg in sys.argv[1:]:
 p=Path(arg)
 raw=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate,avg_frame_rate,duration,nb_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(p)])
 info=json.loads(raw); ts=[float(x['best_effort_timestamp_time']) for x in info['frames']]
 out.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'stream':info['streams'][0], 'decoded_timestamps':len(ts), 'frame238_to_248_s': round(ts[248]-ts[238],6) if len(ts)>248 else None})
print(json.dumps(out,indent=2))
