"""Fetch only queue jobs of an owner whose name starts with a prefix (same logic as cosmos_queue.py fetch)."""
import json, sys
from pathlib import Path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "repo/scripts"))
from cosmos_queue import call
DEFAULT_URL = "http://127.0.0.1:8030"
owner, prefix, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
got = left = 0
for j in call(f"{DEFAULT_URL}/jobs?owner={owner}")["jobs"]:
    if not j["name"].startswith(prefix): continue
    if j["status"] != "done":
        left += j["status"] in ("pending", "running"); print(j["name"], j["status"], j.get("error")); continue
    if j.get("qc"): (out / f"{j['name']}.qc.json").write_text(json.dumps(j["qc"], indent=1))
    mp4 = out / f"{j['name']}.mp4"
    if mp4.exists(): continue
    sc = dict(j.get("sidecar", {})); sc["queue_job_id"] = j["id"]; sc["endpoint"] = j.get("endpoint")
    (out / f"{j['name']}.json").write_text(json.dumps(sc, indent=1))
    mp4.write_bytes(call(f"{DEFAULT_URL}/jobs/{j['id']}/mp4", raw=True))
    for rel in j.get("sidecar", {}).get("relayed", []):
        dest = out / (f"{j['name']}.server.json" if rel == "server_sidecar.json" else f"{j['name']}.{Path(rel).name}")
        dest.write_bytes(call(f"{DEFAULT_URL}/jobs/{j['id']}/files/{rel}", raw=True))
    got += 1
print(f"downloaded {got}; {left} pending/running")
