#!/bin/bash
# ro-1: Cosmos3-Nano server on ro-rtx6000 GPU 1, port 8021; restarts on crash; stops at SWARM_END.
cd /home/rohith/swarm-work/ro-1/srv
END=$(date -d "2026-11-01T08:00:00-05:00" +%s)
IP=$(tailscale ip -4 | head -1)
export CUDA_VISIBLE_DEVICES=1 HF_HOME=/home/rohith/swarm-work/ro-1/hfhome
while [ "$(date +%s)" -lt "$END" ]; do
  echo "=== start $(date -u +%FT%TZ)" >> server.log
  COSMOS_QCHUNK=${COSMOS_QCHUNK:-8192} timeout $(( END - $(date +%s) )) nice -n 10 /home/rohith/swarm-work/ro-1/py312/bin/python server.py --host "$IP" --port 8021 --model /home/rohith/swarm-work/ro-1/models/Cosmos3-Nano >> server.log 2>&1
  echo "=== exit $? $(date -u +%FT%TZ)" >> server.log
  sleep 10
done
