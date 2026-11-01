import json
base=json.loads(open('../cosmos-swarm/work/ro-1/cause_v5/jobs_v5.jsonl').readline())
F=base['prompt']
old="followed by a sequence of successive bounces with diminishing peak heights, before finally coming to rest on the plank."
assert old in F
def rep(s): return F.replace(old,s)
RULE="By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy and come to rest, staying completely still for the rest of the video."
arms={
'F':F,
'QT':rep("bounces only twice with rapidly diminishing heights, and comes to rest on the plank within about one and a half seconds, staying still for the rest of the video."),
'QTnc':rep("comes to rest on the plank within about one and a half seconds, staying still for the rest of the video."),
'CO':rep("bounces only twice with rapidly diminishing heights."),
'R':F+" "+RULE}
# verify QT equals ro-1's QT
for l in open('../cosmos-swarm/work/ro-1/cause_v5/jobs_v5.jsonl'):
    j=json.loads(l)
    if j['arm']=='QT': assert j['prompt']==arms['QT']; break
out=[]
for img,b in (('gauge_ball1_dd33_832x480.png','ball1'),('gauge_ball2_dd35_832x480.png','ball2')):
  for s in (31,32,33):
    for a,p in arms.items():
      j=dict(base); j.update(image=img,prompt=p,seed=s,arm=a,name=f"t138_{a}_{b}_s{s}",protocol="task138 QT-component ablation (prereg #3098, parent task 137)",extra_params={"client":"raj-api-3","task":138},arm_desc=a)
      j.pop('stated_duration_s',None); out.append(j)
open('jobs.jsonl','w').write("\n".join(json.dumps(j) for j in out)+"\n"); print(len(out))
