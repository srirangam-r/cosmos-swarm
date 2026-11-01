#!/bin/bash
# t226 Amendment 8 runner (written before the 2nd coder's codes exist).
# usage: ./run_codes_t226.sh <r5 codes.json> <rahul3 codes.json>
# Primary: 2-coder consensus (analyze_codes_t226.py unchanged). Sensitivity: each coder alone; agreement on #5293 IDs.
set -euo pipefail
cd "$(dirname "$0")"
R5=$1; R3=$2
python3 analyze_codes_t226.py blind_key.json codes_result.json r5="$R5" rahul3="$R3" | tee codes_result.log
python3 analyze_codes_t226.py blind_key.json codes_result_r5only.json r5="$R5" > codes_result_r5only.log
python3 analyze_codes_t226.py blind_key.json codes_result_rahul3only.json rahul3="$R3" > codes_result_rahul3only.log
python3 - "$R5" "$R3" <<'EOF' | tee codes_subset_agreement.log
import json, sys
a = {k.strip().upper(): str(v).strip().upper() for k, v in json.load(open(sys.argv[1])).items()}
b = {k.strip().upper(): str(v).strip().upper() for k, v in json.load(open(sys.argv[2])).items()}
named = {'BRDS', 'LIIF', 'KTSI', 'CLLZ', 'EIIG', 'UYPK', 'XOUV', 'WTUS', 'FEMH', 'RWHG', 'WTVP', 'ZEBT'}  # IDs coded in #5293
ids = sorted(set(a) & set(b))
for lab, sub in (('named_in_5293', [i for i in ids if i in named]), ('other', [i for i in ids if i not in named])):
    agree = sum(a[i] == b[i] for i in sub)
    print(json.dumps({'subset': lab, 'n': len(sub), 'agree': agree, 'rate': round(agree / max(1, len(sub)), 3),
                      'disagree': {i: [a[i], b[i]] for i in sub if a[i] != b[i]}}))
EOF
