"""E6 period cross-check (dk2): measure every clip with BOTH tools/pend_acf (E6's frozen period tool; planted 4/4 within 5%,
formal verdict n/a) and tools/trk_ballfall/measure_pend.py v1 (referee PASS 20/20, raj-3). Both read at --fps 24, so periods are
in frames, like analyze_e6. Writes one JSON row per clip. Frozen before reading any B/C/W clip.
usage: python3 -I xcheck.py OUT.json clip1.mp4 clip2.mp4 ...
"""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
R = Path(__file__).resolve().parents[3]
ACF, MP = R / "tools/pend_acf/pend_acf.py", R / "tools/trk_ballfall/measure_pend.py"

def run(cmd):
    r = subprocess.run([sys.executable, "-I", *map(str, cmd)], capture_output=True, text=True)
    s = r.stdout; i = s.find("{")
    try:
        return json.loads(s[i:]) if cmd[0] == MP else json.loads(s.strip().splitlines()[-1])
    except Exception:
        return {"flag": "error", "stderr": r.stderr[-300:]}

def one(p):
    a = run([ACF, p, "--fps", "24", "--skip", "8"]); m = run([MP, p, "--fps", "24"])
    Pm = m.get("period_s") * 24 if m.get("period_s") else None
    Pa = a.get("period_frames")
    return dict(clip=Path(p).stem, P_acf=Pa, flag_acf=a.get("flag"), P_mp=Pm, flag_mp=m.get("flag"),
                Pzc_mp=(m["period_zc_s"] * 24 if m.get("period_zc_s") else None), r2_mp=m.get("r2"),
                release_t_mp=m.get("release_t"), mp_over_acf=(Pm / Pa if Pm and Pa else None))

if __name__ == "__main__":
    out, clips = sys.argv[1], sys.argv[2:]
    with ThreadPoolExecutor(6) as ex: rows = list(ex.map(one, clips))
    json.dump(rows, open(out, "w"), indent=1)
    for r in rows: print(json.dumps(r))
