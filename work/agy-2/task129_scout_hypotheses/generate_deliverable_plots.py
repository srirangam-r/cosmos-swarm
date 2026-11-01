import json
import numpy as np
import matplotlib.pyplot as plt
import os

out_dir = "/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task129_scout_hypotheses"
os.makedirs(f"{out_dir}/plots", exist_ok=True)

# 1. Plot Kinematics of Non-Settlers s22 and s23
with open(f"{out_dir}/nonsettlers_kinematics.json") as f:
    kin = json.load(f)

y_s22 = np.array(kin["s22"]["y"])
x_s22 = np.array(kin["s22"]["x"])
y_s23 = np.array(kin["s23"]["y"])
x_s23 = np.array(kin["s23"]["x"])
t = np.arange(len(y_s22)) / 24.0 # seconds

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Subplot 1: Vertical Trajectory y(t)
ax1 = axes[0]
ax1.plot(t, y_s22, label="Seed 22 (r60_8bf9f5): Table Micro-Hops (T)", color="#1f77b4", lw=2)
ax1.plot(t, y_s23, label="Seed 23 (r60_0c3579): 5-Frame Edge Loop (G)", color="#d62728", lw=2, linestyle="--")

# Reference lines
ax1.axhline(120, color="gray", linestyle=":", lw=1.5, label="Frame-0 / Gripper Pos (y≈120; Hyp A)")
ax1.axhline(335, color="saddlebrown", linestyle="-.", lw=1.5, label="Plank Surface (y≈335)")
ax1.axhline(395, color="black", linestyle="-.", lw=1.5, label="Table Surface (y≈395)")

ax1.set_xlabel("Time (s) [fps=24]", fontsize=11)
ax1.set_ylabel("Vertical Pixel Coordinate y (px, downward)", fontsize=11)
ax1.set_title("Ball 2 dd33 QT Kinematics: Decisive Refutation of Gripper Pull-Back (A)", fontsize=11, fontweight="bold")
ax1.invert_yaxis()
ax1.grid(True, alpha=0.3)
ax1.legend(loc="upper left", fontsize=8.5)

# Subplot 2: Spatial (x, y) Path
ax2 = axes[1]
ax2.plot(x_s22, y_s22, label="Seed 22: Corridor Center -> Table (x≈297)", color="#1f77b4", alpha=0.7, lw=1.8)
ax2.plot(x_s23, y_s23, label="Seed 23: Plank Edge Drift & 5f Loop (G)", color="#d62728", alpha=0.7, lw=1.8, linestyle="--")

# Draw plank footprint: x in [220, 360], y in [315, 345]
ax2.fill_between([220, 360], 315, 345, color="wheat", alpha=0.4, label="Wooden Plank Footprint")
ax2.scatter([x_s22[0]], [y_s22[0]], color="blue", marker="o", s=80, label="s22 Start (f0)")
ax2.scatter([x_s23[0]], [y_s23[0]], color="red", marker="^", s=80, label="s23 Start (f0)")
ax2.scatter([x_s22[-1]], [y_s22[-1]], color="blue", marker="X", s=90, label="s22 End (f92)")
ax2.scatter([x_s23[-1]], [y_s23[-1]], color="red", marker="X", s=90, label="s23 End (f92)")

ax2.set_xlabel("Horizontal Pixel Coordinate x (px)", fontsize=11)
ax2.set_ylabel("Vertical Pixel Coordinate y (px)", fontsize=11)
ax2.set_title("Spatial Drift & Geometric Template Entrapment (Hyp G)", fontsize=11, fontweight="bold")
ax2.invert_yaxis()
ax2.grid(True, alpha=0.3)
ax2.legend(loc="lower right", fontsize=8.5)

plt.tight_layout()
plt.savefig(f"{out_dir}/plots/ball2_dd33_kinematics.png", dpi=200)
plt.close()
print("Saved ball2_dd33_kinematics.png")

# 2. Plot Artifact Birth Timeline & Mechanism Categorization
artifacts = [
    {"name": "box_ctrl b2 s3", "f_birth": 24, "type": "Mode Interpolation (MI)", "coexist": "f24-50+", "loc": "Held (y≈135) + Landed (y≈315)"},
    {"name": "REC ball2 s1", "f_birth": 25, "type": "Mode Interpolation (MI)", "coexist": "f25-34", "loc": "Held (y≈125) + Plank (y≈327)"},
    {"name": "rog1 ball1 s23 (F)", "f_birth": 2, "type": "Motion Demand (K)", "coexist": "f4-11", "loc": "Left Boundary Entry (x≈0)"},
    {"name": "REC ball2 s2", "f_birth": 58, "type": "Motion Demand (K)", "coexist": "f58-92", "loc": "Ceiling Entry (y≈0-100)"},
    {"name": "pend10 restev s2", "f_birth": 32, "type": "Motion Demand (K)", "coexist": "f39-92", "loc": "T-Bifurcation (Axle/Bob)"},
    {"name": "REC ball1 s3", "f_birth": 30, "type": "Identity Breakdown (B)", "coexist": "f30-92", "loc": "Giant Sphere + Debris Field"},
    {"name": "REC ball2 s3", "f_birth": 35, "type": "Geometric Morphing (B)", "coexist": "f35-92", "loc": "Plank Phantom Box"},
    {"name": "rog1 ball1 s22 (F)", "f_birth": 14, "type": "Planar Breakdown (B)", "coexist": "f14-29", "loc": "Plank Tilt / Edge-On Flip"},
]

fig, ax = plt.subplots(figsize=(12, 6))

colors = {
    "Mode Interpolation (MI)": "#2ca02c",
    "Motion Demand (K)": "#d62728",
    "Identity Breakdown (B)": "#9467bd",
    "Geometric Morphing (B)": "#ff7f0e",
    "Planar Breakdown (B)": "#8c564b"
}

y_pos = np.arange(len(artifacts))
f_births = [a["f_birth"] for a in artifacts]
types = [a["type"] for a in artifacts]
c_list = [colors[t] for t in types]

# Shaded windows for MI early prediction vs K late prediction
ax.axvspan(0, 6, color="green", alpha=0.15, label="Scout-1 MI Prediction Window (f ≤ 6)")
ax.axvspan(36, 93, color="red", alpha=0.12, label="Scout-1 K Prediction Window (f > 36)")

bars = ax.barh(y_pos, f_births, color=c_list, height=0.55, edgecolor="black", alpha=0.85)

for i, a in enumerate(artifacts):
    ax.text(a["f_birth"] + 1.2, i, f"f{a['f_birth']} | {a['type']} ({a['loc']})", 
            va="center", fontsize=9, fontweight="medium")

ax.set_yticks(y_pos)
ax.set_yticklabels([a["name"] for a in artifacts], fontsize=10, fontweight="bold")
ax.set_xlabel("First Observable Artifact Appearance Frame (Native f0-f92)", fontsize=11)
ax.set_title("Empirical Birth Timeline of All 8 Gross Artifact Clips: Refutation of Unitary MI / K Hypotheses", fontsize=11, fontweight="bold")
ax.set_xlim(0, 95)
ax.grid(True, axis="x", alpha=0.3)
ax.invert_yaxis()
ax.legend(loc="lower right", fontsize=9.5)

plt.tight_layout()
plt.savefig(f"{out_dir}/plots/artifact_birth_timeline.png", dpi=200)
plt.close()
print("Saved artifact_birth_timeline.png")

# Save complete evidence ledger
with open(f"{out_dir}/task129_scout_hypotheses_ledger.json", "w") as f:
    json.dump({
        "artifact_cases": artifacts,
        "settling_cases": {
            "s22": {
                "clip_id": "r60_8bf9f5",
                "hypothesis_T_verdict": "SUPPORTED (late window-censoring: macroscopic bounce collapsed, micro-hops ≤2 px on table)",
                "hypothesis_A_verdict": "REFUTED (zero pull-back to gripper y≈120; sits at table y≈394)",
                "hypothesis_G_verdict": "CONSISTENT (falls to lower table surface)",
                "terminal_state": "Table contact micro-oscillation (y=393-395 px, x=297 px)"
            },
            "s23": {
                "clip_id": "r60_0c3579",
                "hypothesis_T_verdict": "REFUTED (undamped limit cycle, not purely late decay)",
                "hypothesis_A_verdict": "REFUTED (zero pull-back to gripper y≈120; loops y=356-379)",
                "hypothesis_G_verdict": "CONFIRMED (lateral plank run-off triggers 5-frame cyclic bounce between table and plank edge)",
                "terminal_state": "5-frame cyclic loop (y=356-379 px, x=294-308 px)"
            }
        },
        "synthesis": {
            "artifact_mechanism": "Mixed multi-factor etiology. Pure mode interpolation (MI) is refuted as a unitary explanation because 7/8 artifacts appear late (f >= 14, median f=25). However, MI correctly explains simultaneous held+landed superposition in box_ctrl and REC ball2 s1. Motion demand (K) drives late ceiling entry and prompt-forced pendulum bifurcation. Structural/identity dissolution accounts for debris and plank flips.",
            "settling_mechanism": "Hypothesis A (gripper pull-back) is decisively refuted across 2/2 non-settling clips (0/2 show return to frame-0 height). Non-settling splits into window censoring (Hypothesis T, 1/2) and geometric plank-boundary loop entrapment (Hypothesis G, 1/2)."
        }
    }, f, indent=2)
print("Saved task129_scout_hypotheses_ledger.json")
