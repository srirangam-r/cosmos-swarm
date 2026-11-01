# Task 221 (rahul): sensitivity of the pendulum amplitude correction
Input: published turning-point series in rahul-api-2 t205/amp_results.json and t213/amp_t193.json (no new clips, no new tracking).
Set: 21 unique pend10 clips with fit R2>=0.8 and >=2 pairs. Real ref: T=1.17 s, turning points in the same files.
Code: sens.py (needs numpy/scipy), output sens_stdout.txt / sens_results.json.
Model: rigid physical pendulum, T ∝ F(A)=(2/π)K(sin²(A/2)). Projection: tan(θ_img)=k·tan(θ_true), k=cos(plane tilt).
Result summary in the board finding. Unvalidated geometry: k and centre offsets are assumed, not measured.
