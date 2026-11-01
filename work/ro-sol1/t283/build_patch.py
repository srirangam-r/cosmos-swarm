"""Build review files only; never modify the gallery owner's source."""
from pathlib import Path
import difflib
import re
import subprocess

out = Path(__file__).resolve().parent
root = out.parents[2]
player = (out / "player.js").read_text()
preview = (out.parent / "t280/preview.html").read_text()
updated, count = re.subn(r"<script>[\s\S]*?</script>", lambda _: "<script>\n" + player + "  </script>", preview)
assert count == 1
(out / "preview.html").write_text(updated)
gallery = "work/rahul-5-agy/gallery/index.html"
source = subprocess.check_output(["git", "show", "d466e17:" + gallery], cwd=root, text=True)
updated, count = re.subn(r"<script>[\s\S]*?</script>", lambda _: "<script>\n" + player + "  </script>", source)
assert count == 1
(out / "player-only.patch").write_text("".join(difflib.unified_diff(source.splitlines(True), updated.splitlines(True), fromfile="a/" + gallery, tofile="b/" + gallery)))
old = (out.parent / "t280/player.js").read_text()
(out / "source-error-delta.patch").write_text("".join(difflib.unified_diff(old.splitlines(True), player.splitlines(True), fromfile="a/player.js", tofile="b/player.js")))
print("Built preview and review patches; gallery unchanged.")
