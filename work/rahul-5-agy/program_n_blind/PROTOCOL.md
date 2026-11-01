# Program N: Independent Blind Second-Coder Protocol (rahul-5-agy)

**Status: Pre-registered protocol for Program N Tasks 225 & 226 (Raj #4464).**
**No deliverable edits.** Deliverables 1–3 and root `README.md` remain untouched until requested by humans.

---

## 1. Objectives & Scope
Per Raj's Program N directive (#4464):
- **Task 225 (N4, poornima-2 & poornima-3)**: Test whether a seed bank selected on contact events (clean fall / rest) generalizes to held-out GAUGE ball frames and prompts on the same GPU type, without selecting static clips.
- **Task 226 (N5, rahul-api & rahul-api-2)**: Test the boundaries of text control of motion across ball and pendulum events under shared noise.
- **Role of rahul-5-agy**: Act as an independent blind second coder for Tasks 225 and 226 when sheets/clip packs are staged, incorporating planted known-answer controls to ensure high-fidelity classification.

---

## 2. Blinding and Integrity Rules
To guarantee unbiased evaluation and eliminate confirmation bias:
1. **Zero Access to Generators or Keys**: Coder receives only anonymized clip IDs and contact sheets (or anonymized video clips). Prompt texts, noise seeds, arm conditions, model checkpoints, and unblinding keys are strictly withheld before coding.
2. **Cryptographic Code Freeze**:
   - All blind classifications are recorded in `blind_codes.csv`.
   - The SHA-256 hash of `blind_codes.csv` is computed and stored in `blind_codes.FROZEN.sha256`.
   - The SHA-256 checksum is committed and announced on the board (in the respective task thread or `#findings`) **before** receiving, opening, or joining with `blind_key.json`.
3. **Immutability After Unblinding**:
   - Once unblinded, the original code file is never edited.
   - Any subsequent adjudications or sensitivity evaluations are saved in separate explicit artifacts (e.g., `adjudicated_codes.csv`).

---

## 3. Standardized Coding Rubrics

### A. Contact & Rest Events (Task 225)
Standardized from poornima-2 `CODEBOOK.md` (#4181) and subsequent swarm consensus audits (#4226, #4271, #4316, #4373):
- **end_state**:
  - `REST`: Ball visible, resting on plank/table across final observation window (shift < 0.5 ball diameter).
  - `MOVING`: Ball visible and actively bouncing, rolling, sliding, or oscillating across final frames.
  - `HELD`: Ball attached to, held by, or suspended from gripper/robot arm.
  - `GONE`: Ball not visible within frame (exited camera boundaries or completely vanished).
  - `UNCLEAR`: Occluded, ambiguous object identity, or unresolved blur.
- **clone**:
  - `Y`: Two or more balls visible at any point in the clip.
  - `N`: Strictly single entity maintained throughout.
  - `U`: Unclear / ambiguous.
- **growth**:
  - `Y`: Ball apparent diameter visibly enlarges by $\ge 1.5\times$ relative to initial frame.
  - `N`: Normal scale maintained (within reasonable perspective variation).
  - `U`: Unclear.
- **retether**:
  - `Y`: Ball returns upward into gripper contact after initial drop.
  - `N`: Ball does not return to gripper.
  - `U`: Unclear.

### B. Text Control & Trajectory Events (Task 226)
Standardized vocabulary for text-vs-seed directional control:
- **motion_direction**:
  - `DOWNWARD`: Ball accelerates / falls downward.
  - `UPWARD`: Ball moves or is propelled upward (violating or reversing gravity).
  - `STATIONARY`: Object hovers or remains static in initial coordinates.
  - `SWINGING_NORMAL`: Pendulum exhibits standard oscillatory arc.
  - `SWINGING_FAST`: Pendulum exhibits accelerated / rapid period oscillation.
  - `FROZEN`: Pendulum does not oscillate; fixed in place.
  - `AMBIGUOUS`: Irregular, chaotic, or undecidable trajectory.
- **text_compliance**:
  - `COMPLIANT`: Macro-motion follows prompt directive (e.g., upward when prompted upward).
  - `NON_COMPLIANT`: Macro-motion defies prompt directive (e.g., falls downward despite prompt to go upward).
  - `UNCLEAR`: Prompt ambiguity or conflicting visual artifacts.

---

## 4. Ground-Truth & Planted Control Validation
In accordance with charter rules:
- Blind evaluation sheets should include interspersed known-answer controls (e.g. real GAUGE continuations with verified rest vs mid-flight, or referee planted cases).
- Coder accuracy on planted controls must be evaluated and reported alongside inter-rater agreement (Cohen's $\kappa$ and percent concordance).
