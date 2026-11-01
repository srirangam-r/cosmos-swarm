#!/usr/bin/env python3
"""Verify source contracts and independent decoder agreement, not physical validity."""
import hashlib,json,subprocess,sys
from pathlib import Path
import cv2,numpy as np
from analyze import ROOT,decode,digest

clips=Path(sys.argv[1]);results=json.loads((ROOT/'results.json').read_text())
out={'independent_ffmpeg':{},'inputs':{},'native_summaries':{}}
for name in ['ms_pend10_restalg4_s1','ms_pend11_restalg8f4_s1']:
    p=clips/(name+'.mp4')
    raw=subprocess.check_output(['ffmpeg','-v','error','-threads','1','-i',str(p),'-f','rawvideo','-pix_fmt','rgb24','-'])
    fr=np.frombuffer(raw,np.uint8).reshape(-1,480,832,3)
    g=fr[:,90:300,240:420].astype(float).sum(axis=-1)/3
    trace=np.abs(g[1:]-g[:-1]).mean(axis=(1,2))
    saved=next(r['roi']['trace'] for r in results['rows'] if r['name']==name)
    err=float(np.max(np.abs(trace-saved)))
    assert err<1e-10
    out['independent_ffmpeg'][name]={'pairs':len(trace),'trace_max_abs_error':err}
for scene,frame in [('pend10','55'),('pend11','44')]:
    source=ROOT/'inputs'/f'{scene}_rest_f{frame}.png'
    im=cv2.imread(str(source)); values={}
    for r in results['rows']:
        if r['scene']!=scene:continue
        f,_=decode(clips/(r['name']+'.mp4'))
        assert f[0].shape==im.shape
        mse=float(np.mean((f[0].astype(float)-im.astype(float))**2))
        values[r['name']]=float(10*np.log10(255**2/mse)) if mse else None
    out['inputs'][scene]={'shared_file_sha256':digest(source),'f0_input_PSNR_dB':values,
       'scope':'shared original file matches basename; original submitted bytes are not recoverable from queue sidecars'}
for p in sorted((ROOT/'source').glob('ms_pend*.json')):
    n=p.stem;s=json.loads(p.read_text());r=next(r for r in results['rows'] if r['name']==n)
    q=json.loads((ROOT/'sidecars'/p.name).read_text())
    assert s['seed']==q['seed'] and s['prompt']==q['prompt_text']
    assert s['extra_params']['queue_id']==q['queue_id']
    assert s['size']=='832x480' and s['frames_out']==93 and s['fps']==24
    assert s['scheduler']=='UniPCMultistepScheduler'
    out['native_summaries'][n]={'scheduler':s['scheduler'],'model':s['model'],'torch':s['torch'],
        'scope':'native saved summary for four seed1 treatment clips only; no sigma configuration or hook firing telemetry'}
assert len(out['native_summaries'])==4
assert all(v==0 for v in results['first_frame_max_pixel_difference_by_input'].values())
(ROOT/'verification.json').write_text(json.dumps(out,indent=1)+'\n')
print('PASS: 14 decoded request/video contracts; 12 source scalars; 184 independent-decoder trace values; two shared input files; four native summaries. Not planted validation.')
