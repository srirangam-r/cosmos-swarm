"""Exploratory rebound-flight fits on GAUGE mocap; not a validated video tool."""
import json
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks


DIRECTORY = Path("work/codex-api-3/task36")


def fit_rebounds(height, fps=30.0, trim=0, floor=None):
    height = np.asarray(height, dtype=float)
    floor = float(np.median(height[-10:])) if floor is None else floor
    peaks, _ = find_peaks(-height, prominence=10, distance=3)
    if len(peaks) < 3:
        raise ValueError("fewer than three detected impacts")
    flights = []
    for left, right in zip(peaks[:2], peaks[1:3]):
        frames = np.arange(left + 1 + trim, right - trim)
        if len(frames) < 4:
            raise ValueError("too few interior samples")
        times = frames / fps
        coefficients = np.polyfit(times, height[frames] - floor, 2)
        roots = np.roots(coefficients)
        if (coefficients[0] >= 0 or np.iscomplex(roots).any()
                or roots.min() > times[0] or roots.max() < times[-1]):
            raise ValueError("flight does not bracket measured samples")
        duration = float(roots.max() - roots.min())
        residual = height[frames] - floor - np.polyval(coefficients, times)
        flights.append({"frames": frames.tolist(), "duration_s": duration,
                        "gravity_m_s2": float(-2 * coefficients[0] / 1000),
                        "rmse_mm": float(np.sqrt(np.mean(residual ** 2)))})
    return {"floor_mm": floor, "impact_frames": peaks[:3].tolist(),
            "flights": flights, "ratio": flights[1]["duration_s"] / flights[0]["duration_s"],
            "discrete_ratio": float((peaks[2] - peaks[1]) / (peaks[1] - peaks[0]))}


def synthetic(rng, noise):
    fps = 30.0
    gravity = 9810.0
    floor = 43.0
    height0 = rng.uniform(370, 400)
    first_e = rng.uniform(0.65, 0.80)
    second_e = rng.uniform(0.60, 0.85)
    impact = np.sqrt(2 * height0 / gravity) + rng.uniform(0, 1 / fps)
    velocity = np.sqrt(2 * gravity * height0) * first_e
    intervals = []
    for restitution in (second_e, 0.70, 0.70, 0.70, 0.70):
        duration = 2 * velocity / gravity
        intervals.append((impact, impact + duration, velocity))
        impact += duration
        velocity *= restitution
    times = np.arange(75) / fps
    values = np.full(len(times), floor)
    first_impact = intervals[0][0]
    age = np.maximum(times - (first_impact - np.sqrt(2 * height0 / gravity)), 0)
    mask = times < first_impact
    values[mask] += height0 - gravity * age[mask] ** 2 / 2
    for start, end, speed in intervals:
        mask = (times >= start) & (times < end)
        elapsed = times[mask] - start
        values[mask] += speed * elapsed - gravity * elapsed ** 2 / 2
    values += rng.normal(0, noise, len(values))
    return values, second_e


def main():
    result = {"real": {}, "synthetic": {}}
    for ball in range(1, 5):
        data = json.loads((DIRECTORY / "mocap" / f"{ball}.json").read_text())
        height = np.asarray(data["ball"]["z"])
        floor = float(np.median(height[-10:]))
        fits = {
            str(trim): fit_rebounds(data["ball"]["z"], data["FPS"], trim)
            for trim in (0, 1)}
        fits["floor_sensitivity"] = {
            str(delta): fit_rebounds(height, data["FPS"], floor=floor + delta)["ratio"]
            for delta in (-5, -2, 0, 2, 5)}
        result["real"][str(ball)] = fits
    for noise in (0.0, 0.5, 2.0):
        rng = np.random.default_rng(881122)
        errors = []
        failures = 0
        for _ in range(2000):
            height, target = synthetic(rng, noise)
            try:
                errors.append(fit_rebounds(height)["ratio"] - target)
            except ValueError:
                failures += 1
        errors = np.asarray(errors)
        result["synthetic"][str(noise)] = {
            "seed": 881122, "n_attempted": 2000, "n_returned": len(errors),
            "failures": failures, "bias": float(errors.mean()),
            "rmse": float(np.sqrt(np.mean(errors ** 2))),
            "absolute_error_p95": float(np.quantile(np.abs(errors), .95)),
            "absolute_error_max": float(np.max(np.abs(errors)))}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
