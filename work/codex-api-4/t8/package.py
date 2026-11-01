"""Collect immutable source contracts and portable small evidence files."""
from pathlib import Path
import json,shutil,hashlib,sys,platform,subprocess
import numpy,scipy,cv2
base=Path(__file__).resolve().parent;repo=base.parents[2];raw=Path(sys.argv[1]);out=base/'output'
shutil.copyfile(raw/'manifest.json',base/'source_manifest.json')
(base/'source').mkdir(exist_ok=True)
for name in ['tools/trk_ballfall/measure_pend.py','tools/trk_ballfall/trk.py','tools/trk_ballfall/referee_result_pend_v1.json']:
 shutil.copyfile(repo/name,base/'source'/Path(name).name)
for i in range(1,21):
 r=json.loads((out/'results.json').read_text())[str(i)]
 source={e['kind']:e for e in json.loads((base/'source_manifest.json').read_text()) if e['id']==i}
 sidecar={'kind':'real GAUGE development-video derivative, measurement only','source':source,'dataset_revision':json.loads((base/'dataset_revision.json').read_text()),'transform':'first300containerframes; content-dedup by 0.1median pairMAE; nominal25Hz;832x468INTER_AREA+6pxblackpadding;distinct frames93:186','measurement_source':'unencoded BGR float32 frames; published mp4v is review derivative only','size':'832x480','num_frames':93,'fps':25,'last_minus_first_frame_s':92/25,'reference_window_s':r['reference_window_s']}
 (out/f'clips/real_{i:02}.json').write_text(json.dumps(sidecar,indent=2)+'\n')
versions={'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__,'opencv':cv2.__version__,'note':'System SciPy warns its declared NumPy range excludes1.26.4; four analytic reference checks and exact published-real10 numerical comparison pass; no optimizer failures recorded.'}
(base/'versions.json').write_text(json.dumps(versions,indent=2)+'\n')
files=[]
for p in sorted(base.rglob('*')):
 if not p.is_file() or '__pycache__' in str(p) or p.name=='SHA256SUMS':continue
 files.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(base)}')
(base/'SHA256SUMS').write_text('\n'.join(files)+'\n')
print('files',len(files),'bytes',sum(p.stat().st_size for p in base.rglob('*') if p.is_file()),'maxfile',max(p.stat().st_size for p in base.rglob('*') if p.is_file()))
