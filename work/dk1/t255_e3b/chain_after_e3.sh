#!/bin/bash
# On the box: run E3b on the same localhost server AFTER both E3 (E3_DONE) and dk2's E6 (~/E6_DONE) are finished,
# so E3b never time-shares the GPU with E6 (co-tenancy slowed E6 inversions 144 s -> 246 s). Starts only before
# 21:10 UTC (E3b alone ~30-40 min; box hard stop 22:00). Usage: bash chain_after_e3.sh <py> <model>
set -u
until grep -q E3_DONE ~/jobs/dk1/e3/run.log 2>/dev/null; do
  pgrep -f "run_onbox.sh" >/dev/null || { grep -q E3_DONE ~/jobs/dk1/e3/run.log || { echo "E3 runner gone without E3_DONE"; exit 1; }; }
  sleep 30; done
echo "E3_DONE seen $(date -u +%T); waiting for ~/E6_DONE"
until [ -f ~/E6_DONE ]; do sleep 30; done
if [ "$(date -u +%H%M)" -ge 2110 ]; then echo "E6_DONE at $(date -u +%T): too late for E3b before 22:00, skipping"; exit 0; fi
echo "E3b start $(date -u +%T)"
cd ~/jobs/dk1/e3b && cp ~/jobs/dk1/e3/run_onbox.sh ~/jobs/dk1/e3/cap_launch.py ~/jobs/dk1/e3/action_cfg.py ~/jobs/dk1/e3/server_action_cfg.patch . \
  && cp -r ~/jobs/dk1/e3/cosmos_local . && MEMFRAC=0.9 bash run_onbox.sh "$1" "$2" 8012
