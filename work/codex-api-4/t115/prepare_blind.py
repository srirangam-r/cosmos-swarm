import hashlib,json,pathlib,re,secrets,random,cv2,numpy as np,urllib.request

ROOT=pathlib.Path(__file__).parent
BASE='http://100.111.167.68:8030'
def collect():
    (ROOT/'clips').mkdir(exist_ok=True)
    records=[]
    for owner in ['ro-3','ro-api-3']:
        for j in json.load(urllib.request.urlopen(BASE+'/jobs?owner='+owner))['jobs']:
            if re.fullmatch(r'ms_pend(10|11)_mid[BTW]_s[1-8]',j['name']):
                records.append(j)
    byname={j['name']:j for j in records}
    assert len(byname)==48,len(byname)
    keypath=ROOT/'blind_key.json'
    if not keypath.exists():
        names=sorted(byname);random.Random(secrets.randbits(128)).shuffle(names)
        keypath.write_text(json.dumps({f'c{k+1:02}':name for k,name in enumerate(names)},indent=2)+'\n')
    key=json.loads(keypath.read_text())
    (ROOT/'queue_snapshot.json').write_text(json.dumps(records,indent=2))
    (ROOT/'blind').mkdir(exist_ok=True)
    made=[]
    for code,name in key.items():
        j=byname[name]
        if j['status']!='done':continue
        path=ROOT/'clips'/(name+'.mp4')
        if not path.exists():
            path.write_bytes(urllib.request.urlopen(BASE+'/jobs/'+j['id']+'/mp4').read())
            path.with_suffix('.json').write_text(json.dumps(j['sidecar'],indent=2))
        out=ROOT/'blind'/(code+'.jpg')
        if out.exists():continue
        cap=cv2.VideoCapture(str(path));fs=[]
        while True:
            ok,f=cap.read()
            if not ok:break
            fs.append(f)
        cap.release()
        ids=list(range(0,len(fs),8))
        if ids[-1]!=len(fs)-1:ids.append(len(fs)-1)
        sheet=np.full((240*((len(ids)+3)//4),416*4,3),32,np.uint8)
        for k,idx in enumerate(ids):
            f=cv2.resize(fs[idx],(416,240))
            cv2.putText(f,f'{code} f{idx}',(5,20),0,.55,(0,255,255),1)
            y,x=divmod(k,4);sheet[y*240:(y+1)*240,x*416:(x+1)*416]=f
        cv2.imwrite(str(out),sheet,[cv2.IMWRITE_JPEG_QUALITY,95]);made.append(code)
    print(json.dumps({'key_sha256':hashlib.sha256(keypath.read_bytes()).hexdigest(),'new_sheets':made,'n_sheets':len(list((ROOT/'blind').glob('*.jpg')))},indent=2))
if __name__=='__main__':collect()
