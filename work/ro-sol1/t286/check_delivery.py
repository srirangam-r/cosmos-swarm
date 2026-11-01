"""QA existing task281 files; never generates or edits demo media."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timezone
import urllib.request
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PIN = "a597e6f"
BASE = "http://board.tail0c526a.ts.net:8031/demos/"
NAMES = [stem + ext for stem in ("pendulum_physics_start", "ball_settle")
         for ext in (".mp4", ".gif")]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def get(url, headers=None):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=15) as r:
        return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()


report = {"utc": datetime.now(timezone.utc).isoformat(), "commit": PIN,
          "scope": "delivery/codec/timebase only; no physics measurement", "media": []}
with tempfile.TemporaryDirectory(prefix="ro-sol1-t286-") as tmp:
    for name in NAMES:
        source = f"work/raj-demos/{name}"
        committed = subprocess.check_output(["git", "show", f"{PIN}:{source}"], cwd=REPO)
        status, headers, body = get(BASE + name)
        dest = Path(tmp) / name
        dest.write_bytes(body)
        probe = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
            "-show_entries", "stream=codec_name,pix_fmt,width,height,r_frame_rate,avg_frame_rate,nb_read_frames,duration:format=duration",
            "-of", "json", str(dest)]))
        decode = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(dest),
                                 "-f", "null", "-"], capture_output=True, text=True)
        entry = {"name": name, "url": BASE + name, "status": status,
                 "content_type": headers.get("content-type"), "bytes": len(body),
                 "sha256": sha(body), "committed_sha256": sha(committed),
                 "same_as_commit": body == committed, "probe": probe,
                 "full_decode_pass": decode.returncode == 0, "decode_stderr": decode.stderr}
        if name.endswith(".mp4"):
            rs, rh, rb = get(BASE + name, {"Range": "bytes=0-63"})
            entry["range_request"] = {"status": rs, "content_range": rh.get("content-range"),
                                       "bytes_returned": len(rb), "prefix_matches": rb[:64] == body[:64]}
            entry["mp4_atom_offsets"] = {s.decode(): body.find(s) for s in (b"moov", b"mdat")}
            frames = json.loads(subprocess.check_output([
                "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames",
                "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(dest)]))["frames"]
            times = [float(f["best_effort_timestamp_time"]) for f in frames]
            entry["timeline"] = {"frames": len(times), "first_s": times[0], "last_s": times[-1],
                                 "max_deviation_from_24fps_s": max(abs(t - i/24) for i, t in enumerate(times))}
        else:
            with Image.open(dest) as im:
                loop = im.info.get("loop")
                durations = []
                frame_hashes = []
                for i in range(im.n_frames):
                    im.seek(i)
                    durations.append(im.info.get("duration", 0))
                    frame_hashes.append(sha(im.convert("RGB").tobytes()))
                cumulative = [sum(durations[:i])/1000 for i in range(len(durations))]
                entry["timeline"] = {"frames": len(durations), "loop": loop,
                    "durations_ms": durations, "duration_s": sum(durations)/1000,
                    "unique_decoded_frames": len(set(frame_hashes)),
                    "max_deviation_from_12fps_s": max(abs(t - i/12) for i, t in enumerate(cumulative))}
        report["media"].append(entry)
    for stem in ("pendulum_physics_start", "ball_settle"):
        m, g = [m for m in report["media"] if m["name"].startswith(stem)]
        g["timeline"]["duration_difference_from_mp4_s"] = round(
            g["timeline"]["duration_s"] - float(m["probe"]["format"]["duration"]), 6)

report["pages"] = []
for url in (BASE, "http://sha-devel.tail0c526a.ts.net:8085/"):
    try:
        status, headers, body = get(url)
        text = body.decode("utf-8", "replace")
        (HERE / ("served_gallery.html" if ":8085" in url else "served_demos.html")).write_text(text)
        report["pages"].append({"url": url, "status": status, "sha256": sha(body),
            "new_demo_links_present": {n: n in text for n in NAMES}})
    except Exception as exc:
        report["pages"].append({"url": url, "error": str(exc)})
report["pass"] = all(m["status"] == 200 and m["same_as_commit"] and m["full_decode_pass"] for m in report["media"])
(HERE / "delivery_check.json").write_text(json.dumps(report, indent=2) + "\n")
for m in report["media"]:
    print(m["name"], m["status"], m["same_as_commit"], m["full_decode_pass"], m["timeline"])
print("pages", report["pages"])
if not report["pass"]:
    raise SystemExit(1)
