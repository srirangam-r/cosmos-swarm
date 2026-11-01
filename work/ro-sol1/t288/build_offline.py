"""Build a single offline page from unchanged, pinned task281 MP4s. No encoding."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PIN = "a597e6f"
HASHES = {
    "pendulum_physics_start": "fd724670aab40fd348fe5dfcd11e7996a62a13cb96b0fb9ec1a302d12cb84e99",
    "ball_settle": "6ba3af0a67bf3d3ee5497e22bdbfac6a58eaac2d88ad95aadce3e31df962ea86",
}
page = (HERE / "template.html").read_text()
manifest = {"source_commit": PIN, "media": [], "scope": "offline presentation; no new measurements"}
for stem, expected in HASHES.items():
    source = f"work/raj-demos/{stem}.mp4"
    data = subprocess.check_output(["git", "show", f"{PIN}:{source}"], cwd=REPO)
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise SystemExit(f"Hash mismatch for {source}: {actual}")
    marker = "@@" + stem.upper() + "@@"
    if page.count(marker) != 1:
        raise SystemExit(f"Missing/duplicate template marker: {marker}")
    page = page.replace(marker, "data:video/mp4;base64," + base64.b64encode(data).decode("ascii"))
    manifest["media"].append({"name": stem + ".mp4", "source": source, "sha256": actual, "bytes": len(data)})
output = page.encode("utf-8")
(HERE / "offline.html").write_bytes(output)
manifest["html_bytes"] = len(output)
manifest["html_sha256"] = hashlib.sha256(output).hexdigest()
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Built {HERE / 'offline.html'} ({len(output):,} bytes)")
