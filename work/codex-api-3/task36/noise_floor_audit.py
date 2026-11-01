import json
from pathlib import Path

import numpy as np

from compare_fit import first_two_segments


DIRECTORY = Path('work/codex-api-3/task36')
RNG_SEED = 20261101
SIMULATIONS = 30000


def design_for_segments(segments):
    rows = []
    for group, segment in enumerate(segments):
        for frame in segment:
            time = frame - np.mean(segment)
            row = np.zeros(5)
            row[0] = time * time
            row[1 + 2 * group:3 + 2 * group] = [time, 1]
            rows.append(row)
    return np.asarray(rows)


def separate_fit(values, segment):
    time = segment - np.mean(segment)
    design = np.column_stack((time ** 2, time, np.ones(len(segment))))
    residual = values[segment] - design @ np.linalg.lstsq(design, values[segment], rcond=None)[0]
    rss = float(residual @ residual)
    return {
        'frames': segment.tolist(),
        'n': len(segment),
        'rmse_px': float(np.sqrt(rss / len(segment))),
        'df_adjusted_residual_scale_px': float(np.sqrt(rss / (len(segment) - 3))),
    }


def simulate_gate(values, segments, rng):
    design = design_for_segments(segments)
    projection = np.eye(len(design)) - design @ np.linalg.pinv(design)
    noise = rng.standard_normal((SIMULATIONS, len(design))) @ projection
    lengths = [len(segment) for segment in segments]
    first = np.sqrt(np.mean(noise[:, :lengths[0]] ** 2, axis=1))
    second = np.sqrt(np.mean(noise[:, lengths[0]:] ** 2, axis=1))
    observed = np.concatenate([values[segment] for segment in segments]) @ projection
    observed_first = float(np.sqrt(np.mean(observed[:lengths[0]] ** 2)))
    observed_second = float(np.sqrt(np.mean(observed[lengths[0]:] ** 2)))
    output = {}
    for sigma in (1.0, 2.3, 3.0):
        reject = np.maximum(first, second) * sigma > 1.5
        fraction = float(np.mean(reject))
        extreme = np.maximum(first, second) * sigma >= max(observed_first, observed_second)
        output[str(sigma)] = {
            'rejection_fraction': fraction,
            'monte_carlo_se': float(np.sqrt(fraction * (1 - fraction) / SIMULATIONS)),
            'max_rmse_at_least_observed_count': int(np.sum(extreme)),
            'max_rmse_at_least_observed_fraction': float(np.mean(extreme)),
        }
    return {'observed_ols_segment_rmse_px': [observed_first, observed_second], 'noise_models': output}


def main():
    rng = np.random.default_rng(RNG_SEED)
    result = {
        'simulation_seed': RNG_SEED,
        'simulations_per_clip': SIMULATIONS,
        'scope': 'fixed observed segments; unrobust OLS residual gate only; not full tracker',
        'clips': {},
    }
    for ball in range(1, 5):
        source = json.loads((DIRECTORY / f'real{ball}_bounce_decay.json').read_text())
        values, segments = first_two_segments(source)
        trimmed = [segments[0][:-2], segments[1][2:-2]]
        result['clips'][f'real{ball}'] = {
            'peaks': source['peaks'],
            'trim_two_contact_adjacent_frames': [separate_fit(values, segment) for segment in trimmed],
            'full_segment_lengths': [len(segment) for segment in segments],
            'fixed_full_segment_gate_simulation': simulate_gate(values, segments, rng),
        }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
