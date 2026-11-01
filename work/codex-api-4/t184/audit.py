#!/usr/bin/env python3
"""Same-video eligibility/aggregation audit and exact unchanged-tool replay."""
import csv,hashlib,json,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'tools/trk_ballfall'))
import trk,measure_pend as mp

def summarize(rows,reference):
    grouped={}
    for r in rows:grouped.setdefault(r['seed'],[]).append(r['period_s'])
    means={str(k):float(np.mean(v)) for k,v in sorted(grouped.items())}
    vals=list(means.values());n=len(vals)
    m=float(np.mean(vals)) if n else None
    se=float(np.std(vals,ddof=1)/np.sqrt(n)) if n>1 else None
    return {'clips':len(rows),'seeds':n,'seed_means_s':means,'mean_s':m,
            'seed_SE_s':se,'ratio_to_saved_real':m/reference if n else None,
            'ratio_SE':se/reference if se is not None else None}

def main():
    clips=Path(sys.argv[1]);(ROOT/'res').mkdir(exist_ok=True)
    key=json.loads((ROOT/'key.json').read_text())
    author=json.loads((ROOT/'source/author_periods.json').read_text())
    codes={r['id']:r for r in csv.DictReader((ROOT/'codes.csv').open())}
    hashes={line.split()[1].split('/')[-1]:line.split()[0]
            for line in (ROOT/'source/author_clips_SHA256SUMS').read_text().splitlines()}
    rows=[];replayed={};tracks={};maxerr=0
    for ident,item in key.items():
        name=item['name'];p=clips/(name+'.mp4');s=json.loads((ROOT/'source'/f'{name}.json').read_text())
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        assert digest==item['sha256']==hashes[p.name]
        assert (s['width'],s['height'],s['num_frames'],s['steps'],s['guidance'])==(832,480,93,35,6.0)
        cap=cv2.VideoCapture(str(p));fps=cap.get(cv2.CAP_PROP_FPS);cap.release()
        F=trk.load(str(p));assert F.shape==(93,480,832,3) and fps==s['fps']==24
        r=mp.measure(F,fps,keep_track=True);track=r.pop('track');replayed[name]=r
        # Exact original result replay includes bootstrap intervals, not only fits.
        assert r.keys()==author[name].keys()
        for k,v in r.items():
            if isinstance(v,(float,int,list)):
                err=float(np.max(np.abs(np.asarray(v)-np.asarray(author[name][k])))) if np.size(v) else 0
                maxerr=max(maxerr,err);assert err<1e-7,(name,k,err)
            else:assert v==author[name][k]
        B=trk.blobs(F);tracks[name]={'blobs':[None if b is None else [float(x) for x in b] for b in B],'fit_track':track}
        row={'id':ident,'name':name,'seed':s['seed'],'arm':s['extra_params']['arm'],
             'endpoint':s['endpoint'],**codes[ident],**r}
        row['fit_zc_relative_gap']=abs(r['period_s']-r['period_zc_s'])/r['period_s']
        rows.append(row)
        # Deterministic native overlays locate the unchanged largest moving blob.
        idx=[4,12,24,36,48,60,72,84,92]
        canvas=Image.new('RGB',(3*390,3*329),'white');d=ImageDraw.Draw(canvas)
        for j,k in enumerate(idx):
            f=F[k].astype(np.uint8).copy();b=B[k]
            if b:cv2.drawMarker(f,(round(b[0]),round(b[1])),(0,0,255),cv2.MARKER_CROSS,16,2)
            im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).crop((130,25,520,330))
            x=j%3*390;y=j//3*329;canvas.paste(im,(x,y+24))
            d.text((x+4,y+4),f'{ident} f{k} centroid '+('none' if b is None else f'{b[0]:.1f},{b[1]:.1f}'),fill='black')
        canvas.save(ROOT/'res'/f'{ident}_centroids.jpg',quality=94)
    reference=author['real_pend10_cont']['period_s']
    stats={'author_s5_s7':summarize([r for r in rows if r['seed']>=5],reference),
           'all_flags_ok':summarize([r for r in rows if r['flag']=='ok'],reference),
           'rigid_Y_and_ok':summarize([r for r in rows if r['rigid']=='Y' and r['flag']=='ok'],reference),
           'unclear_rigid_and_ok_descriptive_only':summarize([r for r in rows if r['rigid']=='U' and r['flag']=='ok'],reference)}
    counts={field:{v:sum(r[field]==v for r in rows) for v in sorted(set(r[field] for r in rows))}
            for field in ('flag','rigid','motion','scene')}
    stats.update({'counts':counts,'author_included_check_count':sum(r['seed']>=5 and r['flag']=='check' for r in rows),
                  'max_original_replay_absolute_error':maxerr,'request_video_hash_audits_pass':len(rows),
                  'saved_real_fit_vs_mocap_relative_error':reference/author['mocap_pend10_window']['period_zc_s']-1,
                  'saved_real_fps':author['real_pend10_cont']['fps'],
                  'tool_sha256':{n:hashlib.sha256((REPO/'tools/trk_ballfall'/n).read_bytes()).hexdigest() for n in ('trk.py','measure_pend.py')}})
    for name,obj in [('results.json',stats),('rows.json',rows),('replayed_periods.json',replayed),('tracks.json',tracks)]:
        (ROOT/'res'/name).write_text(json.dumps(obj,indent=1)+'\n')
    print(json.dumps(stats,indent=1))

if __name__=='__main__':main()
