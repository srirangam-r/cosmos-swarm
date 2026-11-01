#!/usr/bin/env python3
"""Aggregate pre-scored clips using a user-curated manifest; see README."""
import argparse
import json
import math
from pathlib import Path
from statistics import mean


def calculate(manifest, ddof, zero_policy, root=Path('.')):
    if ddof not in (0, 1) or zero_policy not in ('zero', 'error'):
        raise ValueError('invalid variance or zero-denominator convention')
    cache = {}
    used = set()

    def get(entry):
        if not isinstance(entry, dict) or not isinstance(entry.get('file'), str) or not isinstance(entry.get('key'), str):
            raise ValueError('each clip must identify a score file and key')
        path = (root / entry['file']).resolve()
        ident = (str(path), entry['key'])
        if ident in used:
            raise ValueError(f'duplicate clip reference: {ident}')
        used.add(ident)
        if path not in cache:
            with path.open() as f:
                cache[path] = json.load(f)
        row = cache[path][entry['key']]
        dd, fps = row['dd_binary'], row['fps']
        if isinstance(dd, bool):
            dd = int(dd)
        if not isinstance(dd, (int, float)) or dd not in (0, 1):
            raise ValueError(f'non-binary DD for {ident}')
        if isinstance(fps, bool) or not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0:
            raise ValueError(f'invalid playback fps for {ident}')
        return dd, fps

    bands = manifest['bands']
    if not isinstance(bands, list) or not bands:
        raise ValueError('bands must be a non-empty list')
    result, band_ids = [], set()
    for band in bands:
        band_id = band['id']
        if not isinstance(band_id, str) or not band_id or band_id in band_ids:
            raise ValueError('band IDs must be unique nonempty strings')
        band_ids.add(band_id)
        ref = band['reference']
        prompts = band['prompts']
        if not isinstance(ref, list) or not ref or not isinstance(prompts, list) or not prompts:
            raise ValueError('each band needs reference clips and prompts')
        refs = [get(x) for x in ref]
        prompt_results, prompt_ids, fps_values = [], set(), [fps for _, fps in refs]
        for prompt in prompts:
            prompt_id, clips = prompt['id'], prompt['clips']
            if not isinstance(prompt_id, str) or not prompt_id or prompt_id in prompt_ids:
                raise ValueError('prompt IDs must be unique within a band')
            prompt_ids.add(prompt_id)
            if not isinstance(clips, list) or len(clips) != 3:
                raise ValueError(f'{prompt_id}: exactly three clips required')
            seeds = [x.get('seed') for x in clips]
            if any(isinstance(s, bool) or not isinstance(s, int) for s in seeds) or len(set(seeds)) != 3:
                raise ValueError(f'{prompt_id}: three distinct integer seeds required')
            values = [get(x) for x in clips]
            dd = [v[0] for v in values]
            fps_values.extend(v[1] for v in values)
            avg = mean(dd)
            var = sum((x-avg)**2 for x in dd) / (3-ddof)
            denom = var + avg**2
            if denom == 0 and zero_policy == 'error':
                raise ValueError(f'{prompt_id}: MC is undefined for all-static seeds')
            mc = var / denom if denom else 0.0
            prompt_results.append({'id': prompt_id, 'seeds': seeds, 'dd': dd, 'dd_mean': avg, 'variance': var, 'mc': mc, 'zero_denominator': denom == 0})
        # The report describes FPS bands; this tool requires matched playback fps,
        # rather than silently comparing disparate rates. Explicitly resample first.
        if max(fps_values) - min(fps_values) > max(0.01, 0.001 * max(fps_values)):
            raise ValueError(f'{band_id}: reference and generated playback fps differ')
        dd_ref = mean(x[0] for x in refs)
        dd_gen = mean(x['dd_mean'] for x in prompt_results)
        mc = mean(x['mc'] for x in prompt_results)
        result.append({'id': band_id, 'fps_range': [min(fps_values), max(fps_values)], 'reference_count': len(refs), 'reference_dd': dd_ref, 'generated_dd': dd_gen, 'mc': mc, 'mf': (1-abs(dd_gen-dd_ref))*(1-mc), 'prompts': prompt_results})
    return {'method': 'Cosmos 3 report eqs. 10-11; binary DD; equally weighted bands and prompts', 'ddof': ddof, 'zero_denominator_policy': zero_policy, 'bands': result, 'mean_mf_across_bands': mean(x['mf'] for x in result), 'limitations': 'Approximation: scorer differs from original VBench; input matching, distinct videos, generation metadata, fps, duration, and reference representativeness require manual audit. NVIDIA variance and zero conventions are unspecified.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=Path)
    p.add_argument('--ddof', type=int, choices=[0, 1], required=True)
    p.add_argument('--zero-denominator', choices=['zero', 'error'], required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    with args.manifest.open() as f:
        manifest = json.load(f)
    out = calculate(manifest, args.ddof, args.zero_denominator, args.manifest.resolve().parent)
    args.out.write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
