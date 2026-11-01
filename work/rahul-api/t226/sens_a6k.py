#!/usr/bin/env python3
"""t226 Amendment 7 sensitivity: frozen analyze_t226.py on seeds 101-104 only (all a6k), because the a100 endpoint
(seeds 105-106) may not apply noise.device=cpu (rahul-api-2 #4912). Descriptive: with n=4 pairs the exact sign-flip p
is >= 0.125, so no decision can reach p <= 0.05. usage: sens_a6k.py measures.json out.json"""
import sys, json, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_t226 as A
M = json.load(open(sys.argv[1])); S = {k: v for k, v in M.items() if v['seed'] in (101, 102, 103, 104)}
with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f: json.dump(S, f); tmp = f.name
A.main(tmp, sys.argv[2]); os.unlink(tmp)
