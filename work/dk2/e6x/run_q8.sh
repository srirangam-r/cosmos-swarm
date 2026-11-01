#!/bin/bash
# Fetch Raj's q8 E6 + E6-W outputs (read-only http://board.tail0c526a.ts.net:8031/) and apply the frozen cross-check.
# usage: bash run_q8.sh DEST_DIR   (run from anywhere; uses this repo's tools)
set -e; D=$(cd "$1" && pwd); H=$(cd "$(dirname "$0")" && pwd); CS=$(cd "$H/../../.." && pwd)
cd "$D" && wget -q -r -np -nH -R "index.html*" -e robots=off http://board.tail0c526a.ts.net:8031/ || true
E6=$(dirname "$(find "$D" -name 'C_t*_d*_tlo_s1.mp4' | head -1)"); W=$(dirname "$(find "$D" -name 'W_t*_d*_tlo_s1.mp4' | head -1)")
echo "E6 out: $E6  E6W out: $W"
python3 -I "$H/xcheck.py" "$D/xcheck_q8.json" "$E6"/[ABC]_*.mp4 "$W"/W*_*.mp4 > /dev/null
python3 -I "$H/redecide.py" "$H/real.json" "$D/xcheck_q8.json" > "$D/redecide_q8.json"
python3 -c "import json;j=json.load(open('$D/redecide_q8.json'));print(json.dumps(j['agreement']),json.dumps(j['verdict'],indent=1))"
