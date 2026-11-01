"""Build owner-review patch and separate local preview; never edit owner gallery."""
from pathlib import Path
import difflib
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAME = 'work/rahul-5-agy/gallery/index.html'
source = subprocess.check_output(['git', 'show', f'f96be25:{NAME}'], cwd=ROOT).decode()
start = source.index('    function toggleSinglePlay(')
end = source.index('    // --- Paired Dual-Video', start)
patched = source[:start] + (HERE / 'single_controls.js').read_text() + '\n' + source[end:]
for primary, aliases in [('5566', ['5666', '5718']), ('5600', ['5634']), ('5563', ['5785'])]:
    marker = f'<div class="evidence-card" id="{primary}">'
    patched = patched.replace(marker, marker + ''.join(f'<span id="{alias}"></span>' for alias in aliases), 1)
(HERE / 'integration.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True), patched.splitlines(True), fromfile='a/'+NAME, tofile='b/'+NAME)))
(HERE / 'corrected_index.html').write_text(patched)
(HERE / 'preview.html').write_text(patched.replace('clips/', '../../rahul-5-agy/gallery/clips/'))
print('Patch and local preview created; owner gallery unchanged')
