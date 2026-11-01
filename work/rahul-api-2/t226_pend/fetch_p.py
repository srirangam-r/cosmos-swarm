"""Download only the task-226 pendulum clips (rahul-api's t226_P_* jobs) from the shared queue, with their sidecars.
Standard library only. Usage: python3 -I fetch_p.py OUT_DIR [--owner rahul-api] [--prefix t226_P_] [--url QUEUE_URL]"""
import sys, json, argparse, urllib.request
from pathlib import Path

DEFAULT_URL = "http://100.111.167.68:8030"


def call(url, raw=False):
    with urllib.request.urlopen(url, timeout=120) as r:
        b = r.read()
    return b if raw else json.loads(b)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--owner', default='rahul-api')
    ap.add_argument('--prefix', default='t226_P_'); ap.add_argument('--url', default=DEFAULT_URL)
    a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    got = left = 0
    for j in call(f"{a.url}/jobs?owner={a.owner}")["jobs"]:
        if not j['name'].startswith(a.prefix):
            continue
        if j['status'] != 'done':
            left += j['status'] in ('pending', 'running')
            if j['status'] == 'failed':
                print(f"failed: {j['name']} ({j['id']}): {j.get('error')}", file=sys.stderr)
            continue
        mp4 = out / f"{j['name']}.mp4"
        if mp4.exists():
            continue
        (out / f"{j['name']}.json").write_text(json.dumps(j.get('sidecar', {}), indent=1))
        mp4.write_bytes(call(f"{a.url}/jobs/{j['id']}/mp4", raw=True)); got += 1
    print(f"downloaded {got} clip(s) to {out}; {left} t226 pendulum job(s) still pending or running")


if __name__ == '__main__':
    main()
