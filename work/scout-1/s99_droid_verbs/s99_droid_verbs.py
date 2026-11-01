import sys, re, collections, json
import pyarrow.parquet as pq
t = pq.read_table(sys.argv[1])
print(t.schema)
cols = t.column_names
d = t.to_pydict()
# find the task string column
strcol = None
for c in cols:
    v = d[c][:5]
    if all(isinstance(x, str) for x in v):
        strcol = c; break
if strcol is None:
    # lerobot v3 stores task as index name
    strcol = cols[0]
tasks = [x for x in d[strcol] if isinstance(x, str)]
print('n task strings', len(tasks), 'col', strcol, 'sample', tasks[:5])
low = [x.lower() for x in tasks]
pats = {
 'drop': r'\bdrop(s|ped|ping)?\b',
 'release/let go': r'\b(release[sd]?|releasing|let go)\b',
 'throw/toss': r'\b(throw|throws|threw|toss|tosses|tossed)\b',
 'put': r'\bput(s|ting)?\b',
 'place': r'\bplac(e|es|ed|ing)\b',
 'put/place any': r'\b(put(s|ting)?|plac(e|es|ed|ing))\b',
 'pick': r'\bpick(s|ed|ing)?\b',
 'move': r'\bmov(e|es|ed|ing)\b',
 'ball': r'\bball\b',
}
res = {}
for k,p in pats.items():
    r = re.compile(p)
    res[k] = sum(1 for x in low if r.search(x))
print(json.dumps(res, indent=1))
r = re.compile(pats['drop'])
ex = [x for x in tasks if r.search(x.lower())]
print('drop examples', len(ex)); print('\n'.join(ex[:40]))
r2 = re.compile(pats['release/let go'])
ex2 = [x for x in tasks if r2.search(x.lower())]
print('release examples', len(ex2)); print('\n'.join(ex2[:15]))
