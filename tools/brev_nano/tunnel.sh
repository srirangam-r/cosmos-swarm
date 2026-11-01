#!/bin/bash
# Run on sha-devel: forwards the box's loopback servers to sha-devel's tailnet IP (tailnet only, ports 8001-8099).
# Usage: bash tunnel.sh <brev-box-name> <first-local-port> <n-gpus>    e.g. bash tunnel.sh rapi2-pro6k-1 8071 2
B=$1; L=$2; N=$3; IP=$(tailscale ip -4)
ARGS=""; for i in $(seq 0 $((N-1))); do ARGS="$ARGS -L $IP:$((L+i)):127.0.0.1:$((8011+i))"; done
while true; do
  echo "=== tunnel $B start $(date -u +%FT%TZ)"
  ssh -N -T -o ControlMaster=no -o ControlPath=none -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 \
      -o ServerAliveCountMax=3 $ARGS $B
  echo "=== tunnel exit $? $(date -u +%FT%TZ)"; sleep 10
done
