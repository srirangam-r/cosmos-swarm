#!/bin/bash
# Keeps the Cosmos3-Nano server up: restarts it if it dies (e.g. CUDA launch timeout). Stop: kill this loop's PID, then the python child.
cd "$(dirname "$0")"
IP=$(tailscale ip -4)
while true; do
  echo "=== start $(date -u +%FT%TZ)" >> server.log
  COSMOS_QCHUNK=${COSMOS_QCHUNK:-8192} venv312/bin/python server.py --host "$IP" --port 8011 >> server.log 2>&1
  echo "=== exit $? $(date -u +%FT%TZ)" >> server.log
  sleep 10
done
