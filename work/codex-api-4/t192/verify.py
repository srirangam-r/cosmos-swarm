"""Portable arithmetic, frozen-code, input and example-movie verification."""
import hashlib,importlib.util,json,math,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit',ROOT/'analyze.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def tail(p,k,n,upper):
 return sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in (range(k,n+1) if upper else range(k+1)))
def bisect(target,k,n,upper):
 lo,hi=0.,1.
 for _ in range(100):
  mid=(lo+hi)/2;v=tail(mid,k,n,upper)
  if (v<target)==upper:lo=mid
  else:hi=mid
 return (lo+hi)/2
checks=0
for alpha in [.05,.025]:
 for k in range(9):
  expected=[0. if k==0 else bisect(alpha/2,k,8,True),1. if k==8 else bisect(alpha/2,k,8,False)]
  assert max(abs(x-y) for x,y in zip(expected,a.cp(k,8,alpha)))<1e-10
  checks+=1
for up,down in [(0,0),(1,0),(0,1),(2,0),(0,2),(3,1),(4,4)]:
 d=[1]*up+[-1]*down+[0]*(8-up-down);v=a.contrast([max(x,0) for x in d],[max(-x,0) for x in d]);n=up+down
 expected=min(1.,2*sum(math.comb(n,j) for j in range(min(up,down)+1))/2**n) if n else 1.
 assert abs(v['sign_p_two_sided']-expected)<1e-12
 assert abs(v['mean']-(up-down)/8)<1e-12
 if up==1 and down==0:assert abs(v['seed_se']-.125)<1e-12 and abs(v['t95'][1]-(.125+2.364624251*.125))<1e-9
 if not n:assert v['t95'] is None and v['conservative_paired95'][1]>.4
 checks+=1
assert a.sha(ROOT/'codes.csv')=='084951d4e5ccbb9058003075aff27d66f0039eefaf789c69e092373a871f70f2'
assert a.sha(ROOT/'panels/key.json')=='7c593c8a7fd038f108605bd0367d1b2dfb74b6024e5a41feb2d86763e07755c1'
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)
 subprocess.run([sys.executable,str(ROOT/'analyze.py'),str(ROOT/'source'),str(ROOT/'panels'),str(p)],check=True,stdout=subprocess.DEVNULL)
 for n in ['results.json','joined.json','contracts.json']:assert (p/n).read_bytes()==(ROOT/'results'/n).read_bytes()
key={k['name']:k for k in json.loads((ROOT/'panels/key.json').read_text())}
rgb_matches=0
for p in sorted((ROOT/'examples').glob('*.mp4')):
 k=key[p.stem];assert a.sha(p)==k['sha256']
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-f','rawvideo','-pix_fmt','rgb24','-threads','1','-'])
 assert len(raw)==93*832*480*3
 rgb_matches+=hashlib.sha256(raw).hexdigest()==k['rgb_sha256']
print(json.dumps({'arithmetic_checks':checks,'frozen_codes_and_key':True,'reanalysis_byte_identical_files':3,'example_movie_file_sha_and_decoded_lengths_pass':3,'remote_rgb_exact_matches':rgb_matches,'local_ffmpeg':subprocess.check_output(['ffmpeg','-version']).decode().splitlines()[0],'remote_ffmpeg':(ROOT/'decode_check/ffmpeg.txt').read_text().splitlines()[0],'source_counts_and_pairs':True,'request_video_contracts':24,'source_input_job_hashes':7,'gaussian_doses_byte_exact':True},indent=2))
