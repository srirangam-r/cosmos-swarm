import csv
import json
from pathlib import Path

import numpy as np


def main():
    directory = Path('work/codex-api-3/task36')
    with (directory / 'center_annotations.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    results = {}
    for clip in range(1, 5):
        tracked = json.loads((directory / f'real{clip}_bounce_decay.json').read_text())['track_y']
        entries = []
        for row in rows:
            if int(row['clip']) != clip:
                continue
            frame = int(row['frame'])
            manual = float(row['manual_y_px'])
            entries.append({'frame': frame, 'phase': row['phase'], 'manual_y_px': manual,
                            'tracker_y_px': tracked[frame],
                            'tracker_minus_manual_px': round(tracked[frame] - manual, 2)})
        ascending = [item['tracker_minus_manual_px'] for item in entries if item['phase'] == 'ascending']
        descending = [item['tracker_minus_manual_px'] for item in entries if item['phase'] == 'descending']
        results[str(clip)] = {'entries': entries, 'ascending_bias_px': float(np.mean(ascending)),
                              'descending_bias_px': float(np.mean(descending)),
                              'phase_difference_px': float(np.mean(ascending) - np.mean(descending))}
    differences = np.array([value['phase_difference_px'] for value in results.values()])
    print(json.dumps({'clips': results, 'mean_phase_difference_px': float(differences.mean()),
                      'sample_se_px': float(differences.std(ddof=1) / np.sqrt(len(differences)))}, indent=2))


if __name__ == '__main__':
    main()
