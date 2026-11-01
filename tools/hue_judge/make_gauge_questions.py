# HUE-format question sets (Yes = good) for GAUGE-style scenes: ball drop, pendulum, slope slide.
import json,sys
G=[("Visual Integrity","temporal stability","Throughout the video, does the video stay free of unnatural flickering?"),
   ("Visual Integrity","artifacts","Throughout the video, is the image clean, free of heavy noise, static or distortion?"),
   ("Visual Integrity","shot change","Throughout the video, does the video stay in one continuous shot without cuts to a different scene?"),
   ("Geometric Reasoning","camera stability","Throughout the video, does the camera stay static?"),
   ("Geometric Reasoning","position/motion","Throughout the video, do objects move smoothly and continuously rather than jumping between positions?"),
   ("Physical Laws","object permanence","Throughout the video, do the robot arm and the table stay present without appearing or disappearing?")]
S={
 "gauge_ball":[("Semantic Alignment","prompt attributes","At the start of the video, does a robot arm hold a black ball above a wooden plank?"),
   ("Physical Laws","physics","In the middle of the video, after the ball is released, does it fall downward?"),
   ("Physical Laws","physics","In the middle of the video, does the ball speed up as it falls?"),
   ("Physical Laws","collision/momentum","When the ball hits the plank, does it bounce up instead of passing through it?"),
   ("Physical Laws","causal order","Does the ball start falling only after the gripper releases it?"),
   ("Physical Laws","behavioral realism","Do the ball's bounces get lower each time until it comes to rest?"),
   ("Visual Integrity","deformation","Throughout the video, does the ball keep a round shape?")],
 "gauge_pend":[("Semantic Alignment","prompt attributes","Does the video show a pendulum with a ball on a rod hanging from a frame?"),
   ("Physical Laws","physics","Throughout the video, does the pendulum swing back and forth around its lowest point?"),
   ("Physical Laws","physics","Does the pendulum move fastest at the bottom of its swing and slow down at the ends?"),
   ("Physical Laws","behavioral realism","Does the pendulum keep swinging smoothly without stopping abruptly?"),
   ("Geometric Reasoning","geometry/contact","Throughout the video, does the rod stay attached to its pivot?"),
   ("Physical Laws","causal order","Does each swing follow from the previous one without sudden changes of direction mid-swing?"),
   ("Visual Integrity","deformation","Throughout the video, does the pendulum rod stay straight and rigid?")],
 "gauge_slope":[("Semantic Alignment","prompt attributes","Does the video show a wooden slope (inclined plank) on a table next to a robot arm?"),
   ("Physical Laws","physics","When an object is placed on the slope, does it slide down the incline rather than up?"),
   ("Physical Laws","physics","Does the sliding object speed up as it moves down the slope?"),
   ("Geometric Reasoning","geometry/contact","While sliding, does the object stay in contact with the slope surface?"),
   ("Physical Laws","causal order","Does the object begin to move only after it is placed or released?"),
   ("Physical Laws","collision/momentum","At the bottom, does the object stop or collide realistically instead of passing through the end stop?"),
   ("Visual Integrity","deformation","Throughout the video, do the plank and the sliding object keep their shapes?")],
}
out=[]
for k,qs in S.items():
    s={"sample_name":k,"prompt":""}
    for i,(c,sub,t) in enumerate(qs+G,1):
        s[f"question_{i}"]=f"[{c}][{sub}] {t}"; s[f"question_{i}_choices"]=["Yes","No","Unclear"]
    out.append(s)
json.dump({"samples":out},open(sys.argv[1] if len(sys.argv)>1 else "gauge_questions.json","w"),indent=1)
