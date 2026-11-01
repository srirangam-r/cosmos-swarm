"""Secondary unchanged planted-PASS measurement on all source-gate-passing clips.

python measure_existing.py <task198 clips dir>
Native QC was frozen before gate selection was opened. All three source
passes are retained, including native-U Q07. No revised exclusions.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'source'))
import measure_pend as mp, trk

def default(x):
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)

def main():
    clips=Path(sys.argv[1]);out=ROOT/'measurement';out.mkdir(exist_ok=True)
    gates=json.loads((ROOT/'source/gates_fresh.json').read_text())
    key=json.loads((ROOT/'key.json').read_text());records={}
    for ident,k in key.items():
        if not gates[k['name']]['PASS']:continue
        path=clips/(k['name']+'.mp4')
        if not path.exists():path=clips/(ident+'.mp4')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==k['sha256']
        F=trk.load(str(path));assert F.shape==(93,480,832,3)
        r=mp.measure(F,24,keep_track=True)
        mp.qc(F,r,str(out/f'{ident}.png'))
        records[ident]=r
        print(ident, r['flag'],r['period_s'],r['period_ci95'],flush=True)
    (out/'results.json').write_text(json.dumps(records,indent=2,default=default,allow_nan=False)+'\n')

if __name__=='__main__':main()
