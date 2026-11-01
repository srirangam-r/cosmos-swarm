import json
from pathlib import Path

import numpy as np

from compare_fit import first_two_segments, fit


def main():
    directory = Path('work/codex-api-3/task36')
    centers = json.loads((directory / 'hough_comparison.json').read_text())
    results = {}
    for clip in range(1, 5):
        recorded = json.loads((directory / f'real{clip}_bounce_decay.json').read_text())
        original, segments = first_two_segments(recorded)
        substituted = original.copy()
        entries = centers['clips'][str(clip)]['entries']
        for entry in entries:
            substituted[entry['frame']] = entry['hough_y_px']
        original_fit = fit(original, segments, True)
        substituted_fit = fit(substituted, segments, True)
        results[str(clip)] = {
            'substituted_frames': [entry['frame'] for entry in entries],
            'original_training_rmse_px': original_fit['train_rmse_px'],
            'substituted_training_rmse_px': substituted_fit['train_rmse_px'],
            'original_segment_rmse_px': original_fit['segment_rmse_px'],
            'substituted_segment_rmse_px': substituted_fit['segment_rmse_px'],
        }
    deltas = np.array([result['substituted_training_rmse_px'] - result['original_training_rmse_px']
                       for result in results.values()])
    print(json.dumps({'clips': results, 'mean_training_delta_px': float(deltas.mean()),
                      'sample_se_px': float(deltas.std(ddof=1) / np.sqrt(len(deltas)))}, indent=2))


if __name__ == '__main__':
    main()
