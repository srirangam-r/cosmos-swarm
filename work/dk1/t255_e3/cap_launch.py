"""Run a script with this process's CUDA caching allocator capped (co-tenant safety on a shared GPU).
Usage: python cap_launch.py <fraction> <script.py> [args...]. If we exceed the cap, WE OOM, not the other tenant."""
import os, runpy, sys
import torch
frac = float(sys.argv[1]); script = os.path.abspath(sys.argv[2])
torch.cuda.set_per_process_memory_fraction(frac, 0)
sys.argv = [script] + sys.argv[3:]
sys.path.insert(0, os.path.dirname(script))
runpy.run_path(script, run_name="__main__")
