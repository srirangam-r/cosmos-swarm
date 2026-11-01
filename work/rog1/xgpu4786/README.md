# rog1: replication of #4786 (CPU noise -> same clip on any GPU type) on other GPUs and another scene
Input: real GAUGE wood-slope frame (copy of work/ro-agy1/task140_rule_r_devscenes/inputs/frame(wood).png, sha256 7745499b...), t140 base slope prompt.
832x480, 93 f, 24 fps, 35 steps, CFG 6, flow_shift 10 (Karras on board servers). Seeds 301-303, extra_params.noise={"device":"cpu"}
on int-a100, puget21, laptop5090 (GPU types not in #4786 or task 239), plus cuda-noise s301 controls on int-a100 and puget21.
analyze_xgpu.py and its decision rule were committed before any clip was fetched. Queue owner rog1, ids 133754-*/133755-*/133756-*.
