"""Download original public GAUGE development videos/mocap; no sealed data."""
from pathlib import Path
import concurrent.futures, requests, hashlib, json, sys, time
root=Path(sys.argv[1]); root.mkdir(parents=True,exist_ok=True)
revision=json.loads((Path(__file__).parent/'dataset_revision.json').read_text())['sha']
base=f'https://huggingface.co/datasets/InternRobotics/GAUGE-Dataset/resolve/{revision}/data/rigid/pendulum'
manifest=Path(__file__).parent/'source_manifest.json'
expected={(e['id'],e['kind']):e['sha256'] for e in json.loads(manifest.read_text())} if manifest.exists() else {}
def one(p):
 i,kind,ext=p; path=root/f'{i}.{ext}'; u=f'{base}/{kind}/{i}.{ext}'
 if not path.exists():
  r=requests.get(u,stream=True,timeout=120); r.raise_for_status()
  tmp=path.with_suffix(path.suffix+'.part')
  with tmp.open('wb') as f:
   for c in r.iter_content(1024*1024): f.write(c)
  tmp.rename(path)
 rec={'id':i,'kind':kind,'url':u,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 if expected: assert rec['sha256']==expected[(i,kind)],(i,kind,'source hash mismatch')
 print(i,kind,rec['bytes'],flush=True); return rec
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 out=list(ex.map(one,[(i,k,e) for i in range(1,21) for k,e in [('json','json'),('video','mp4')]]))
(root/'manifest.json').write_text(json.dumps(out,indent=2)+'\n')
