"""Independent same-data arithmetic and intervention audit, after QC freeze."""
import argparse,csv,hashlib,json,math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageFilter
from scipy.stats import beta,binomtest,t

SEEDS=[1,2,3,4,11,12,13,14]
ARMS=['b0','b05','b15']
FIELDS=['hover','fall','clean_fall','clone','morph','holder_redrawn','hover_strict','clean_strict','clean_lenient']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def cp(k,n,alpha=.05):
    return [0. if k==0 else float(beta.ppf(alpha/2,k,n-k+1)),1. if k==n else float(beta.ppf(1-alpha/2,k+1,n-k))]
def contrast(a,b):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);d=a-b;n=len(d)
    if not n:return {'n':0}
    mean=float(d.mean());se=float(d.std(ddof=1)/math.sqrt(n)) if n>1 else None
    up=int((d>0).sum());down=int((d<0).sum());nd=up+down
    rng=np.random.default_rng(192024)
    boot=d[rng.integers(0,n,(40000,n))].mean(axis=1)
    # Two 97.5% marginal CP intervals give >=95% simultaneous coverage
    # by the union bound; subtract bounds for the paired mean difference.
    ub=cp(up,n,.025);db=cp(down,n,.025)
    return {'n':n,'delta':d.tolist(),'mean':mean,'seed_se':se,
            'zero_sample_variance':bool(se==0),
            't95':[max(-1.,mean-float(t.ppf(.975,n-1))*se),min(1.,mean+float(t.ppf(.975,n-1))*se)] if n>1 and se>0 else None,
            'bootstrap95':np.quantile(boot,[.025,.975]).tolist(),
            'bootstrap_warning':'Discrete empirical support; zero-width/one-direction intervals are not equivalence bounds',
            'conservative_paired95':[ub[0]-db[1],ub[1]-db[0]],
            'up':up,'down':down,'ties':n-nd,
            'sign_p_two_sided':float(binomtest(up,nd,.5).pvalue) if nd else 1.,
            'sign_p_increase':float(binomtest(up,nd,.5,alternative='greater').pvalue) if nd else 1.,
            'sign_p_decrease':float(binomtest(down,nd,.5,alternative='greater').pvalue) if nd else 1.,
            'up_rate_cp95':cp(up,n),'down_rate_cp95':cp(down,n)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('panels',type=Path);ap.add_argument('out',type=Path)
    z=ap.parse_args();s=z.source;o=z.out;o.mkdir(parents=True,exist_ok=True)
    key=json.loads((z.panels/'key.json').read_text());assert len(key)==24
    ours={r['id']:r for r in csv.DictReader((Path(__file__).parent/'codes.csv').open())}
    source=json.loads((s/'codes_blur.json').read_text())
    blind=json.loads((s/'codes_blind.json').read_text());bk=json.loads((s/'blind_key.json').read_text())
    assert len(source)==len(bk)==len(blind)==24
    assert all(source[n]==blind[b] for n,b in bk.items())
    frozen={line.split()[1]:line.split()[0] for line in (s/'codes_blind.FROZEN.sha256').read_text().splitlines()}
    assert all(sha(s/n)==h for n,h in frozen.items())
    for v in source.values():
        v['hover_strict']=int(v['hover'] and not v['drift_up'])
        v['clean_strict']=int(v['clean_fall'] and not v['borderline'])
        v['clean_lenient']=int(v['clean_fall'] or v['borderline'] and v['fall'])
    totals={a:{f:sum(source[f'hrb_{a}_s{i}'][f] for i in SEEDS) for f in FIELDS} for a in ARMS}
    paired={a:{f:contrast([source[f'hrb_{a}_s{i}'][f] for i in SEEDS],[source[f'hrb_b0_s{i}'][f] for i in SEEDS]) for f in FIELDS} for a in ARMS[1:]}
    reported=json.loads((s/'results_blur.json').read_text())
    assert totals==reported['totals']
    for a,fs in reported['paired_vs_b0'].items():
        for f,v in fs.items():
            assert paired[a][f]['up']==v['up'] and paired[a][f]['down']==v['down']
            assert round(paired[a][f]['sign_p_two_sided'],4)==v['sign_p_two_sided']
    joined=[]
    for k in key:
        name=k['name'];a=name.split('_')[1];seed=int(name.split('_s')[1]);r=ours[k['id']]
        joined.append({**k,'arm':a,'seed':seed,'independent':r,'author':source[name]})
    qcs={a:{f:{v:sum(r['independent'][f]==v for r in joined if r['arm']==a) for v in ['Y','N','U']} for f in ['hover','original_descends','clean_fall','clone']} for a in ARMS}
    independent_pairs={}
    for a in ARMS[1:]:
        independent_pairs[a]={}
        for f in ['hover','clean_fall','clone','original_descends']:
            rs={r['seed']:r['independent'][f] for r in joined if r['arm']==a}
            base={r['seed']:r['independent'][f] for r in joined if r['arm']=='b0'}
            valid=[i for i in SEEDS if rs[i]!='U' and base[i]!='U']
            independent_pairs[a][f]={'included_seeds':valid,**contrast([rs[i]=='Y' for i in valid],[base[i]=='Y' for i in valid])}
    agreement={}
    for f in ['hover','clean_fall','clone']:
        valid=[r for r in joined if r['independent'][f]!='U']
        bad=[{'id':r['id'],'name':r['name'],'independent':r['independent'][f],'author':r['author'][f]} for r in valid if (r['independent'][f]=='Y')!=bool(r['author'][f])]
        agreement[f]={'certain_n':len(valid),'agree':len(valid)-len(bad),'disagreements':bad,'unknown_n':24-len(valid)}
    jobs={}
    for gp in sorted(s.glob('jobs_blur_gpu*.jsonl')):
        for line in gp.read_text().splitlines():
            j=json.loads(line);assert j['name'] not in jobs;jobs[j['name']]=j
    assert len(jobs)==24
    settings={'width':832,'height':480,'num_frames':93,'fps':24,'steps':35,'guidance':6.,'flow_shift':10.}
    contracts=[]
    prompt=None
    for k in key:
        name=k['name'];m=json.loads((s/'clips_blur'/(name+'.json')).read_text());j=jobs[name]
        assert all(m[x]==j[x]==v for x,v in settings.items())
        assert m['seed']==j['seed']==int(name.split('_s')[1])
        assert m['image']==j['image']
        if prompt is None:prompt=j['prompt']
        assert m['prompt']==j['prompt']==prompt and not m.get('negative_prompt')
        assert k['frames']==93 and k['fps']==24 and k['shape']==[480,832,3]
        contracts.append({'id':k['id'],'name':name,'seed':m['seed'],'endpoint':m['endpoint'],'model_declaration':m['model'],'image_basename':Path(m['image']).name,'server_clip_id':m['server_clip_id']})
    inputnames={'b0':'v8_A.png','b05':'x_mineA_v8_blur0.5.png','b15':'x_mineA_v8_blur1.5.png'}
    baseim=Image.open(s/'inputs'/inputnames['b0']).convert('RGB');ba=np.asarray(baseim)
    dose={}
    for a,n in inputnames.items():
        im=Image.open(s/'inputs'/n).convert('RGB');arr=np.asarray(im);gray=cv2.cvtColor(arr,cv2.COLOR_RGB2GRAY)
        sigma={'b0':0.,'b05':.5,'b15':1.5}[a]
        expect=np.asarray(baseim.filter(ImageFilter.GaussianBlur(sigma))) if sigma else ba
        cvexpect=cv2.GaussianBlur(ba,(0,0),sigma) if sigma else ba
        dose[a]={'name':n,'sha256':sha(s/'inputs'/n),'shape':list(arr.shape),'laplacian_variance':float(cv2.Laplacian(gray,cv2.CV_64F).var()),'mae_from_b0':float(np.abs(arr.astype(float)-ba).mean()),'matches_Pillow_GaussianBlur':bool(np.array_equal(arr,expect)),'max_error_from_Pillow_blur':int(np.abs(arr.astype(int)-expect).max()),'matches_cv2_GaussianBlur':bool(np.array_equal(arr,cvexpect))}
        assert np.array_equal(arr,cvexpect)
    for n in ['x_mineA_v8_f0proxy.png','x_t139A_ball1_f0proxy.png']:
        arr=np.asarray(Image.open(s/'inputs'/n).convert('RGB'));dose[n]={'sha256':sha(s/'inputs'/n),'laplacian_variance':float(cv2.Laplacian(cv2.cvtColor(arr,cv2.COLOR_RGB2GRAY),cv2.CV_64F).var())}
    relevant=set(inputnames.values())|{'x_mineA_v8_f0proxy.png','x_t139A_ball1_f0proxy.png'}
    filechecks=[]
    for line in (s/'SHA256SUMS').read_text().splitlines():
        h,n=line.split(maxsplit=1)
        if n.startswith('jobs_blur_') or Path(n).name in relevant:
            assert sha(s/n)==h;filechecks.append(n)
    assert len(filechecks)==7
    endpointpairs={a:sum(next(c for c in contracts if c['name']==f'hrb_{a}_s{i}')['endpoint']==next(c for c in contracts if c['name']==f'hrb_b0_s{i}')['endpoint'] for i in SEEDS) for a in ARMS[1:]}
    result={'source_counts':totals,'source_paired':paired,'independent_counts':qcs,'independent_paired_complete_case':independent_pairs,'agreement_operational_definitions_differ':agreement,'input_dose':dose,'exact_endpoint_matched_pairs':endpointpairs,'source_code_hashes_verified':frozen,'source_input_job_hashes_verified':filechecks,'source_blind_join_pass':True,'request_video_contracts_pass':24,'prompt':prompt,'settings':settings,'caveats':['Same24 clips, one input, no fresh seeds','Unvalidated partially masked independent LLM coding, U excluded only with denominators shown','Independent clean_fall requires whole-clip single identity; source first-descent convention differs','No sigma/checkpoint/initial tensor capture; sampler Karras/ignored shift from source report, not instrumented here','Intervals descriptive under exchangeable seeds, not scene generalization or equivalence','Pixel softness does not isolate all aspects of image or latent conditioning']}
    dump(o/'results.json',result);dump(o/'joined.json',joined);dump(o/'contracts.json',contracts)
    print(json.dumps({'source_counts':totals,'independent_counts':qcs,'agreement':agreement,'dose':dose,'endpoints':endpointpairs},indent=2))

if __name__=='__main__':main()
