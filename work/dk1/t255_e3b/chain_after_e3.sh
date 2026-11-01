#!/bin/bash
# On the box: wait for E3 to finish, then run E3b on the same localhost server (concurrency 1). Usage: bash chain_after_e3.sh <py> <model>
set -u
until grep -q E3_DONE ~/jobs/dk1/e3/run.log 2>/dev/null; do
  pgrep -f "run_onbox.sh" >/dev/null || { grep -q E3_DONE ~/jobs/dk1/e3/run.log || { echo "E3 runner gone without E3_DONE"; exit 1; }; }
  sleep 30; done
cd ~/jobs/dk1/e3b && cp ~/jobs/dk1/e3/run_onbox.sh ~/jobs/dk1/e3/cap_launch.py ~/jobs/dk1/e3/action_cfg.py ~/jobs/dk1/e3/server_action_cfg.patch . \
  && cp -r ~/jobs/dk1/e3/cosmos_local . && bash run_onbox.sh "$1" "$2" 8012
