#!/usr/bin/env python3
"""Verify frozen inputs/source copies; byte-replay every panel and analysis output."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):return subprocess.check_output([sys.executable,*map(str,args)],text=True).strip()
def main():
 checks=[]
 assert sha(ROOT/'codes_frozen.csv')=='9c25b235239467d07ade76febb56ea64260327139e8e128252c1fb1f42d51117';checks.append('frozen codes hash')
 assert sha(ROOT/'key.json')=='5eff85bdddfd216fcbe06075b0d2abecffe684c95f46513555c708f8c8c273cc';checks.append('pre-view key hash')
 for item in json.loads((ROOT/'source_manifest.json').read_text()):
  assert sha(ROOT/item['copy'])==item['sha256'];checks.append('source copy '+item['copy'])
 assert (ROOT/'source/server_prompt_switch.py').read_bytes()==(ROOT/'source/executed_server_prompt_switch.py').read_bytes();checks.append('claimed executed source equals original source')
 for item in json.loads((ROOT/'source_locations.json').read_text()):
  assert sha(REPO/item['repo_path'])==item['sha256'];checks.append('published original '+item['name'])
 with tempfile.TemporaryDirectory(prefix='t209-replay-') as tmp:
  tmp=Path(tmp);clone=tmp/'package';clone.mkdir();shutil.copytree(ROOT/'source',clone/'source')
  for name in ['prepare.py','analyze.py','audit_hook.py','codes_frozen.csv','key.json']:shutil.copy2(ROOT/name,clone/name)
  clips=tmp/'originals';clips.mkdir()
  for item in json.loads((ROOT/'source_locations.json').read_text()):(clips/(item['name']+'.mp4')).symlink_to((REPO/item['repo_path']).resolve())
  run([clone/'prepare.py',clips,tmp/'hidden'])
  assert (tmp/'hidden/key.json').read_bytes()==(ROOT/'key.json').read_bytes();checks.append('masked key byte replay')
  for p in (ROOT/'qc').iterdir():
   assert p.read_bytes()==(clone/'qc'/p.name).read_bytes(),p.name;checks.append('panel byte replay '+p.name)
  run([clone/'analyze.py',clips]);run([clone/'audit_hook.py'])
  for name in ['results.json','table.csv','hook_audit.json']:
   assert (ROOT/name).read_bytes()==(clone/name).read_bytes(),name;checks.append('analysis byte replay '+name)
 # Independently check arm counts and full-control rows.
 out=json.loads((ROOT/'results.json').read_text())
 for arm,expected in {'F':(0,2,0),'QT':(1,0,1),'SWfull':(1,0,1),'SWe3':(0,2,0),'SWe7':(0,2,0),'SWl7':(1,1,0),'SWl17':(0,2,0)}.items():
  assert tuple(out['counts'][arm][k] for k in 'YNU')==expected;checks.append('arm count '+arm)
 assert all(r['present_end']=='Y' for r in out['rows']);checks.append('all14 end-present codes')
 q2=next(r for r in out['rows'] if r['id']=='Q02');assert q2['arm']=='SWe7' and q2['seed']==5 and q2['stable_size']=='N';checks.append('named artifact join')
 report=dict(n_checks=len(checks),checks=checks,source_audit_checks=len(json.loads((ROOT/'hook_audit.json').read_text())['checks']),contract_analysis_checks=out['n_checks'])
 (ROOT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'}))

if __name__=='__main__':main()
