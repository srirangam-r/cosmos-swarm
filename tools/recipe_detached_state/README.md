# Detached-State Dynamics Recipe for NVIDIA Cosmos3-Nano

**Charter Deliverable 1 Implementation Tool (Harmonized Runner)**

This tool provides turnkey, standalone execution of the **Detached-State Dynamics Recipe** for NVIDIA Cosmos3-Nano using `diffusers`. It restores physical Earth gravitational acceleration ($g = 9.82 \pm 0.35\text{ m/s}^2$) and 100% object release, eliminating phantom duplicate cloning and robotic arm plunging artifacts without visual degradation.

> **Tooling Note**: This runner is harmonized with [`tools/recipe/run_recipe.py`](../recipe/run_recipe.py), which provides extended support for HTTP endpoints (`vLLM-Omni`), automated release-seam optical flow detection, and integrated verification.

## Quickstart

```bash
# Generate video rollout under the recipe (93 frames @ 24 fps, seed 1)
python3 tools/recipe_detached_state/run_recipe.py \
  --model nvidia/Cosmos3-Nano \
  --input_image work/raj-3/midfall/ball1_f33.png \
  --output_dir ./outputs \
  --seed 1 \
  --num_frames 93 \
  --fps 24

# Verify physical acceleration using referee-validated firstfall.py
python3 tools/realball/firstfall.py \
  --video ./outputs/recipe_drop_s1.mp4 \
  --fps 24 \
  --px_per_m 539.8 \
  --out_json ./outputs/kinematics_s1.json
```

See [deliverable_1_recipe.md](../../reports/deliverable_1_recipe.md) for full physical theory, negative result audits, and NVIDIA scoreboard proofs.
