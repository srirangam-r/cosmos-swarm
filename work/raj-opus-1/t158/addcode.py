"""python3 addcode.py <codes.json> <id> '<note>' key=val ... (defaults all 0)"""
import sys, json, os
p, i, note = sys.argv[1:4]
d = json.load(open(p)) if os.path.exists(p) else {}
Z = dict(fall=0, clean_fall=0, jump=0, clone=0, hold=0, carried=0, reentry=0, any_fall=0, midair_reversal=0, holder_back=0)
for kv in sys.argv[4:]:
    k, v = kv.split('='); Z[k] = int(v) if v.isdigit() else v
d[i] = {**Z, 'note': note}; json.dump(d, open(p, 'w'), indent=1); print(len(d), 'coded')
