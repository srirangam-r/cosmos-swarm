import json
from pathlib import Path

import numpy as np


def first_two_segments(result):
    values = np.array([float(value) if value is not None else np.nan for value in result['track_y']])
    peaks = result['peaks']
    segments = [np.arange(0, peaks[0]), np.arange(peaks[0] + 1, peaks[1])]
    segments = [segment[np.isfinite(values[segment])] for segment in segments]
    first = segments[0]
    start_y = np.median(values[first[:3]])
    leading = 0
    while leading < len(first) and abs(values[first[leading]] - start_y) <= 1:
        leading += 1
    descending = len(first) - 1
    while descending > 0 and values[first[descending]] - values[first[descending - 1]] > 0.3:
        descending -= 1
    segments[0] = first[max(leading - 1, descending - 1, 0):]
    for index, segment in enumerate(segments):
        if len(segment) < 3:
            continue
        stop = int(np.argmin(values[segment])) + 1
        while stop < len(segment) and values[segment[stop]] - values[segment[stop - 1]] > 0.3:
            stop += 1
        segments[index] = segment[:stop]
    return values, segments


def fit(values, segments, shared):
    rows = []
    observations = []
    labels = []
    for group, segment in enumerate(segments):
        midpoint = np.mean(segment)
        for frame in segment:
            time = frame - midpoint
            row = np.zeros(5 if shared else 6)
            if shared:
                row[0] = time * time
                row[1 + 2 * group:3 + 2 * group] = [time, 1]
            else:
                row[3 * group:3 * group + 3] = [time * time, time, 1]
            rows.append(row)
            observations.append(values[frame])
            labels.append(group)
    design = np.array(rows)
    observations = np.array(observations)
    labels = np.array(labels)
    coefficients, _, rank, _ = np.linalg.lstsq(design, observations, rcond=None)
    residuals = observations - design @ coefficients
    if rank != design.shape[1]:
        return {'error': 'rank deficient'}
    leverage = np.sum(design * (design @ np.linalg.inv(design.T @ design)), axis=1)
    loo = residuals / (1 - leverage)
    return {
        'coefficients_px_per_frame2': [float(coefficients[0])] if shared else [float(coefficients[0]), float(coefficients[3])],
        'train_rmse_px': float(np.sqrt(np.mean(residuals ** 2))),
        'segment_rmse_px': [float(np.sqrt(np.mean(residuals[labels == group] ** 2))) for group in range(2)],
        'loo_rmse_px': float(np.sqrt(np.mean(loo ** 2))),
        'max_leverage': float(max(leverage)),
        'residuals_px': [float(value) for value in residuals],
    }


def main():
    directory = Path('work/codex-api-3/task36')
    output = {}
    for ball in range(1, 5):
        result = json.loads((directory / f'real{ball}_bounce_decay.json').read_text())
        values, segments = first_two_segments(result)
        arms = {}
        for drop_adjacent in (0, 1, 2):
            selected = [segments[0][:-drop_adjacent] if drop_adjacent else segments[0],
                        segments[1][drop_adjacent:-drop_adjacent] if drop_adjacent else segments[1]]
            if min(map(len, selected)) < 4:
                continue
            arms[str(drop_adjacent)] = {'frames': [segment.tolist() for segment in selected],
                                       'shared': fit(values, selected, True),
                                       'free': fit(values, selected, False)}
        output[f'real{ball}'] = {'peaks': result['peaks'], 'arms': arms}
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
