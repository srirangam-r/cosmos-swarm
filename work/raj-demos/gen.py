import json, subprocess, threading
from pathlib import Path
PROMPT = Path("/home/swarm/e6/pend_base.txt").read_text().strip()
def post(url, name, step, seed):
    if Path(f"{name}.mp4").exists(): return
    extra = {"noise": {"device": "cpu"}, "latent": {"ref": "proxy_phys.mp4", "init": "noised", "start_step": step}}
    cmd = ["curl", "-s", "-o", f"{name}.mp4", "-D", f"{name}.headers", "-w", "%{http_code}", "--max-time", "3000", "-X", "POST",
           f"{url}/v1/videos/sync", "-F", f"prompt={PROMPT}", "-F", "num_frames=93", "-F", "fps=24", "-F", "num_inference_steps=35",
           "-F", "guidance_scale=6", "-F", f"seed={seed}", "-F", "input_reference=@/home/swarm/e6/out/f0_10.png",
           "-F", f"extra_params={json.dumps(extra)}", "-F", "internals_files=@proxy_phys.mp4"]
    code = subprocess.run(cmd, capture_output=True, text=True).stdout.strip(); print(name, code, flush=True)
    cid = [l.split(":", 1)[1].strip() for l in Path(f"{name}.headers").read_text().splitlines() if l.lower().startswith("x-clip-id")]
    if cid: subprocess.run(["curl", "-s", "-o", f"{name}.server.json", f"{url}/v1/sidecars/{cid[0]}"])
jobs = [("http://127.0.0.1:8041", "sp_k19_s1", 19, 1), ("http://127.0.0.1:8042", "sp_k19_s2", 19, 2),
        ("http://127.0.0.1:8043", "sp_k12_s1", 12, 1), ("http://127.0.0.1:8044", "sp_k12_s2", 12, 2)]
ts = [threading.Thread(target=post, args=j) for j in jobs]; [t.start() for t in ts]; [t.join() for t in ts]
print("GEN DONE", flush=True)
