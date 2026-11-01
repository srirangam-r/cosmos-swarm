"""Build task 253's frozen controls (#5178); do not submit before provenance gate."""
import json
from pathlib import Path

template = ("Static camera view: a simple pendulum, a thin rigid rod with a bright {color} metal ball at its tip, hangs from a horizontal axle mounted between two vertical posts on a table, in front of a plain grey wall. The pendulum swings back and forth {speed}, each full back-and-forth swing taking about {period}, under gravity, for the whole video.")
prompts = {
    "A": template.format(color="blue", speed="slowly", period="three seconds"),
    "B": template.format(color="red", speed="slowly", period="three seconds"),
    "C": template.format(color="blue", speed="quickly", period="half a second"),
}
jobs = []
for seed in (201, 202, 203):
    base = dict(image=None, negative_prompt=None, width=832, height=480,
                num_frames=93, fps=24, steps=35, guidance=6.0,
                flow_shift=10.0, seed=seed)
    for p in prompts:
        jobs.append(dict(base, name=f"t253_s{seed}_plain_{p}", prompt=prompts[p],
                         extra_params={"noise": {"device": "cpu"}}))
    for contrast in ("AB", "AC"):
        a, b = contrast
        for source, target in ((a, a), (b, b), (a, b), (b, a)):
            jobs.append(dict(base, name=f"t253_s{seed}_{contrast}_{source}to{target}",
                             prompt=prompts[source], extra_params={
                                 "noise": {"device": "cpu"},
                                 "internals": {"prompt_switch": {
                                     "prompt": prompts[target], "step_range": [0, 35]}}}))
assert len(jobs) == 33 and len({j["name"] for j in jobs}) == 33
assert all(j["extra_params"]["noise"]["device"] == "cpu" for j in jobs)
assert all(j["image"] is None and j["negative_prompt"] is None for j in jobs)
Path(__file__).with_name("feasibility.jsonl").write_text(
    "".join(json.dumps(j, sort_keys=True) + "\n" for j in jobs))
