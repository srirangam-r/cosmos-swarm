"""Run the unchanged preregistered tools; keep outputs masked until QC freeze."""
import pathlib,json,subprocess,sys,concurrent.futures,os
ROOT=pathlib.Path(__file__).resolve().parent
REPO=next(p for p in [ROOT.parent/'cosmos-swarm',*ROOT.parents] if (p/'tools/trk_ballfall/measure_pend.py').exists())
TOOLS=REPO/'tools'
def one(item):
    code,name=item;clip=ROOT/'clips'/(name+'.mp4')
    if not clip.exists():return code,None
    out={}
    for kind,tool,args in [('mp','trk_ballfall/measure_pend.py',[]),('acf','pend_acf/pend_acf.py',['--skip','12'])]:
        p=subprocess.run([sys.executable,'-I',str(TOOLS/tool),str(clip),'--fps','24',*args],capture_output=True,text=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
        try:out[kind]=json.loads(p.stdout)
        except Exception:out[kind]={'error':p.stderr[-3000:],'stdout':p.stdout[-500:]}
    return code,out
if __name__=='__main__':
    key=json.loads((ROOT/'blind_key.json').read_text());outpath=ROOT/'metrics_masked.json'
    out=json.loads(outpath.read_text()) if outpath.exists() else {}
    todo=[item for item in key.items() if item[0] not in out]
    with concurrent.futures.ProcessPoolExecutor(2) as pool:
        for code,r in pool.map(one,todo):
            if r is not None:out[code]=r;outpath.write_text(json.dumps(out,indent=2)+'\n')
    print('measured',len(out),'of',len(key),'clips; outputs still masked')
