import csv
import json
from pathlib import Path

import cv2
import numpy as np


def main():
    directory = Path('work/codex-api-3/task36')
    with (directory / 'center_annotations.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    results = {}
    cells = []
    for clip in range(1, 5):
        tracked = json.loads((directory / f'real{clip}_bounce_decay.json').read_text())['track_y']
        video = (f'work/agy-4/task72_score_review/real_control_clips/'
                 f'real_ball_{clip}_f0_93f.mp4')
        capture = cv2.VideoCapture(video)
        entries = []
        for row in rows:
            if int(row['clip']) != clip:
                continue
            frame = int(row['frame'])
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame)
            success, image = capture.read()
            if not success:
                raise ValueError(f'cannot read {video}, frame {frame}')
            region = cv2.cvtColor(image[200:280, 265:340], cv2.COLOR_BGR2GRAY)
            region = cv2.GaussianBlur(region, (5, 5), 1)
            circles = cv2.HoughCircles(region, cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                                       param1=60, param2=15, minRadius=11, maxRadius=21)
            if circles is None or len(circles[0]) != 1:
                raise ValueError(f'expected one circle in {video}, frame {frame}')
            center_x, center_y, radius = circles[0][0].astype(float) + np.array([265, 200, 0])
            manual = float(row['manual_y_px'])
            entries.append({'frame': frame, 'phase': row['phase'], 'hough_x_px': center_x,
                            'hough_y_px': center_y, 'radius_px': radius, 'manual_y_px': manual,
                            'tracker_y_px': tracked[frame],
                            'tracker_minus_hough_px': round(tracked[frame] - center_y, 2),
                            'hough_minus_manual_px': round(center_y - manual, 2)})
            crop = image[200:280, 265:340].copy()
            cv2.circle(crop, (round(center_x - 265), round(center_y - 200)), round(radius),
                       (0, 255, 0), 1)
            cv2.line(crop, (0, round(tracked[frame] - 200)), (74, round(tracked[frame] - 200)),
                     (0, 0, 255), 1)
            cv2.putText(crop, f'{clip}:{frame}', (2, 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.35, (0, 255, 255), 1)
            cells.append(crop)
        ascending = [item['tracker_minus_hough_px'] for item in entries if item['phase'] == 'ascending']
        descending = [item['tracker_minus_hough_px'] for item in entries if item['phase'] == 'descending']
        results[str(clip)] = {'entries': entries, 'ascending_bias_px': float(np.mean(ascending)),
                              'descending_bias_px': float(np.mean(descending)),
                              'phase_difference_px': float(np.mean(ascending) - np.mean(descending))}
    differences = np.array([value['phase_difference_px'] for value in results.values()])
    manual_errors = [abs(entry['hough_minus_manual_px']) for result in results.values()
                     for entry in result['entries']]
    print(json.dumps({'clips': results, 'mean_phase_difference_px': float(differences.mean()),
                      'sample_se_px': float(differences.std(ddof=1) / np.sqrt(len(differences))),
                      'hough_manual_mean_abs_px': float(np.mean(manual_errors)),
                      'hough_manual_max_abs_px': float(np.max(manual_errors))}, indent=2))
    sheet = np.concatenate([np.concatenate(cells[i:i + 4], axis=1)
                            for i in range(0, len(cells), 4)], axis=0)
    sheet = cv2.resize(sheet, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
    if not cv2.imwrite(str(directory / 'hough_tracker_overlay.png'), sheet):
        raise ValueError('could not write sheet')


if __name__ == '__main__':
    main()
