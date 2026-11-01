"""Confirm the browser GIF screenshot pairs differ in decoded pixels."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops

here = Path(__file__).resolve().parent
results = []
for stem in ("pendulum_physics_start", "ball_settle"):
    paths = [here / f"{stem}_gif_{suffix}.png" for suffix in ("a", "b")]
    a, b = [Image.open(p).convert("RGB") for p in paths]
    pixels = sum(max(v) > 8 for v in ImageChops.difference(a, b).getdata())
    results.append({"stem": stem, "screenshot_sha256": [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths],
                    "different_pixels_gt8": pixels, "total_pixels": a.width * a.height,
                    "fraction": pixels / (a.width * a.height), "pass": pixels > 100})
(here / "gif_pixel_changes.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
if not all(r["pass"] for r in results):
    raise SystemExit(1)
