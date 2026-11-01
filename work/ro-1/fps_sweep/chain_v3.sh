#!/bin/bash
cd /home/rohith/swarm-work/ro-1/fps_sweep
while kill -0 428991 2>/dev/null; do sleep 20; done
nice -n 10 /home/rohith/swarm-work/ro-1/py312/bin/python -I client.py jobs_v3.jsonl --url http://100.77.182.40:8021 --out out > client_v3.log 2>&1
while kill -0 428992 2>/dev/null; do sleep 20; done
nice -n 10 /home/rohith/swarm-work/ro-1/py312/bin/python -I measure_all.py > meas/measure_all_v3.log 2>&1
