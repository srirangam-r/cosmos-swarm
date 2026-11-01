"""Amendment 3 helper: keep only clips whose seed is in a list. Usage: python -I subset_seeds.py IN.json OUT.json 101,102,103,104"""
import sys, json
inp, outp, seeds = sys.argv[1], sys.argv[2], {int(s) for s in sys.argv[3].split(',')}
rows = json.load(open(inp))
keep = [r for r in rows if int((r.get('sidecar') or {}).get('seed', -1)) in seeds]
json.dump(keep, open(outp, 'w'))
print(f'kept {len(keep)}/{len(rows)} clips, seeds {sorted(seeds)}')
