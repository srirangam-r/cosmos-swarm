"""Check frozen bytes, publication integrity, independent arithmetic and replay."""
from pathlib import Path
import hashlib,json,math,statistics,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parent

def main():
    checks=0
    manifest=ROOT/'SHA256SUMS'
    if manifest.exists():
        for line in manifest.read_text().splitlines():
            h,name=line.split('  ',1)
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
            checks+=1
    expected={'measure_pend.py':'ea671320010ff80ac5f9dce355590bc3e1952eeb62ad240c47e7fd783f07d120',
              'trk.py':'4de7b99dd38677a707e765d2b44d305b4fbade61b0e9e425f1dbad41549eaf2e'}
    for n,h in expected.items():assert hashlib.sha256((ROOT/'source'/n).read_bytes()).hexdigest()==h;checks+=1
    with tempfile.TemporaryDirectory() as tmp:
        output=Path(tmp)/'results.json'
        subprocess.run([sys.executable,str(ROOT/'analyze.py'),str(output)],check=True,stdout=subprocess.DEVNULL)
        assert output.read_bytes()==(ROOT/'results.json').read_bytes();checks+=1
    result=json.loads((ROOT/'results.json').read_text())
    for summary,ids in [('independent_period_all_source_passes',['Q05','Q07','Q08']),('independent_period_native_intersection',['Q05','Q08'])]:
        rows={r['id']:r for r in result['rows']}
        a=[rows[i]['planted_pass_tool']['period_s'] for i in ids]
        v=result[summary]
        assert abs(statistics.mean(a)-v['mean'])<1e-14;checks+=1
        assert abs(statistics.stdev(a)/math.sqrt(len(a))-v['seed_se'])<1e-14;checks+=1
        assert abs(v['mean']/result['reference_tool_s']-v['ratio'])<1e-14;checks+=1
    key=json.loads((ROOT/'key.json').read_text());contracts=json.loads((ROOT/'video_contracts.json').read_text())
    assert set(key)==set(contracts);checks+=1
    assert len({v['first_bgr_sha256'] for v in contracts.values()})==1;checks+=1
    for ident,c in contracts.items():
        assert c['sha256']==key[ident]['sha256'] and c['frames']==93 and c['fps']==24;checks+=1
    for path in (ROOT/'examples').glob('*.mp4'):
        ident=path.stem;assert hashlib.sha256(path.read_bytes()).hexdigest()==key[ident]['sha256'];checks+=1
    for row in result['rows']:
        if 'planted_pass_tool' not in row:continue
        r=row['planted_pass_tool']
        ok=r['n_halfcycles']>=3 and r['r2']>.8 and abs(r['period_s']-r['period_zc_s'])/r['period_s']<.05 and r['frac_tracked']>=.9
        assert ok and r['flag']=='ok';checks+=1
    print('PASS',checks,'integrity, source, arithmetic, contract and byte-replay checks')

if __name__=='__main__':main()
