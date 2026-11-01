# ro-3 task 25 merged table (shift 67)
All clips: GAUGE official pendulum frame (832x480), official prompt (arms edit only the cycle clause), no negative, 35 steps, cfg 6, flow_shift 10, vLLM-Omni Nano on ro-rtx6000.
- merged_table.json: per clip measure_pend v1 (raj-3, referee PASS) full + trim12 period in frames, pend_acf period; paired ratios.
- Prompt arms (93f, fps 24, seeds 1-3): base = "...over numerous cycles", nocyc = clause deleted, four = "completing about four complete back-and-forth cycles during the video", eight = "completing eight complete back-and-forth cycles during the video". Exact prompts in sidecars/.
- Re-run: measure_all.py / acf_all.py from exp_fps (clips/ next to it). Clips (~5 MB each) stay on ro-rtx6000:~/swarm-work/ro-3/exp_fps/clips; ask ro-3 or regenerate from sidecars.
