#!/usr/bin/env python3
"""Independent exact rational OLS oracle and actual Node CLI acceptance.

All data are synthetic. No media, network, GPU, referee or reader is used.
"""
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent


def node(code, payload=None):
    result = subprocess.run(['node', '-e', code], cwd=ROOT,
                            input=json.dumps(payload), text=True,
                            capture_output=True, check=True)
    return json.loads(result.stdout)


def near(a, b):
    return a == b if a is None or b is None else math.isclose(a, b, rel_tol=2e-12, abs_tol=2e-12)


def verify():
    source_messages = json.loads((ROOT/'board_provenance.json').read_text())['messages']
    source_checks = []
    for message_id, name in [(5951,'dial_analysis.cjs'),(5954,'test_dial_analysis.cjs')]:
        body = next(m['body'] for m in source_messages if m['id']==message_id)
        exact = body.split('```javascript\n',1)[1].split('\n```',1)[0].rstrip('\n')+'\n'
        actual = (ROOT/name).read_bytes()
        assert actual == exact.encode(), name
        source_checks.append({'message_id':message_id,'file':name,
                              'sha256':hashlib.sha256(actual).hexdigest(),'exact':True,
                              'match_policy':'Code block with trailing LF normalized to one; no executable changes'})
    regression_run = subprocess.run(['node','test_dial_analysis.cjs'], cwd=ROOT,
                                    capture_output=True, text=True, check=True)
    (ROOT/'node_regression.json').write_text(regression_run.stdout)
    regression = json.loads(regression_run.stdout)
    assert regression['checks']==121

    x = [F(3,5),F(9,10),F(59,50),F(3,2),F(2)]
    rng = random.Random(3015951)
    ys = [[F(rng.randrange(1,2001),500) for _ in x] for _ in range(100)]
    ys += [[F(6,5)]*5]
    fits = node("const fs=require('fs'); const {fit}=require('./dial_analysis.cjs'); const a=JSON.parse(fs.readFileSync(0,'utf8')); console.log(JSON.stringify(a.map(v=>fit(v.x,v.y))));",
                [{'x':list(map(float,x)),'y':list(map(float,y))} for y in ys])
    max_abs = 0.0
    oracle_checks = 0
    for y, actual in zip(ys,fits):
        # Raw-sum normal equations in exact Fraction arithmetic, independent
        # of JavaScript's centered floating-point cross-product implementation.
        n = len(x)
        sx, sy = sum(x), sum(y)
        sxx, sxy, syy = sum(v*v for v in x), sum(a*b for a,b in zip(x,y)), sum(v*v for v in y)
        b = (n*sxy-sx*sy)/(n*sxx-sx*sx)
        a = (sy-b*sx)/n
        residual = sum((yy-a-b*xx)**2 for xx,yy in zip(x,y))
        total = syy-sy*sy/n
        errors = [yy-xx for xx,yy in zip(x,y)]
        expected = {'slope':float(b),'intercept_s':float(a),
                    'r2':None if total==0 else float(1-residual/total),
                    'bias_s':float(sum(errors)/n),
                    'rmse_to_command_s':math.sqrt(float(sum(e*e for e in errors)/n)),
                    'mean_abs_relative_error':float(sum(abs(e)/xx for e,xx in zip(errors,x))/n)}
        for key,value in expected.items():
            assert near(actual[key],value), (key,actual[key],value)
            oracle_checks += 1
            if value is not None: max_abs=max(max_abs,abs(value-actual[key]))

    subprocess.run(['node','write_examples.cjs'], cwd=ROOT, check=True)
    checks = 0
    for name, accepted, full in [('empty',0,False),('unity',30,True),
                                  ('twice_command',30,True),('missing_middle',29,False)]:
        input_file = ROOT/'examples'/f'{name}_input.json'
        proc = subprocess.run(['node','analyze.cjs',str(input_file)], cwd=ROOT,
                              capture_output=True,text=True,check=True)
        report=json.loads(proc.stdout)
        assert report==json.loads((ROOT/'examples'/f'{name}_report.json').read_text())
        assert report['planned']==30 and report['qc_accepted']==accepted
        assert report['all_slots_pass_qc']==full
        assert (report['tools']['acf_s']['full_grid_slope_summary'] is not None)==full
        assert report['data_kind']=='synthetic'
        assert report['input_sha256']==hashlib.sha256(input_file.read_bytes()).hexdigest()
        checks+=6

    unity=json.loads((ROOT/'examples/unity_input.json').read_text())
    invalid=[]
    def copy(): return json.loads(json.dumps(unity))
    doc=copy(); doc['data_kind']='model_improvement'; invalid.append(('invalid_kind',doc))
    doc=copy(); del doc['data_kind']; invalid.append(('missing_kind',doc))
    doc=copy(); doc['plan']=[p for p in doc['plan'] if p['scene']!='syntheticC']; doc['observations']=[]; invalid.append(('two_scenes',doc))
    doc=copy(); doc['plan']=[p for p in doc['plan'] if p['seed']==1]; doc['observations']=[]; invalid.append(('one_seed',doc))
    doc=copy(); doc['observations'].append(doc['observations'][0]); invalid.append(('duplicate_row',doc))
    doc=copy(); doc['observations'][0]['id']='unknown'; invalid.append(('unknown_row',doc))
    doc=copy(); doc['plan'][0]['target_s']=.7; invalid.append(('altered_plan',doc))
    doc=copy(); doc['observations']=''; invalid.append(('bad_rows',doc))
    with tempfile.TemporaryDirectory(prefix='cli-check-',dir=ROOT) as tmp:
        for label,doc in invalid:
            p=Path(tmp)/f'{label}.json'; p.write_text(json.dumps(doc))
            proc=subprocess.run(['node','analyze.cjs',str(p)],cwd=ROOT,capture_output=True,text=True)
            assert proc.returncode==2 and proc.stdout=='' and proc.stderr.startswith('dial analysis: '), label
            checks+=1
        p=Path(tmp)/'malformed.json'; p.write_text('{')
        for args in [[],[str(p)],['a','b']]:
            proc=subprocess.run(['node','analyze.cjs',*args],cwd=ROOT,capture_output=True,text=True)
            assert proc.returncode==2 and proc.stdout==''
            checks+=1
    return {'data_kind':'synthetic_software_only','exact_source_checks':source_checks,
            'original_regression':regression,'independent_rational_fixtures':len(ys),
            'independent_metric_comparisons':oracle_checks,'max_abs_metric_error':max_abs,
            'cli_acceptance_checks':checks,'node_version':subprocess.check_output(['node','--version'],text=True).strip(),
            'no_model_or_media_measurement':True,'no_planted_validation':True}


if __name__=='__main__':
    result=verify()
    raw=json.dumps(result,indent=2)+'\n'
    (ROOT/'verification.json').write_text(raw)
    print(raw,end='')
