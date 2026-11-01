"""Verify self-contained published evidence, not physical amplitude validity."""
from pathlib import Path
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from scipy.integrate import quad
import audit

HERE=Path(__file__).resolve().parent

def main():
    out=json.loads((HERE/'results.json').read_text())
    checks=[]
    def check(name,condition):
        checks.append({'name':name,'passed':bool(condition)})
        assert condition,name
    for name,digest in out['source_sha256'].items():
        check('source hash '+name,hashlib.sha256((HERE/'source'/name).read_bytes()).hexdigest()==digest)
    check('all analysis checks passed',all(r['passed'] for r in out['checks']))
    check('six unique selected seeds',len({r['seed'] for r in out['gate_rows']})==6)
    for angle in [1.,30.,60.,90.,120.,150.,179.]:
        m=math.sin(math.radians(angle)/2)**2
        q=2/math.pi*quad(lambda u:1/math.sqrt(1-m*math.sin(u)**2),0,math.pi/2,
                         epsabs=1e-11,epsrel=1e-11)[0]
        check('ODE vs independent quadrature '+str(angle),abs(audit.factor(angle)-q)<1e-9)
    for amplitude in [20.,51.,80.]:
        ts=np.arange(93)/24
        record={'T':1.5,'series':{'t':ts.tolist(),'theta':(amplitude*np.sin(2*np.pi*ts/1.5)).tolist()}}
        got=audit.extrema_amplitude(record,1)
        check('sampled synthetic extrema '+str(amplitude),abs(got['amplitude_deg']-amplitude)<1e-10 and got['pair_count']>=2)
    # Check the stated orthographic envelope implication, including >90 degrees.
    for c in [.001,.1,.5,1.]:
        theta=np.linspace(.001,179.999,2000)
        alpha=np.degrees(np.arctan2(c*np.sin(np.radians(theta)),np.cos(np.radians(theta))))
        check('projection conditional cap '+str(c),bool(np.all(theta<=np.maximum(90.,alpha)+1e-12)))
    native=out['native_QC_subset']['rows']
    check('previous native subset IDs',sorted(x['id'] for x in native)==['Q05','Q08'])
    check('13 broader seed means',len(out['broader_fit_A0']['seed_means'])==13)
    check('17 broader clips',out['broader_fit_A0']['clip_weighted']['n']==17)
    with tempfile.TemporaryDirectory(prefix='t219-verify-') as tmp:
        root=Path(tmp)
        shutil.copyfile(HERE/'audit.py',root/'audit.py')
        shutil.copytree(HERE/'source',root/'source')
        run=subprocess.run([sys.executable,str(root/'audit.py')],cwd=root,capture_output=True,text=True)
        check('standalone replay exits zero',run.returncode==0)
        check('standalone results byte identical',(root/'results.json').read_bytes()==(HERE/'results.json').read_bytes())
    manifest=HERE/'SHA256SUMS'
    if manifest.exists():
        for line in manifest.read_text().splitlines():
            digest,name=line.split('  ',1)
            check('manifest '+name,hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest)
    report={'scope':'software/source/model checks, not referee amplitude validation',
            'passed_checks':len(checks),'checks':checks}
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed_checks':len(checks)}))

if __name__=='__main__':
    main()
