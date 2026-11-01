import json, sys
sys.argv=['x']
import make_simproxy as m
P=json.loads(open('jobs_simproxy.jsonl').readline())
prompt=P['prompt']; jobs=[]
for pn in ['pend10','pend11']:
    for per in [0.6,0.9,1.186,1.5,2.0]:
        tag=f'{int(per*1000)}'
        fn=f'dial/dp_{pn}_P{tag}.mp4'; m.make(pn,per,out=fn)
        for s in [1,2]:
            jobs.append(dict(name=f'dial_{pn}_P{tag}_s{s}',prompt=prompt,image=P['image'].replace('pend10_mid_f93',{'pend10':'pend10_mid_f93','pend11':'pend11_mid_f81'}[pn]),
              width=832,height=480,num_frames=93,fps=24,steps=35,guidance=6.0,flow_shift=10.0,seed=s,negative_prompt='',
              files=[f'/home/rohith/swarm-work/ro-3/midswing/{fn}'],
              extra_params={'noise':{'device':'cpu'},'latent':{'ref':f'dp_{pn}_P{tag}.mp4','init':'noised','start_step':19}}))
open('jobs_dial.jsonl','w').write('\n'.join(json.dumps(j) for j in jobs)+'\n'); print(len(jobs))
