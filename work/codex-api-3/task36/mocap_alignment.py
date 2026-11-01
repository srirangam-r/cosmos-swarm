"""Exploratory comparison of real-video tracker centers to GAUGE mocap.

Run from the shared repository root after fetching the four documented JSONs.
The affine projection and relative clock are fitted to selected non-impact
frames. This is not a validated estimator of gravity or restitution.
"""
import csv
import json
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks

from compare_fit import first_two_segments


DIRECTORY = Path("work/codex-api-3/task36")
VIDEO_FPS = 25.0


def mocap_peaks(height):
    indices, _ = find_peaks(-height, prominence=10.0, distance=3)
    return indices


def align(frames, measured, height, mocap_fps, offset_grid):
    """Fit y = intercept + scale * z((frame-offset)/25)."""
    times = np.arange(len(height)) / mocap_fps
    best = None
    for offset in offset_grid:
        sample_times = (frames - offset) / VIDEO_FPS
        if sample_times.min() < times[0] or sample_times.max() > times[-1]:
            continue
        interpolated = np.interp(sample_times, times, height)
        design = np.column_stack((np.ones(len(frames)), interpolated))
        coefficients, _, rank, _ = np.linalg.lstsq(design, measured, rcond=None)
        if rank < 2 or not -0.75 <= coefficients[1] <= -0.35:
            continue
        residual = measured - design @ coefficients
        candidate = (float(np.mean(residual ** 2)), float(offset), coefficients)
        if best is None or candidate[0] < best[0]:
            best = candidate
    if best is None:
        raise ValueError("No admissible alignment")
    return best


def evaluate(ball):
    track = json.loads((DIRECTORY / f"real{ball}_bounce_decay.json").read_text())
    mocap = json.loads((DIRECTORY / "mocap" / f"{ball}.json").read_text())
    height = np.array(mocap["ball"]["z"], dtype=float)
    mocap_fps = float(mocap["FPS"])
    values, segments = first_two_segments(track)
    peaks = np.array(track["peaks"], dtype=int)
    reference_peaks = mocap_peaks(height)
    if len(reference_peaks) < 3:
        raise ValueError("Not enough prominent mocap impacts")
    anchor = peaks[0] - reference_peaks[0] * VIDEO_FPS / mocap_fps
    grid = np.linspace(anchor - 2.0, anchor + 2.0, 161)
    frames = np.concatenate(segments)
    with (DIRECTORY / "center_annotations.csv").open(newline="") as source:
        annotations = [row for row in csv.DictReader(source) if int(row["clip"]) == ball]
    annotation_frames = {int(row["frame"]) for row in annotations}
    fit_frames = np.array([frame for frame in frames
                           if np.min(np.abs(peaks[:2] - frame)) > 1
                           and frame not in annotation_frames], dtype=int)
    impact_frames = peaks[:2]
    rmse2, offset, coefficients = align(fit_frames, values[fit_frames], height,
                                         mocap_fps, grid)
    all_frames = np.arange(len(values))
    sample_times = (all_frames - offset) / VIDEO_FPS
    valid = (sample_times >= 0) & (sample_times <= (len(height) - 1) / mocap_fps)
    prediction = np.full(len(values), np.nan)
    prediction[valid] = coefficients[0] + coefficients[1] * np.interp(
        sample_times[valid], np.arange(len(height)) / mocap_fps, height)
    residual = values - prediction
    reference_in_video = offset + reference_peaks * VIDEO_FPS / mocap_fps
    comparisons = []
    for frame in peaks:
        distance = np.abs(reference_in_video - frame)
        index = int(np.argmin(distance))
        comparisons.append({"track_peak": int(frame),
                            "nearest_sampled_mocap_min_frame": float(reference_in_video[index]),
                            "difference_frames": float(frame - reference_in_video[index])})
    center_comparisons = []
    for row in annotations:
        frame = int(row["frame"])
        center_comparisons.append({"frame": frame, "phase": row["phase"],
                                   "mocap_projected_y_px": float(prediction[frame]),
                                   "tracker_error_px": float(residual[frame]),
                                   "manual_error_px": float(row["manual_y_px"]) - float(prediction[frame])})
    common_frames = fit_frames[(fit_frames - (offset + 1.0)) / VIDEO_FPS >= 0]
    common_frames = common_frames[(common_frames - (offset - 1.0)) / VIDEO_FPS
                                  <= (len(height) - 1) / mocap_fps]
    sensitivity = []
    for shift in (-1.0, -0.5, 0.0, 0.5, 1.0):
        alt_rmse2, alt_offset, alt_coefficients = align(
            common_frames, values[common_frames], height, mocap_fps, [offset + shift])
        annotated_frames = np.array([item["frame"] for item in center_comparisons])
        annotated_y = np.array([float(row["manual_y_px"]) for row in annotations])
        alt_z = np.interp((annotated_frames - alt_offset) / VIDEO_FPS,
                          np.arange(len(height)) / mocap_fps, height)
        alt_prediction = alt_coefficients[0] + alt_coefficients[1] * alt_z
        mae_delta = np.mean(np.abs(values[annotated_frames] - alt_prediction)
                            - np.abs(annotated_y - alt_prediction))
        sensitivity.append({"offset_shift_frames": shift,
                            "common_fit_rmse_px": float(np.sqrt(alt_rmse2)),
                            "tracker_minus_manual_mae_px": float(mae_delta)})
    return {"fit_frames": fit_frames.tolist(), "heldout_peak_frames": impact_frames.tolist(),
            "fit_rmse_px": float(np.sqrt(rmse2)), "clock_offset_frames": offset,
            "y_intercept_px": float(coefficients[0]), "scale_px_per_mm": float(coefficients[1]),
            "fit_residuals_px": [float(residual[frame]) for frame in fit_frames],
            "heldout_peak_residuals_px": [float(residual[frame]) for frame in impact_frames],
            "heldout_annotated_centers": center_comparisons,
            "sensitivity_common_fit_frames": common_frames.tolist(),
            "clock_sensitivity": sensitivity,
            "peak_comparisons": comparisons}


def main():
    output = {str(ball): evaluate(ball) for ball in range(1, 5)}
    print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
