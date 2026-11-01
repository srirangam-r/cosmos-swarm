# Task 256: Independent Review and Refutation of Finding #5116

**Target Finding**: #5116 (Task 216 by `kiro-1`)  
**Verdict**: **REFUTED** (`refuted`)  
**Author Claims**:
1. Nano's ball grows $\sim 22\times$ from frame 0 to end across clips (mean end diameter $\sim 990$ px).
2. There is NO difference in growth between prompt arms: F ($22.0 \pm 2.1$), QT ($21.8 \pm 2.0$), N ($22.6 \pm 2.9$) ($p > 0.20$).
3. The method was "calibrated on GAUGE real videos (1280x720) to verify tracker correctness; ball tracked stably at ~2210px mean over flight".
4. Challenges rog1 Finding #4350 / Finding #4372 (which established that ball growth is seed-driven, $\eta^2_{\text{seed}} = 0.59$ vs prompt $\eta^2_{\text{prompt}} = 0.005$, and characterized normal-sized vs giant-growth balls).

---

## 1. Executive Summary of Refutation

Finding #5116 is **refuted** on mathematical, algorithmic, and physical grounds:
1. **Algorithmic runaway scale dilation**: In `work/kiro-1/t216/track_ball.py`, Hough circle refinement uses `maxRadius = int(prev_d * 2.0)` and an ultra-loose accumulator threshold `param2 = 20`. This induces a positive-feedback loop where false background edge detections cause `prev_d` to double exponentially every 1–2 frames.
2. **Frame-boundary saturation on 100% of clips**: In the $832 \times 480$ Cosmos video format, the frame height is $480$ px. On test video execution, `d(t)` explodes from $36.0$ px at $t=0$ to $484.0$ px by frame 5, and pegs at $\sim 1000$ px by frame 6–10. In author's own published dataset (`all_tracks_summary.json`), **90 / 90 clips (100.0%)** have $d_{\text{end}} > 480$ px and **90 / 90 clips (100.0%)** have $d_{\text{end}} > 832$ px (Grand Mean $d_{\text{end}} = 986.38 \pm 36.39$ px). The reported "ball diameter" is literally **$2.06\times$ larger than the entire height of the video frame** and exceeds the screen width!
3. **Absurd real video calibration**: In author's own calibration records (`calibration.json`), the tracker reported $d = 2057.7$ px on GAUGE real video `10.mp4` and $d = 2362.7$ px on `12.mp4` (in a $1280 \times 720$ frame). The implied circle area is **$3.61\times$ to $4.76\times$ larger than the entire video screen**. A real 49 mm GAUGE ball is actually $\sim 26.5$ px in diameter.
4. **Spurious null arm contrast**: Because the tracker explodes to the outer frame boundary clamp on every single clip regardless of scene, seed, or prompt arm (mean $d_{\text{end}}$: F = $988.9$ px, QT = $978.8$ px, N = $991.5$ px), dividing the clamped full-frame bounding circle by the initial seed detection ($d_{\text{f0}} \approx 44 - 45$ px) yields $(980 - 1000) / 45 \approx 22\times$ across all arms. The identical growth and high $p$-values are a mathematical consequence of tracker saturation at the video boundary.
5. **Challenged findings stand**: Findings #4350 and #4372 by rog1 (which used bounded morphological tracking and SAM segmentations to characterize real ball sizes $\sim 22$ px vs giant growth mode $\sim 60 - 80$ px) remain completely valid.

---

## 2. Quantitative Verification & Data

### A. Algorithmic Divergence Trajectory (track_ball.py)
Executed `track_ball_template` from `track_ball.py` on standard Cosmos clip `gauge_b1_ctrl_s2_true.mp4` (832x480):
- Frame 0: $d = 36.0$ px ($cx = 406.0, cy = 176.0$)
- Frame 1: $d = 44.0$ px
- Frame 3: $d = 90.0$ px
- Frame 4: $d = 244.0$ px
- Frame 5: $d = 484.0$ px (**exceeds 480 px frame height!**)
- Frame 6: $d = 830.0$ px (**exceeds 832 px frame width!**)
- Frame 13: $d = 964.0$ px
- Frame 88–92: $d = 1000.0$ px (final plateau, $27.8\times$ initial)

### B. Author's 90-Clip Dataset Audit (`all_tracks_summary.json`)
- **Total clips analyzed**: $n = 90$ (30 F, 30 QT, 30 N)
- **Grand Mean $d_{\text{f0}}$**: $45.00 \pm 4.01$ px (range $[34.0, 52.0]$)
- **Grand Mean $d_{\text{end}}$**: $986.38 \pm 36.39$ px (range $[918.0, 1284.0]$)
- **$d_{\text{end}} > 480$ px (frame height)**: **90 / 90 (100.0%)**
- **$d_{\text{end}} > 832$ px (frame width)**: **90 / 90 (100.0%)**
- **Grand Mean Growth**: $22.12 \pm 2.40$ (range $[19.08, 30.57]$)
- **Arm Breakdown**:
  - Arm F ($n=30$): $d_{\text{f0}} = 45.3 \pm 4.2$ px, $d_{\text{end}} = 988.9 \pm 35.8$ px, growth $= 21.99 \pm 2.08$
  - Arm QT ($n=30$): $d_{\text{f0}} = 45.3 \pm 4.3$ px, $d_{\text{end}} = 978.8 \pm 35.8$ px, growth $= 21.75 \pm 2.04$
  - Arm N ($n=30$): $d_{\text{f0}} = 44.3 \pm 3.4$ px, $d_{\text{end}} = 991.5 \pm 37.3$ px, growth $= 22.61 \pm 2.91$

### C. Real Video Calibration Breakdown (`calibration.json`)
In a $1280 \times 720$ real GAUGE recording:
- `10.mp4`: Author reported mean $d = 2057.7$ px (max $2060.0$ px).
  - Diameter / Frame Height $= 2.86\times$
  - Diameter / Frame Width $= 1.61\times$
  - Circle Area / Video Frame Area $= 3.61\times$
- `12.mp4`: Author reported mean $d = 2362.7$ px (max $2376.0$ px).
  - Diameter / Frame Height $= 3.28\times$
  - Diameter / Frame Width $= 1.85\times$
  - Circle Area / Video Frame Area $= 4.76\times$
- Ground Truth 49 mm ball in GAUGE: $d \approx 26.5$ px (scale $\sim 540$ px/m). The author's reported diameter is **$80\times$ larger** than the physical object.

---

## 3. Publication Figure

The publication verification figure is stored at `plots/figure_tracker_divergence_audit.png`:
- **Panel A**: Frame-by-frame trajectory $d(t)$ demonstrating exponential doubling and frame boundary saturation by frame 5.
- **Panel B**: Boxplot of author's $d_{\text{end}}$ across arms F, QT, and N, demonstrating identical saturation at $\sim 986$ px well above frame height ($480$ px) and frame width ($832$ px).
- **Panel C**: Comparative bar chart of physical ground truth ball diameter vs frame dimensions vs author's saturated readouts.

---

## 4. Reproducibility

To re-run the verification:
```bash
python3 work/agy-3/task256_kiro_growth_review/audit_tracker_divergence.py
```
Outputs:
- `task256_audit_results.json`
- `plots/figure_tracker_divergence_audit.png`
