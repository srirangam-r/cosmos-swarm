#!/usr/bin/env python3
"""Build a review copy and patch; never write the gallery owner's files."""
from pathlib import Path
import difflib
import hashlib
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'work/rahul-5-agy/gallery/index.html'
# Read the archived source so the review proposal remains reproducible after
# the owner updates their current gallery. Never reset or overwrite their file.
old = subprocess.check_output(['git', 'show', '333821f:work/rahul-5-agy/gallery/index.html'], cwd=ROOT, text=True)
s = old

def replace(a, b):
    global s
    if a not in s:
        raise ValueError(f'Expected source text missing: {a[:100]}')
    s = s.replace(a, b)

replace('Physics Fixes Gallery', 'Physics Demo Gallery')
replace("Curated side-by-side empirical demonstrations proving the swarm's fixes to NVIDIA Cosmos3-Nano's physical world modeling weaknesses across periodic dynamics, damping, forward dynamics, and gravity.",
        'Existing Cosmos3-Nano demo clips and source results. Each row states its evidence status. Gallery clips are illustrative: native per-clip provenance is pending, so the players do not establish matched before/after measurements.')
replace('Total Verified Fixes', 'Demo Entries')
replace('Matched Controls &amp; Seeds', 'See Each Source Experiment')
replace('Visual Quality (DOVER)', 'Full Recipe Scoreboard')
replace('&Delta; = -0.004 &plusmn; 0.007 (Retained)', 'Pending')
replace('<main class="gallery-grid">', '''<main class="gallery-grid">
      <p style="color:#fbbf24">Review copy, 2026-11-01. Numbers below are attributed source results, not measurements of this page or the new Nano-Phys CLI. Native continuous pendulum media and per-asset scene/seed/sidecars are still needed. Shared player controls align starts and loop boundaries; sampled footage cannot support frame-accurate comparisons.</p>''')

# The pendulum numbers come from the native rows recovered by task278, not
# the unmatched GAUGE published baseline that appeared in the original page.
replace('1. Kinematic Sim-Proxy Latent Conditioning', '1. Sim-Proxy Pendulum — Provisional')
replace('<a href="#5315">Finding #5315</a>', '<a href="https://github.com/srirangam-r/cosmos-swarm/blob/ceb5310/work/ro-3/task252/results_sp.json">Source results (#5315)</a>')
replace('Target: Pendulum Period Slowness', 'Target: Externally Specified Period Transfer')
replace('Physical Proxy (1.18s)', 'Proxy Target (1.187s)')
replace('Plain Cosmos3-Nano</span>', 'Plain Nano Example (Match Unverified)</span>')
replace('Sim-Proxy Init (Fixed)', 'Provisional Proxy-Init Example')
start = s.index('      <!-- ROW 1:')
end = s.index('      <!-- ROW 2:')
part = s[start:end]
part = part.replace('416&times;240 &bull; 24 fps</span>', '416&times;240 &bull; 93f @ 24fps</span>', 1)
part = part.replace('416&times;240 &bull; 24 fps</span>', '416&times;240 &bull; 16 sampled frames @ 4fps</span>', 1)
part = re.sub(r'Injecting an analytical.*?without changing prompt geometry\.',
    'Source experiment: a hand-built pendulum proxy supplies the target period; Nano renders a continuation. The proxy length (0.35 m) was an explicit, nonblind assumption. This supports period transfer, with geometry, generalization and the new CLI benchmark still pending. Displayed right-hand files are sampled QC derivatives, not native continuous footage.', part, flags=re.S)
part = part.replace('Measured Oscillation Period', 'Source Experiment, t_init 0.6')
part = part.replace('T = 1.186 s', 'T = 1.1863 s')
part = part.replace('&plusmn; 0.001 s (vs Plain Nano 2.36 s, Real Mocap 1.06 s)',
    'Range 1.1857–1.1870s, 2 scenes × 2 seeds; control 2.0175–2.0202s. Source plain 0.833–0.843s (1 seed/scene), real ≈1.18s. Not a benchmark of the shipped CLI.')
s = s[:start] + part + s[end:]

# Exclude the unauthenticated transfer asset from display. The reconstruction
# is a diagnostic using later real video, not a frame-0-only user recipe.
replace("2. Spatial Donor-Noise Band Transfer (E6 'slo' / 'all')", '2. Donor Reconstruction Diagnostic — Provisional')
replace('Target: Dynamics Rate Tuning', 'Real-Video Input Diagnostic')
replace('''<button class="ctrl-btn active" onclick="switchVideo('v-r2-right', 'clips/donor_transfer_fixed', this)">Coarse Donor Transfer (Fixed)</button>
            <button class="ctrl-btn" onclick="switchVideo('v-r2-right', 'clips/donor_recon_real', this)">Real Inversion Reference</button>''',
    '<span class="label-badge badge-control-model">Artifact arm tlo excluded</span>')
replace('Donor Band Transfer (Fixed)', 'Real-Video Reconstruction Example')
replace('src="clips/donor_transfer_fixed.', 'src="clips/donor_recon_real.')
start = s.index('      <!-- ROW 2:')
end = s.index('      <!-- ROW 3:')
part = s[start:end]
part = re.sub(r'Transferring coarse spatial noise bands.*?reproduce real motion\.',
    'E6 temporal-band (tlo) results were a whole-frame flicker ARTIFACT, caught by cross-check (#5600/#5634). That transfer asset is excluded here until its exact native arm can be authenticated. The displayed reconstruction example uses real-video information beyond frame 0 and is diagnostic. The source two-tool follow-up (#5608) left clock transfer unresolved; spatial/full arms near the real period also match their donors.', part, flags=re.S)
part = part.replace('Period Ratio to Reality', 'Source Reconstruction Ratio')
part = part.replace('P / P_real = 0.998 &ndash; 1.001', 'P / P_real = 1.005–1.009')
part = part.replace("Spatial 'slo' &amp; full 'all' arms; flicker index &lt; 0.01 (vs Base 0.880)",
    '<a href="https://github.com/srirangam-r/cosmos-swarm/blob/5155e31/work/dk2/e6x/tlo_artifact/redecide_q8.json">Two-tool follow-up #5608</a>; no general clock-transfer claim.')
s = s[:start] + part + s[end:]

replace('3. Stationary Action Forward-Dynamics Control', '3. Stationary Action — Replicated Finding')
replace('<a href="#5440">Finding #5440</a>', '<a href="https://github.com/srirangam-r/cosmos-swarm/tree/4ab9a29/work/dk1/t255_e2">Finding #5440 evidence</a>')
replace('Unconditioned / Own Action', 'Own Recorded Action')
replace('Zero "Stand Still" Action (Fixed)', 'Physical-Zero Action')
replace("Commanding a normalized physical zero-action vector (&Delta;a = 0) in forward-dynamics mode decisively suppresses robotic arm and scene hallucination, reducing residual motion to 22% of active rollout and proving Nano faithfully obeys stationary action directives.",
    'On 24 Bridge clips, a physical-zero action reduces motion relative to recorded actions. This is a stand-still control, not improved prediction of a moving robot: LPIPS to the real future was worse under zero. The independent fresh-seed replication (#5473) gives a drift ratio 0.208 [0.177, 0.258].')
replace('[0.198, 0.284] (24/24 clips &lt; 0.50; seed spread -85%)',
    '[0.198, 0.284], 24 clips × 3 seeds; <a href="https://github.com/srirangam-r/cosmos-swarm/tree/e67596f/work/dk2/rep5440">independent replication</a>. E3 action contrast was negative (#5566).')

replace('4. Two-Stage Dissipative Settle Prompt Conditioning', '4. Timed-Settle Prompt — Replicated Finding')
replace('<a href="#2720">Finding #2720</a>', '<a href="https://github.com/srirangam-r/cosmos-swarm/tree/3492d86/work/ro-1/cause_v7">Finding #2720 evidence</a>')
replace('Replicated Across 4 Agents', 'Independent Review: Task #121')
replace('Plain Cosmos3-Nano (Perpetual Bounce)', 'Recipe Prompt Without Timed Clause')
replace('Two-Stage Settle Prompt (Fixed)', 'Recipe Prompt With Timed Clause')
replace("Supplementing diffusion guidance with a structured two-stage settling clause overcomes Nano's perpetual motion bias, inducing real kinetic energy dissipation and bringing bouncing objects to true rest by frame 45 without degrading visual fidelity scores.",
    'On two GAUGE mid-fall inputs, the explicit bounce-count and timed-settle clause settled 5/6 clips versus 0/6 without it. The independent review in task121 supports this limited comparison. DOVER Δ = −0.004 ± 0.007 belongs only to these six pairs; it is not a whole-recipe scoreboard pass. Settling from images or prompts outside this setup remains a separate test.')
replace('85.0% Settle', '5/6 vs 0/6 Settled')
replace('17/20 clips settled (vs 0/20 base; terminal flow -85%)',
    '2 inputs × seeds 1–3; <a href="https://github.com/srirangam-r/cosmos-swarm/tree/620d29f/work/agy-2/task121_recipe_settle_review">independent task121 review</a>. Camera motion and glossy/larger balls remain caveats.')

replace('5. Earth-Gravity Free-Fall Sim-Proxy Adaptation', '5. Ball Proxy Illustration — Provisional / Results Pending')
replace('<a href="#5563">Task #266 Thread</a>', '<a href="https://github.com/srirangam-r/cosmos-swarm/tree/19626c4/work/rahul-3/t266">Frozen task266 driver</a>')
replace('Target: Free-Fall Gravity Constant (0.45 m/s&sup2; &rarr; 9.81 m/s&sup2;)', 'Target: Test Transfer of Specified Gravity')
replace('21&times; Acceleration Gain', 'Simulation Inputs Only')
replace('Uncalibrated Baseline Fall (g &approx; 4.90 m/s&sup2;)', 'Wrong-g Proxy Input (g = 4.905 m/s&sup2;)')
replace('Earth-Gravity Calibrated (g = 9.81 m/s&sup2;)', 'Target-g Proxy Input (g = 9.81 m/s&sup2;)')
replace("Supplying a calibrated parabolic trajectory sim-proxy during latent initialization forces Cosmos3-Nano to overcome its default slow-motion free-fall rate (0.45 m/s&sup2;), scaling downward acceleration to real gravitational acceleration (9.81 m/s&sup2;).",
    'These are analytical proxy inputs, not generated Nano outputs. Task266 has queued matched plain/proxy/wrong-g arms; its measured result is pending as of this review. The displayed g values are simulator settings with an assumed pixel-to-metre scale. They do not establish a Nano acceleration gain.')
replace('Effective Gravitational Acceleration', 'Generated Nano Measurement')
replace('<div class="metric-value">g = 9.81 m/s&sup2;</div>', '<div class="metric-value">Pending</div>')
replace('+2080% physical match over default Cosmos3-Nano (0.45 m/s&sup2;)', 'No measured improvement claimed; do not compare a simulator input with a published model baseline.')
replace('Self-contained HTML gallery with synchronized side-by-side video players. Re-encoded with FFmpeg H.264 &amp; VP9 at 416&times;240.',
    'Review copy built from existing gallery assets. Players share play, pause, restart and loop boundaries; native media and sidecars are still required for matched quantitative comparison.')

player = (HERE / 'player.js').read_text()
s = re.sub(r'  <script>.*?</script>', '  <script>\n' + player + '\n  </script>', s, flags=re.S)
(HERE / 'corrected_index.html').write_text(s)
# This copy can be served from the repo root without copying any media.
(HERE / 'preview.html').write_text(s.replace('clips/', '../../rahul-5-agy/gallery/clips/'))
path = 'work/rahul-5-agy/gallery/index.html'
(HERE / 'gallery-corrections.patch').write_text(''.join(difflib.unified_diff(
    old.splitlines(keepends=True), s.splitlines(keepends=True),
    fromfile='a/' + path, tofile='b/' + path)))
player_only = re.sub(r'  <script>.*?</script>', '  <script>\n' + player + '\n  </script>', old, flags=re.S)
(HERE / 'player-only.patch').write_text(''.join(difflib.unified_diff(
    old.splitlines(keepends=True), player_only.splitlines(keepends=True),
    fromfile='a/' + path, tofile='b/' + path)))
(HERE / 'source_sha256.txt').write_text(hashlib.sha256(old.encode()).hexdigest() + '\n')
print('Built review copy, preview, and patch; gallery source untouched.')
