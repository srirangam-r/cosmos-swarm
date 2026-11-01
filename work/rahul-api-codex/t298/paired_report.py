"""Frozen task277/5770 report; standard library only, no tracking or network.

Validation evidence must be supplied separately; row-level `validated` flags
are never read. This program binds evidence, it does not authenticate referees.
See README.md for the evidence boundary and synthetic-only example.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

SCENES = ("real06", "real14")
SEEDS = (101, 102, 103)
ARMS = ("plain", "proxy", "wrong")
TOOLS = ("crossing", "measure_pend", "pend_acf")
TARGETS = {"proxy": 1.186, "wrong": 2.0162}
SCHEMA = "t298-observations-v1"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def positive(value):
    return finite(value) and value > 0


def text(value):
    return isinstance(value, str) and bool(value.strip())


def no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key: " + key)
        out[key] = value
    return out


def read_json(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=no_duplicates,
                      parse_constant=lambda s: (_ for _ in ()).throw(
                          ValueError("nonfinite JSON constant: " + s)))


def load_validation(path):
    """Hash-check the exact raw response, retaining FAIL even at pass_rate=1.

    Registry entries pin code identity and the referee's exact method string.
    The executor/reviewer must independently check that evidence_url points to
    that real referee record; untrusted JSON can always forge a PASS document.
    """
    path = Path(path)
    registry = read_json(path)
    if registry.get("schema") != "t298-validation-v1":
        raise ValueError("validation schema")
    if registry.get("kind") not in ("synthetic", "referee"):
        raise ValueError("validation evidence kind")
    if set(registry.get("tools", {})) != set(TOOLS):
        raise ValueError("exactly three validation tool entries required")
    result = {}
    for tool in TOOLS:
        entry = registry["tools"][tool]
        errors, raw, actual_hash = [], {}, None
        if not text(entry.get("method")) or not sha(entry.get("source_sha256")):
            errors.append("method_identity_missing")
        if not text(entry.get("evidence_url")):
            errors.append("referee_evidence_missing")
        if not sha(entry.get("referee_response_sha256")):
            errors.append("response_hash_missing")
        try:
            response_path = path.parent / entry["referee_response_path"]
            response_bytes = response_path.read_bytes()
            actual_hash = digest(response_bytes)
            raw = read_json(response_path)
            if actual_hash != entry.get("referee_response_sha256"):
                errors.append("response_hash_mismatch")
        except (OSError, KeyError, TypeError, ValueError):
            errors.append("response_unreadable")
        if not isinstance(raw, dict):
            errors.append("response_not_object")
            raw = {}
        if raw.get("method") != entry.get("method"):
            errors.append("referee_method_mismatch")
        if raw.get("verdict") not in ("pass", "PASS"):
            errors.append("raw_referee_not_pass")
        if registry["kind"] == "referee" and raw.get("synthetic") is True:
            errors.append("synthetic_response_not_referee_evidence")
        result[tool] = dict(entry, passed=not errors, errors=errors,
                            evidence_kind=registry["kind"],
                            actual_response_sha256=actual_hash,
                            raw_verdict=raw.get("verdict"))
    return result


def job_id(scene, seed, arm):
    return f"t277_{scene}_{arm}_s{seed}"


def expected_slots():
    return [(scene, seed, arm) for scene in SCENES
            for seed in SEEDS for arm in ARMS]


def gate(row, validation):
    """Return raw observations, technical gate, and separate validation gate."""
    issues, validation_issues, periods, tool_issues = [], [], {}, {}
    if not sha(row.get("clip_sha256")) or not text(row.get("evidence_url")):
        issues.append("clip_evidence_missing")
    flicker = row.get("flicker")
    if not finite(flicker) or not 0 <= flicker < .08:
        issues.append("flicker_missing_or_outside_[0,.08)")
    strip = row.get("strip", {})
    if (not isinstance(strip, dict) or strip.get("single_bob_rod") is not True
            or not text(strip.get("reviewed_by"))
            or not text(strip.get("evidence_url"))):
        issues.append("single_bob_rod_strip_not_approved")
    readings = row.get("tools", {})
    if not isinstance(readings, dict):
        readings = {}
    if set(readings) != set(TOOLS):
        issues.append("exactly_three_tool_results_required")
    for tool in TOOLS:
        reading = readings.get(tool, {})
        errors = []
        if not isinstance(reading, dict):
            reading = {}
        if reading.get("status") != "ok":
            errors.append("tool_not_ok")
        if not positive(reading.get("period_s")):
            errors.append("period_not_finite_positive")
        if tool == "crossing" and reading.get("reason") != "measurable_unvalidated":
            errors.append("crossing_reason_not_accepted")
        method = validation[tool]
        if (reading.get("method") != method.get("method")
                or reading.get("source_sha256") != method.get("source_sha256")
                or not sha(reading.get("source_sha256"))):
            errors.append("method_identity_mismatch")
        if not method.get("passed"):
            validation_issues.append(tool + ":UNVALIDATED")
        if errors:
            tool_issues[tool] = errors
            issues.extend(tool + ":" + error for error in errors)
        else:
            periods[tool] = reading["period_s"]
    agreement = None
    if len(periods) == len(TOOLS):
        lo, hi = min(periods.values()), max(periods.values())
        agreement = hi / lo
        if hi > 1.1 * lo:
            issues.append("three_tool_disagreement_gt_10pct")
    return dict(technical_clean=not issues, accepted=not issues and not validation_issues,
                issues=issues, validation_issues=validation_issues,
                periods_s=periods, three_tool_max_over_min=agreement,
                tool_issues=tool_issues)


def quantile(sorted_values, q):
    position = q * (len(sorted_values) - 1)
    lo, hi = math.floor(position), math.ceil(position)
    return (sorted_values[lo] * (hi - position)
            + sorted_values[hi] * (position - lo)) if lo != hi else sorted_values[lo]


def paired_bootstrap(ratios_by_scene):
    """Exactly 3^3 * 3^3 equiprobable, fixed-scene, PAIRED seed resamples.

    Resample a proxy/wrong seed pair as a unit, three draws within each scene.
    Percentiles use linear interpolation at q*(729-1). Never resample tools,
    frames, crossing intervals, or the two selected scenes as independent units.
    """
    if set(ratios_by_scene) != set(SCENES):
        raise ValueError("two fixed scenes required")
    logs = {}
    for scene in SCENES:
        values = ratios_by_scene[scene]
        if len(values) != 3 or not all(positive(v) for v in values):
            raise ValueError("three finite positive paired ratios per scene required")
        logs[scene] = [math.log(v) for v in values]
    scene_means = {}
    for scene in SCENES:
        scene_means[scene] = [sum(logs[scene][i] for i in indices) / 3
                              for indices in itertools.product(range(3), repeat=3)]
    samples = sorted(math.exp((a + b) / 2) for a in scene_means[SCENES[0]]
                     for b in scene_means[SCENES[1]])
    return dict(geometric_mean=math.exp(sum(sum(v) for v in logs.values()) / 6),
                percentile_95=[quantile(samples, .025), quantile(samples, .975)],
                resamples=len(samples), samples_sorted=samples,
                uncertainty_scope="seed spread conditional on fixed real06/real14; not new scenes",
                percentile_method="linear interpolation at q*(729-1)")


def analyze(data, validation):
    if data.get("schema") != SCHEMA or data.get("kind") not in ("synthetic", "measured"):
        raise ValueError("observations schema/kind")
    if set(validation) != set(TOOLS):
        raise ValueError("exactly three validation entries required")
    if data["kind"] == "measured" and any(
            v.get("evidence_kind") != "referee" for v in validation.values()):
        raise ValueError("synthetic validation cannot support measured input")
    rows, observed = data.get("rows"), {}
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("row must be object")
        scene, seed, arm = row.get("scene"), row.get("seed"), row.get("arm")
        if (scene not in SCENES or type(seed) is not int or seed not in SEEDS
                or arm not in ARMS):
            raise ValueError("out-of-plan row")
        key = (scene, seed, arm)
        if row.get("id") != job_id(*key):
            raise ValueError("job ID/slot mismatch")
        if key in observed:
            raise ValueError("duplicate planned slot")
        observed[key] = row
    slots, indexed = [], {}
    for key in expected_slots():
        scene, seed, arm = key
        record = dict(id=job_id(*key), scene=scene, seed=seed, arm=arm)
        row = observed.get(key)
        if row is None:
            record.update(present=False, technical_clean=False, accepted=False,
                          issues=["missing_planned_clip"], validation_issues=[], periods_s={})
        else:
            record.update(present=True, raw=row, **gate(row, validation))
            if arm in TARGETS:
                target = TARGETS[arm]
                record["prescribed_calibration"] = {
                    tool: dict(target_s=target, measured_over_target=p / target,
                               signed_error_s=p-target, absolute_relative_error=abs(p / target-1))
                    for tool, p in record["periods_s"].items()}
        indexed[key] = record
        slots.append(record)
    pairs, plain_comparisons = [], []
    for scene in SCENES:
        for seed in SEEDS:
            plain, proxy, wrong = (indexed[scene, seed, arm] for arm in ARMS)
            complete = proxy["accepted"] and wrong["accepted"]
            raw_ratios = {tool: wrong["periods_s"][tool] / proxy["periods_s"][tool]
                          for tool in TOOLS if tool in proxy["periods_s"] and tool in wrong["periods_s"]}
            raw_differences = {tool: wrong["periods_s"][tool] - proxy["periods_s"][tool]
                               for tool in raw_ratios}
            pairs.append(dict(scene=scene, seed=seed, accepted=complete,
                              proxy_id=proxy["id"], wrong_id=wrong["id"],
                              raw_wrong_over_proxy=raw_ratios,
                              raw_wrong_minus_proxy_s=raw_differences,
                              accepted_wrong_minus_proxy_s=raw_differences if complete else None,
                              accepted_wrong_over_proxy=raw_ratios if complete else None))
            for arm, guided in (("proxy", proxy), ("wrong", wrong)):
                plain_ok = plain["accepted"] and guided["accepted"]
                values = {tool: dict(guided_over_plain=guided["periods_s"][tool] / plain["periods_s"][tool],
                                     guided_minus_plain_s=guided["periods_s"][tool]-plain["periods_s"][tool])
                          for tool in TOOLS if tool in plain["periods_s"] and tool in guided["periods_s"]}
                plain_comparisons.append(dict(scene=scene, seed=seed, guided_arm=arm,
                                              accepted=plain_ok, raw_by_tool=values,
                                              accepted_by_tool=values if plain_ok else None))
    complete_pairs = sum(p["accepted"] for p in pairs)
    interval = None
    if complete_pairs == 6:
        interval = {tool: paired_bootstrap({scene: [p["accepted_wrong_over_proxy"][tool]
                                                    for p in pairs if p["scene"] == scene]
                                           for scene in SCENES}) for tool in TOOLS}
    def coverage(subset):
        return dict(planned=len(subset), present=sum(s["present"] for s in subset),
                    technical_clean=sum(s["technical_clean"] for s in subset),
                    accepted=sum(s["accepted"] for s in subset))
    dispersion = []
    for scene in SCENES:
        for arm in ARMS:
            subset = [indexed[scene, seed, arm] for seed in SEEDS]
            complete = all(slot["accepted"] for slot in subset)
            by_tool = None
            if complete:
                by_tool = {}
                for tool in TOOLS:
                    values = [slot["periods_s"][tool] for slot in subset]
                    mean = sum(values) / 3
                    sd = math.sqrt(sum((value - mean)**2 for value in values) / 2)
                    by_tool[tool] = dict(n=3, mean_s=mean, sample_sd_s=sd,
                                         cv=sd/mean, min_s=min(values), max_s=max(values))
            dispersion.append(dict(scene=scene, arm=arm, accepted_seeds=sum(s["accepted"] for s in subset),
                                   complete_seed_summary_by_tool=by_tool))
    return dict(schema="t298-report-v1", kind=data["kind"],
                status=("SYNTHETIC_SOFTWARE_CHECK_ONLY" if data["kind"] == "synthetic"
                        else "NO_CLIPS" if not observed else "MEASUREMENT_SUMMARY_ONLY"),
                method_validation_status=("VALIDATED_METHODS_PER_SUPPLIED_RECORDS" if all(
                    v.get("passed") for v in validation.values()) else "UNVALIDATED"),
                validation=validation, coverage=coverage(slots),
                coverage_by_scene={scene: coverage([s for s in slots if s["scene"] == scene]) for scene in SCENES},
                coverage_by_arm={arm: coverage([s for s in slots if s["arm"] == arm]) for arm in ARMS},
                slots=slots, guided_pairs=pairs, complete_guided_pairs=complete_pairs,
                paired_intervals_by_tool=interval,
                interval_suppressed_reason=None if interval else "requires all6 validated guided pairs",
                supplied_wrong_over_proxy=TARGETS["wrong"] / TARGETS["proxy"],
                paired_plain_comparisons=plain_comparisons,
                descriptive_seed_dispersion=dispersion,
                limits=["Targets are prescribed periods, not observed real-scene periods.",
                        "No real-physics recovery, causal mechanism, improvement or NVIDIA-score claim is computed.",
                        "Input/builder/native-schedule/sidecar identity and media QA are separate executor gates.",
                        "Validation files must be independently checked against actual referee records.",
                        "Synthetic PASS fixtures are not evidence of planted validation."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations")
    parser.add_argument("--validation", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    data = read_json(args.observations)
    validation = load_validation(args.validation)
    report = analyze(data, validation)
    report["input_sha256"] = digest(Path(args.observations).read_bytes())
    report["validation_registry_sha256"] = digest(Path(args.validation).read_bytes())
    report["report_source_sha256"] = digest(Path(__file__).read_bytes())
    Path(args.out).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
