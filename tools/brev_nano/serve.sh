#!/bin/bash
# Run on the Brev box after ~/nano/READY exists and tools/cosmos_local/ has been copied to ~/nano/cosmos_local/.
# One server.py per GPU on 127.0.0.1:8011+i (never a public interface), each in a restart loop.
# Usage: bash serve.sh <label-prefix>   e.g. bash serve.sh brev-p6k   (labels brev-p6k-0, brev-p6k-1, ...)
P=${1:-brev}
cd ~/nano/cosmos_local
ln -sfn ~/nano/models models
N=$(nvidia-smi -L | wc -l)
for i in $(seq 0 $((N-1))); do
  nohup bash -c "while true; do echo \"=== start \$(date -u +%FT%TZ)\" >> ~/nano/server$i.log;
    CUDA_VISIBLE_DEVICES=$i COSMOS_OFFLOAD=0 COSMOS_LABEL=$P-$i COSMOS_QCHUNK=8192 ~/nano/venv312/bin/python server.py \
      --host 127.0.0.1 --port $((8011+i)) --out ~/nano/out_srv$i >> ~/nano/server$i.log 2>&1;
    echo \"=== exit \$? \$(date -u +%FT%TZ)\" >> ~/nano/server$i.log; sleep 10; done" > /dev/null 2>&1 &
  echo "GPU $i -> 127.0.0.1:$((8011+i)) label $P-$i loop pid $!"
done
