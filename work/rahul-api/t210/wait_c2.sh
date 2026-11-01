#!/bin/bash
cd "$(dirname "$0")"
while true; do
  n=$(ls clips_c2 | grep -c mp4)
  if [ "$n" -ge 288 ]; then echo "ALL $n"; exit 0; fi
  if grep -q FAILED fetch_c2.log; then echo "FAILED seen at $n"; exit 1; fi
  python3 fetch_t210.py clips_c2 t210c2_ >> fetch_c2.log 2>&1; sleep 10
done
