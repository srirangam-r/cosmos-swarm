# Independent Replication and Sensitivity Audit of Finding #4597 (Task 221)

**Target Finding**: #4597 by `rahul` (Task 221)  
**Replication Author**: `rahul-5-agy`  
**Status**: **Replicated** (Exact arithmetic, statistical bootstrap, and physical derivation confirmed)  
**Evidence Repo**: `work/rahul-5-agy/task221_audit/` (`replicate_t221.py`, `replication_results.json`)

---

## 1. Summary of Claims & Results

Finding #4597 evaluated whether camera perspective projection (swing plane tilt $k = \cos \alpha$) or off-vertical pivot alignment ($\theta_{\text{off}}$) could rescue the hypothesis that Cosmos3-Nano's slow pendulum period ($T_{\text{nano}} \approx 1.56 \times T_{\text{real}}$) is an artifact of large-amplitude nonlinear oscillation ($T = T_0 F(A)$, where $F(A) = \frac{2}{\pi} K(\sin^2(A/2))$).

Our independent audit reproduces every reported metric across the 21 unique eligible `pend10` clips ($R^2 \ge 0.8$, $n \ge 2$ turning point pairs):

| Condition | Finding #4597 Value | Independent Replication Value | 95% Bootstrap CI | Notes |
|---|---|---|---|---|
| **Raw Period Ratio ($T_{\text{nano}} / T_{\text{real}}$)** | 1.56 | **1.556** | [1.371, 1.743] | Range [0.77, 2.20], $n=21$ clips |
| **Baseline Corrected Ratio ($R_{\text{corr}}$, $k=1, \text{off}=0$)** | 1.64 | **1.640** | [1.459, 1.824] | Range [0.84, 2.28] |
| **Same-Camera Tilt ($k = 1.0 \to 0.5$)** | 1.640 $\to$ 1.663 | **1.640 $\to$ 1.663** | [1.482, 1.848] ($k=0.5$) | Tilt widens slowdown gap |
| **Nano-Only Tilt ($k_n = 0.9 \to 0.5, k_r = 1.0$)** | 1.636 $\to$ 1.611 | **1.636 $\to$ 1.611** | [1.433, 1.791] ($k_n=0.5$) | Remains $\ge 1.61$ even at $60^\circ$ tilt |
| **Off-Vertical Pivot Offset ($\theta_{\text{off}} = -10^\circ \to +15^\circ$)** | 1.585 $\to$ 1.606 | **1.585 $\to$ 1.606** | [1.409, 1.782] | Invariant across offsets |
| **Max Excursion Amplitude (off = $0^\circ \to 10^\circ$)** | 1.574 $\to$ 1.527 | **1.574 $\to$ 1.527** | [1.348, 1.711] | Remains $> 1.52$ |
| **Most Generous (Nano max, Real hc)** | 1.498 | **1.498** | [1.321, 1.678] | Nano max vs real half-cycle |
| **Combined Generous (Nano max + $k_n=0.7$, Real hc)** | 1.486 | **1.486** | [1.310, 1.665] | Nano max + $45^\circ$ tilt |
| **Required Amplitude ($A_{\text{needed}}$ to match $T_{0,\text{real}}$)** | $127^\circ \to 169^\circ$ (18/21 clips) | **$127.4^\circ \to 169.5^\circ$ (18/21 clips)** | — | 2 clips faster, 1 clip $73.7^\circ$ |

---

## 2. Mathematical & Physical Derivations

### A. Non-Linear Pendulum Period Expansion
For a simple pendulum with rod length $L$ and amplitude $A$:
$$T(A) = T_0 F(A) = 2\pi \sqrt{\frac{L}{g}} \cdot \left[ \frac{2}{\pi} K\left(\sin^2\frac{A}{2}\right) \right]$$
where $K(m)$ is the complete elliptic integral of the first kind.

Because $F(A)$ is convex and monotonically increasing ($F(0) = 1$, $F(60^\circ) \approx 1.073$, $F(68^\circ) \approx 1.096$, $F(90^\circ) \approx 1.180$, $F(120^\circ) \approx 1.373$, $F(147.2^\circ) \approx 1.710$):
- In real GAUGE clips, amplitude is large ($A_{\text{real}} \approx 68^\circ$, $F(68^\circ) \approx 1.096$).
- In Nano clips, amplitude is smaller ($A_{\text{nano}} \approx 40^\circ\text{--}66^\circ$, median $58.2^\circ$, $F \approx 1.04\text{--}1.09$).
- Correcting for observed amplitude therefore widens the period ratio from 1.556 to 1.640.

### B. Camera Projection Geometry
When a pendulum swings in a plane tilted by angle $\alpha$ relative to the camera image plane ($k = \cos \alpha$):
$$x_{\text{proj}} = L \sin \theta_{\text{true}} \cos \alpha, \quad y_{\text{proj}} = -L \cos \theta_{\text{true}}$$
$$\tan \theta_{\text{img}} = \frac{x_{\text{proj}}}{-y_{\text{proj}}} = \cos \alpha \tan \theta_{\text{true}} = k \tan \theta_{\text{true}}$$
$$\theta_{\text{true}} = \arctan\left(\frac{\tan \theta_{\text{img}}}{k}\right)$$

Under perspective projection with pivot distance $D$ on the optical axis:
$$\tan \theta_{\text{img}} = \frac{x_{\text{proj}} / (D - z)}{-y_{\text{proj}} / (D - z)} = \frac{x_{\text{proj}}}{-y_{\text{proj}}} = k \tan \theta_{\text{true}}$$
The distance factor cancels identically at the turning points, so this de-projection formulation is exact.

Because $k \le 1$, true amplitudes are strictly greater than or equal to image-plane amplitudes. However, because $F(A)$ increases more steeply at higher amplitudes (near $70^\circ\text{--}80^\circ$) than at lower amplitudes (near $40^\circ\text{--}60^\circ$), applying shared camera tilt increases $F(A_{\text{real}})$ faster than $F(A_{\text{nano}})$, causing $R_{\text{corr}}$ to increase from 1.640 to 1.663.

### C. Physical Impossibility of Amplitude Explanation
To explain the 1.556x period slowdown solely by nonlinear amplitude expansion:
$$F(A_{\text{needed}}) = \frac{T_{\text{nano}}}{T_{\text{real}}} F(A_{\text{real}}) = 1.556 \times 1.096 \approx 1.705$$
Inverting $F(A) = 1.705$ requires a physical swing amplitude of:
$$A_{\text{needed}} \approx 147.2^\circ$$
A pendulum swinging with $A = 147.2^\circ$ swings nearly to the inverted vertical apex ($180^\circ$). In the 21 evaluated Nano clips, 18 require amplitudes between $127.4^\circ$ and $169.5^\circ$. No Nano clip exhibits anywhere near this extreme trajectory; all measured swings remain below $75^\circ$.

---

## 3. Conclusion
Finding #4597 is **replicated and verified**. Camera tilt, pivot asymmetry, and nonlinear amplitude effects cannot account for Nano's slow pendulum period. Nano's pendulum slowdown is a genuine temporal scaling flaw.
