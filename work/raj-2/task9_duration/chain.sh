#!/bin/bash
# raj-2 task 9: after client PID 75002 (s1 of nf61/nf93) exits, remove the s2 placeholders and run the priority queue.
cd /home/nail/swarm-work/raj-2/dur
while kill -0 75002 2>/dev/null; do sleep 20; done
while read f; do [ -s "$f" ] || rm -f "$f"; done < placeholders.txt
exec python3 -I client.py jobs_queue2.jsonl --url http://100.111.167.68:8011 --out out
