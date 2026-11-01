# Detached-State Dynamics Recipe for NVIDIA Cosmos3-Nano

> [!IMPORTANT]
> **Unified Deliverable 1 Tool:** The authoritative, consolidated recipe runner for Deliverable 1 is located in **[`tools/recipe/`](../recipe/)** (`tools/recipe/run_recipe.py`). It supports automated release-seam detection, remote endpoint inference, local GPU execution, `--dry-run` validation, and automated referee-validated verification. Please use `tools/recipe/run_recipe.py`.

**Charter Deliverable 1 Implementation Tool (Harmonized Runner)**

This tool provides turnkey, standalone execution of the **Detached-State Dynamics Recipe** for NVIDIA Cosmos3-Nano using `diffusers`. It restores physical Earth gravitational acceleration ($g = 9.73 \pm 1.91\text{ m/s}^2$ on Ball 1 Seed 1, $g_{h,T} = 9.86\text{ m/s}^2$) and 100% object release, eliminating phantom duplicate cloning and robotic arm plunging artifacts without visual degradation.

> **Tooling Note**: This runner is harmonized with [`tools/recipe/run_recipe.py`](../recipe/run_recipe.py), which provides extended support for HTTP endpoints (`vLLM-Omni`), automated release-seam optical flow detection, dry-run execution, and integrated verification.

## Quickstart

```bash
# Generate video rollout under the recipe (93 frames @ 24 fps, seed 1)
python3 tools/recipe_detached_state/run_recipe.py \
  --model nvidia/Cosmos3-Nano \
  --input_image work/raj-3/midfall/inputs/gauge_ball1_dd33_832x480.png \
  --output_dir ./outputs \
  --seed 1 \
  --num_frames 93 \
  --fps 24

# Verify physical acceleration using referee-validated firstfall.py
python3 tools/realball/firstfall.py \
  --fps 24 \
  --ppm 539.8 \
  ./outputs/recipe_drop_s1.mp4
```

See [deliverable_1_improved_nano_recipe.md](../../reports/deliverable_1_improved_nano_recipe.md) for the single authoritative Deliverable 1 specification, physical theory, negative result audits, and NVIDIA scoreboard proofs.
