#!/bin/bash
# t257: fetch Raj's E3 clips (owners raj-noise-f/g), hash, measure (frozen e3seed.py), analyze. Writes DONE.
cd /home/sha/swarm-work/rahul-api-2/t257
Q=/home/sha/devel/agentic_colab/scripts/cosmos_queue.py
E=/home/sha/swarm-work/rahul-api-2/cosmos-swarm/work/rahul-api-2/t257_e3seed/e3seed.py
PY=/home/sha/swarm-work/rahul-api-2/.venv/bin/python
for o in raj-noise-f raj-noise-g; do python3 $Q fetch --owner $o --out clips; done
ls clips/N_E3_*.mp4 | wc -l
(cd clips && sha256sum N_E3_*.mp4 > ../E3_SHA256SUMS)
$PY -I $E measure clips meas.json
$PY -I $E analyze meas.json result.json
touch DONE
