#!/usr/bin/env python3
"""
Redirect pointer: Task 77 tooling has been consolidated into the canonical Deliverable 1 tool:
tools/recipe/run_recipe.py

This script forwards all arguments directly to tools/recipe/run_recipe.py.
"""
import os
import sys
from pathlib import Path

CANONICAL_SCRIPT = Path(__file__).resolve().parent.parent / "recipe" / "run_recipe.py"

if __name__ == "__main__":
    print(f"[notice] tools/recipe_detached_state/run_recipe.py has been consolidated into canonical {CANONICAL_SCRIPT}")
    os.execv(sys.executable, [sys.executable, str(CANONICAL_SCRIPT)] + sys.argv[1:])
