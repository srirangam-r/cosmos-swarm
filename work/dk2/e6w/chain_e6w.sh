#!/bin/bash
# On the box: after ~/E6_DONE, run E6-W (wrong-period donor control) on the same 127.0.0.1:8011 server, then analyze.
# Starts only before 21:40 UTC (laptop watcher hard stop 23:00). Writes E6W_DONE when finished or skipped.
cd ~/jobs/dk2/e6w; touch PENDING
until [ -f ~/E6_DONE ]; do sleep 30; done
if [ "$(date -u +%H%M)" -ge 2140 ]; then echo "too late $(date -u +%T), skip"; touch E6W_DONE; exit 0; fi
echo "E6W start $(date -u +%T)"
PY=~/nano/venv312/bin/python
E6W_ENDPOINT=http://127.0.0.1:8011 $PY run_e6w.py
echo "E6W gen finished $(date -u +%T)"
$PY -I analyze_e6w.py > analyze_e6w.log 2>&1
echo "E6W_DONE $(date -u +%T)"; touch E6W_DONE
