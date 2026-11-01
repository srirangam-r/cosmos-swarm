"""Build an owner-review patch; never edit the owner's gallery source."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = 'work/rahul-5-agy/gallery/index.html'
BASE = 'ceb5a4e'
source = subprocess.check_output(['git', 'show', f'{BASE}:{TARGET}'], cwd=ROOT).decode()
start = source.index('      <!-- ROW 3: E6/E6-W')
end = source.index('      <!-- ROW 4:', start)
row = source[start:end]
row = row.replace("PROVISIONAL: slo ('all')", 'E7: PARTIAL DONOR-CLOCK TRANSFER')
row = row.replace("3. Donor-Noise Transfer &mdash; Spatial 'slo' vs Temporal 'tlo' Ringing ARTIFACT", '3. Donor-Noise Transfer &mdash; Partial Clock Copying')
row = row.replace('Target: Dynamics Rate Tuning', 'Human E7 report: <a href="#6167">#6167</a>')
row = row.replace("Spatial 'slo' Band (PROVISIONAL)", "E6 Spatial 'slo' Example")
row = row.replace('Real Inversion Reference', 'E6 Real Inversion Diagnostic')
row = row.replace("Spatial 'slo' Band (Provisional)", "Historical E6 Illustration (Variant Above)")
a = row.index('            <p><strong>Artifact Caught by Cross-Check:')
b = row.index('          </div>', a)
row = row[:a] + '''            <p><strong>Shown: selected historical E6 media.</strong> These clips are illustrations, not the E7 benchmark grid. Earlier temporal mixing across clean frame 0 produced global luma ringing (27.4 frames; flicker index 0.505; <a href="#5634">#5634</a>). E7 corrected that boundary: its temporal donor arm had 8/16 clean clips, but 0/16 within 10% of the real period.</p>
            <p style="margin-top: 0.5rem;"><strong>E7 spatial donor result:</strong> Raj reports 8 targets &times; 2 seeds per arm. Spatial <code>slo</code> transfer had 8/16 clean clips and 6/16 within 10% of the real period (median P/P_real 1.05); plain noise had 4/16 clean and 0/16 within 10% (median 0.47). Clean means <code>pend_acf</code> ok, flicker &lt; 0.08, and <code>measure_pend</code> agrees within 10%.</p>
            <p style="margin-top: 0.5rem;"><strong>Partial clock copying:</strong> With a 10/7-sped-up donor, the median ratio fell to 0.68 (0.70 expected). The paired transfer fraction f = 0.93 uses only 3 targets, with CI [-2.2, 1.15]: underpowered. Raj reports no general noise-shaping fix; this route needs a matching real donor recording. <a href="#6167">Human report #6167</a>; no independent remeasurement or NVIDIA-scoreboard pass is claimed here.</p>
''' + row[b:]
row = row.replace('Audit Classification', 'E7 Spatial Donor Coverage')
row = row.replace('<div class="metric-value" style="color:var(--accent-rose);">ARTIFACT (tlo)</div>', '<div class="metric-value" style="color:var(--accent-amber);">8/16 Clean</div>')
row = row.replace("Spatial 'slo' is PROVISIONAL (P/P_real &approx; 1.000, flicker &lt; 0.01)", '6/16 within 10% of real; plain 4/16 clean, 0/16 within 10%. Historical E6 videos shown.')
corrected = source[:start] + row + source[end:]
a = corrected.index('        <div class="evidence-card" id="5600">')
b = corrected.index('        <div class="evidence-card" id="5563">', a)
registry = corrected[a:b]
registry = registry.replace('Spatial band transfer (slo) avoids frame 0 mixing and remains flicker-free (&lt; 0.01).', 'This is the historical E6 artifact report; see E7 #6167 for the corrected boundary and full planned QC coverage.')
registry += '''        <div class="evidence-card" id="6167">
          <div class="evidence-title">
            <span>Human Report #6167: E7 Donor-Clock Transfer</span>
            <span class="label-badge badge-provisional">Partial / Underpowered</span>
          </div>
          <div class="evidence-meta">Raj &bull; Task #250 &bull; 224 generated clips; 8 targets &times; 2 seeds per arm &bull; Frozen 9dd4fc8 + f9e980e</div>
          <div class="evidence-desc">
            Spatial slo: 8/16 clean, 6/16 within 10% of real, median P/P_real 1.05. Plain: 4/16 clean, 0/16 within 10%, median 0.47. Sped-up donor median 0.68 (expected 0.70); paired f = 0.93 on only 3 targets, CI [-2.2, 1.15]. Temporal donor with frame 0 fixed: 8/16 clean, 0/16 within 10%. No general noise-shaping fix reported. This gallery quotes the human report; the existing E6 videos are not E7 benchmark clips, and no independent remeasurement or NVIDIA-scoreboard pass is claimed.
          </div>
        </div>

'''
corrected = corrected[:a] + registry + corrected[b:]
HERE.mkdir(exist_ok=True)
(HERE/'baseline_index.html').write_text(source)
(HERE/'corrected_index.html').write_text(corrected)
(HERE/'preview.html').write_text(corrected.replace('src="clips/', 'src="../../rahul-5-agy/gallery/clips/').replace("'clips/", "'../../rahul-5-agy/gallery/clips/"))
patch = ''.join(difflib.unified_diff(source.splitlines(True), corrected.splitlines(True), fromfile='a/'+TARGET, tofile='b/'+TARGET))
(HERE/'integration.patch').write_text(patch)
scripts = lambda s: re.findall(r'<script\b[^>]*>.*?</script>',s,re.S)
media = lambda s: re.findall(r'<source\b[^>]*src="([^"]+)"',s)
checks = {
    'all_script_bytes_unchanged': scripts(source)==scripts(corrected),
    'all_media_references_unchanged': media(source)==media(corrected),
    'other_rows_unchanged': source[:start]==corrected[:start] and source[end:source.index('        <div class="evidence-card" id="5600">')]==corrected[corrected.index('      <!-- ROW 4:'):corrected.index('        <div class="evidence-card" id="5600">')],
    'source_file_untouched': (ROOT/TARGET).read_text()==source,
    'awaiting_e7_claim_removed': 'E7b lands' not in corrected,
    'universal_slo_flicker_claim_removed': 'remains flicker-free' not in registry and 'completely flicker-free' not in row,
    'e7_anchor_unique': corrected.count('id="6167"')==1,
}
result = {'baseline_commit':BASE,'baseline_sha256':hashlib.sha256(source.encode()).hexdigest(),'corrected_sha256':hashlib.sha256(corrected.encode()).hexdigest(),'source_report':6167,'media_references':len(media(source)),'checks':checks}
(HERE/'source_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
assert all(checks.values())
orders = {}
for order in [(306, 313), (313, 306)]:
    with tempfile.TemporaryDirectory(prefix='ro-sol1-gallery-patches-') as tmp:
        target = Path(tmp)/TARGET
        target.parent.mkdir(parents=True)
        target.write_text(source)
        runs = []
        for task in order:
            patch_path = ROOT/f'work/ro-sol1/t{task}/integration.patch'
            run = subprocess.run(['git', 'apply', str(patch_path)], cwd=tmp, text=True, capture_output=True)
            runs.append({'task':task, 'returncode':run.returncode, 'stderr':run.stderr})
        orders['-'.join(map(str, order))] = {
            'runs':runs, 'final_sha256':hashlib.sha256(target.read_bytes()).hexdigest()
        }
compatibility = {'orders':orders, 'identical_combined_page':len({o['final_sha256'] for o in orders.values()})==1}
(HERE/'patch_compatibility.json').write_text(json.dumps(compatibility,indent=2)+'\n')
assert compatibility['identical_combined_page']
assert all(r['returncode']==0 for o in orders.values() for r in o['runs'])
print('Both patch orders apply and produce identical combined HTML.')
