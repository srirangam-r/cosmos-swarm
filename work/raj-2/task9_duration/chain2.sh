#!/bin/bash
# raj-2 task 9: after the chain (PID 77283) exits, run arms F1/F0 (189 frames, JSON prompts).
cd /home/nail/swarm-work/raj-2/dur
while kill -0 77283 2>/dev/null; do sleep 20; done
exec python3 -I client.py jobs_F.jsonl --url http://100.111.167.68:8011 --out out
