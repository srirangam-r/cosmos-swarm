# brev_nano (rahul-api-2): Brev GPU box → Cosmos queue endpoint, board stack, tailnet only

Turns a rented Brev box into one Cosmos3-Nano endpoint per GPU, running **the board's own
`tools/cosmos_local/server.py`** (diffusers bf16, no offload, the same sampler, internals hooks and loss
probe as q8/l40s/a6k). Jobs the queue sends to any endpoint therefore see the same stack everywhere.

Brev boxes are not on the tailnet. The servers bind to the box's 127.0.0.1 only. An ssh tunnel from
sha-devel forwards them to sha-devel's **tailnet** IP (ports 8001-8099), and the queue reaches them there.
Nothing listens on a public interface.

## Steps
1. `brev create <name> --type <type> --startup-script @bootstrap.sh`. The box's startup hook did not keep the
   background job alive on verda, so if `~/nano/setup.log` is missing after boot, run
   `ssh <name> 'cd ~/nano && setsid nohup bash setup.sh > setup.log 2>&1 < /dev/null &'`.
   setup.sh: uv, py3.12 venv, diffusers@main + torch (cu130 wheels; needs driver ≥ 580), Nano weights (~32 GB).
   It touches `~/nano/READY` when both are done.
2. `scp -r tools/cosmos_local tools/brev_nano <name>:nano/`
3. On the box: `bash ~/nano/brev_nano/serve.sh <label-prefix>` starts one server per GPU on 127.0.0.1:8011+i.
   Each server's sidecar `model` field carries the label (`COSMOS_LABEL`). Loading takes ~1-2 min.
4. On sha-devel: `nohup bash tools/brev_nano/tunnel.sh <name> <first-port> <n-gpus> > tunnel.log 2>&1 &`
   gives `http://<sha-devel tailnet ip>:<first-port+i>/health`.
5. Ask the queue operator (#compute) to add `--endpoint <label>-i=http://<sha-devel ip>:<port>`.

## Boxes run this way
See #compute (rahul-api-2 posts) for the live list, $/h and the running tally of Rahul's $100.

## Idle/budget watcher
`idle_watch.sh <box> <usd_per_h> <start_epoch> <tunnel_loop_pid> <url>...` (on sha-devel, nohup). Deletes the box
and stops its tunnel when the endpoints serve no clip for `IDLE_MIN` (40) minutes or its spend reaches `CAP_USD` (60).
It never deletes while an endpoint is busy. `touch ~/STOP_<box>` stops the watcher and keeps the box.

## Measured (rapi2-pro6k-1, verda 2× RTX Pro 6000, 11:21 UTC)
93 f / 35 steps / 832x480: 52 s per clip per GPU. The same seed is not bit-identical to q8 (frame-0 diff 0.32/255,
whole clip 3-4/255 vs 4.7/255 between seeds; one of two seeds took a different branch), so treat endpoints as
different draws and pin `--endpoints` for seed-paired A/B arms.
