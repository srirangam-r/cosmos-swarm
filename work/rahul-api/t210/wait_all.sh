#!/bin/bash
cd "$(dirname "$0")"
while true; do
  n=$(ls clips | grep -c mp4)
  if [ "$n" -ge 288 ]; then echo "ALL $n"; exit 0; fi
  if grep -q FAILED fetch.log; then echo "FAILED seen at $n"; exit 1; fi
  sleep 5
done
