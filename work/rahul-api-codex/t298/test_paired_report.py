"""Adversarial SOFTWARE tests. All periods and PASS documents are synthetic."""
import copy
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import paired_report as pr


def fixture(directory, factors=None, gain=1):
    directory = Path(directory)
    registry = dict(schema="t298-validation-v1", kind="synthetic", tools={})
    for tool in pr.TOOLS:
        method = "SYNTHETIC-ONLY-" + tool
        source_sha = pr.digest(method.encode())
        raw = dict(method=method, verdict="pass", synthetic=True)
        response = (json.dumps(raw, indent=2) + "\n").encode()
        path = directory / (tool + ".json")
        path.write_bytes(response)
        registry["tools"][tool] = dict(
            method=method, source_sha256=source_sha,
            referee_response_path=path.name,
            referee_response_sha256=pr.digest(response),
            evidence_url="synthetic://not-a-referee/" + tool)
    registry_path = directory / "validation.json"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n")
    rows = []
    for scene, seed, arm in pr.expected_slots():
        period = (1.6 if arm == "plain" else pr.TARGETS[arm]) * gain
        if factors and arm == "wrong":
            period = pr.TARGETS["proxy"] * factors[scene][pr.SEEDS.index(seed)] * gain
        identity = pr.job_id(scene, seed, arm)
        tools = {tool: dict(status="ok", period_s=period,
                            method=entry["method"], source_sha256=entry["source_sha256"])
                 for tool, entry in registry["tools"].items()}
        tools["crossing"]["reason"] = "measurable_unvalidated"
        rows.append(dict(id=identity, scene=scene, seed=seed, arm=arm,
                         clip_sha256=pr.digest(identity.encode()),
                         evidence_url="synthetic://not-a-video/" + identity,
                         flicker=.005,
                         strip=dict(single_bob_rod=True, reviewed_by="SYNTHETIC-FIXTURE",
                                    evidence_url="synthetic://not-a-strip/" + identity),
                         tools=tools))
    data = dict(schema=pr.SCHEMA, kind="synthetic", rows=rows)
    return data, pr.load_validation(registry_path), registry_path


def weighted_reference(factors):
    """Independent count-vector enumeration, not ordered-draw implementation."""
    counts = [(a, b, 3-a-b) for a in range(4) for b in range(4-a)]
    out = []
    for left, right in itertools.product(counts, repeat=2):
        log_total = 0
        weight = 1
        for scene, count in zip(pr.SCENES, (left, right)):
            log_total += sum(c * math.log(x) for c, x in zip(count, factors[scene]))
            weight *= 6 // math.prod(math.factorial(c) for c in count)
        out.extend([math.exp(log_total/6)] * weight)
    return sorted(out)


class PairedReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data, self.validation, self.registry = fixture(self.tmp.name)

    def report(self, data=None, validation=None):
        return pr.analyze(self.data if data is None else data,
                          self.validation if validation is None else validation)

    def assert_suppressed(self, result, accepted):
        self.assertEqual(result["coverage"]["planned"], 18)
        self.assertEqual(len(result["slots"]), 18)
        self.assertEqual(result["complete_guided_pairs"], accepted)
        self.assertIsNone(result["paired_intervals_by_tool"])

    def test_complete_prescribed_synthetic_transfer(self):
        result = self.report()
        self.assertEqual(result["kind"], "synthetic")
        self.assertEqual(result["status"], "SYNTHETIC_SOFTWARE_CHECK_ONLY")
        self.assertEqual(result["coverage"], dict(planned=18, present=18, technical_clean=18, accepted=18))
        self.assertEqual(result["complete_guided_pairs"], 6)
        self.assertEqual(len(result["paired_plain_comparisons"]), 12)
        for tool, interval in result["paired_intervals_by_tool"].items():
            self.assertEqual(interval["resamples"], 729)
            self.assertEqual(len(interval["samples_sorted"]), 729)
            self.assertAlmostEqual(interval["geometric_mean"], 1.7, places=14)
            for bound in interval["percentile_95"]:
                self.assertAlmostEqual(bound, 1.7, places=14)

    def test_exact_resamples_against_independent_weighted_enumeration(self):
        factors = {"real06": [1.2, 1.7, 2.4], "real14": [.9, 1.5, 2.2]}
        actual = pr.paired_bootstrap(factors)
        ref = weighted_reference(factors)
        self.assertEqual(len(ref), 729)
        for a, b in zip(actual["samples_sorted"], ref):
            self.assertAlmostEqual(a, b, places=14)
        self.assertAlmostEqual(actual["geometric_mean"], math.prod(sum(factors.values(), []))**(1/6))
        # Sorted729 linear percentile indices18.2 and709.8, independent formula.
        self.assertAlmostEqual(actual["percentile_95"][0], .8*ref[18]+.2*ref[19])
        self.assertAlmostEqual(actual["percentile_95"][1], .2*ref[709]+.8*ref[710])

    def test_pairing_cancels_same_seed_scale_changes(self):
        factors = [0.7, 1.1, 2.0]
        for row in self.data["rows"]:
            for reading in row["tools"].values():
                reading["period_s"] *= factors[pr.SEEDS.index(row["seed"])]
        result = self.report()
        self.assertEqual(result["complete_guided_pairs"], 6)
        for interval in result["paired_intervals_by_tool"].values():
            self.assertAlmostEqual(interval["percentile_95"][0], 1.7)
            self.assertAlmostEqual(interval["percentile_95"][1], 1.7)

    def test_right_ratio_can_have_twice_wrong_absolute_scale(self):
        data, validation, _ = fixture(self.tmp.name, gain=2)
        result = self.report(data, validation)
        for interval in result["paired_intervals_by_tool"].values():
            self.assertAlmostEqual(interval["geometric_mean"], 1.7)
        for slot in result["slots"]:
            for c in slot.get("prescribed_calibration", {}).values():
                self.assertAlmostEqual(c["measured_over_target"], 2)
                self.assertAlmostEqual(c["absolute_relative_error"], 1)

    def test_no_response_is_not_transfer(self):
        for row in self.data["rows"]:
            for r in row["tools"].values():
                r["period_s"] = 1.6
        result = self.report()
        for interval in result["paired_intervals_by_tool"].values():
            self.assertAlmostEqual(interval["geometric_mean"], 1)

    def test_missing_guided_clip_retains_all_slots_and_no_interval(self):
        self.data["rows"].pop(1)
        result = self.report()
        self.assert_suppressed(result, 5)
        self.assertEqual(result["coverage"]["present"], 17)
        self.assertEqual(result["slots"][1]["issues"], ["missing_planned_clip"])

    def test_missing_plain_does_not_remove_guided_pair(self):
        self.data["rows"].pop(0)
        result = self.report()
        self.assertEqual(result["complete_guided_pairs"], 6)
        self.assertEqual(result["coverage"]["present"], 17)
        self.assertEqual(sum(p["accepted"] for p in result["paired_plain_comparisons"]), 10)

    def test_empty_and_selective_success_cannot_hide_denominator(self):
        result = self.report(dict(self.data, rows=[]))
        self.assert_suppressed(result, 0)
        self.assertEqual(result["coverage"]["present"], 0)
        result = self.report(dict(self.data, rows=self.data["rows"][:3]))
        self.assert_suppressed(result, 1)
        self.assertEqual(result["coverage"]["accepted"], 3)
        self.assertEqual(result["coverage_by_scene"]["real14"]["planned"], 9)

    def test_each_required_tool_can_independently_fail(self):
        for tool in pr.TOOLS:
            with self.subTest(tool=tool):
                data = copy.deepcopy(self.data)
                data["rows"][1]["tools"][tool]["status"] = "failed"
                result = self.report(data)
                self.assert_suppressed(result, 5)
                self.assertIn(tool+":tool_not_ok", result["slots"][1]["issues"])

    def test_candidate_period_never_promoted(self):
        reading = self.data["rows"][1]["tools"]["crossing"]
        reading.update(reason="unstable_intervals", candidate_period_s=1.186)
        # Even a stale numeric period_s cannot bypass the reason gate.
        self.assert_suppressed(self.report(), 5)
        del reading["period_s"]
        self.assert_suppressed(self.report(), 5)

    def test_flicker_contract_including_boundary_and_nonfinite(self):
        for value in (0, .079999):
            self.data["rows"][1]["flicker"] = value
            self.assertEqual(self.report()["complete_guided_pairs"], 6)
        for value in (.08, -.001, None, True, "0.01", float("nan"), float("inf")):
            with self.subTest(value=value):
                self.data["rows"][1]["flicker"] = value
                self.assert_suppressed(self.report(), 5)

    def test_single_bob_strip_evidence_required(self):
        for field, value in (("single_bob_rod", False), ("single_bob_rod", "true"),
                             ("reviewed_by", ""), ("evidence_url", "")):
            data = copy.deepcopy(self.data)
            data["rows"][1]["strip"][field] = value
            self.assert_suppressed(self.report(data), 5)

    def test_all_three_agreement_boundary_and_disagreement(self):
        row = self.data["rows"][1]
        for reading in row["tools"].values():
            reading["period_s"] = 1
        row["tools"]["pend_acf"]["period_s"] = 1.1
        self.assertEqual(self.report()["complete_guided_pairs"], 6)
        row["tools"]["pend_acf"]["period_s"] = 1.10001
        result = self.report()
        self.assert_suppressed(result, 5)
        self.assertIn("three_tool_disagreement_gt_10pct", result["slots"][1]["issues"])

    def test_invalid_periods_do_not_count_as_success(self):
        for value in (None, 0, -1, True, "1.186", float("nan"), float("inf")):
            data = copy.deepcopy(self.data)
            data["rows"][1]["tools"]["crossing"]["period_s"] = value
            self.assert_suppressed(self.report(data), 5)

    def test_method_hash_or_string_mismatch(self):
        for field, value in (("method", "another-method"), ("source_sha256", "0"*64)):
            data = copy.deepcopy(self.data)
            data["rows"][1]["tools"]["crossing"][field] = value
            self.assert_suppressed(self.report(data), 5)

    def test_unvalidated_is_separate_from_technical_clean(self):
        self.validation["crossing"]["passed"] = False
        result = self.report()
        self.assert_suppressed(result, 0)
        self.assertEqual(result["coverage"]["technical_clean"], 18)
        self.assertEqual(result["coverage"]["accepted"], 0)
        self.assertEqual(result["slots"][1]["validation_issues"], ["crossing:UNVALIDATED"])
        self.assertAlmostEqual(result["guided_pairs"][0]["raw_wrong_over_proxy"]["crossing"], 1.7)
        self.assertIsNone(result["guided_pairs"][0]["accepted_wrong_over_proxy"])

    def test_raw_fail_overrides_perfect_pass_rate_and_same_method(self):
        raw_path = Path(self.tmp.name) / "crossing.json"
        raw = pr.read_json(raw_path)
        raw.update(verdict="fail", pass_rate=1, estimates_scored=4, within_tolerance=4)
        response = (json.dumps(raw) + "\n").encode()
        raw_path.write_bytes(response)
        registry = pr.read_json(self.registry)
        registry["tools"]["crossing"]["referee_response_sha256"] = pr.digest(response)
        self.registry.write_text(json.dumps(registry))
        validation = pr.load_validation(self.registry)
        self.assertFalse(validation["crossing"]["passed"])
        self.assertIn("raw_referee_not_pass", validation["crossing"]["errors"])
        self.assert_suppressed(self.report(validation=validation), 0)

    def test_tampered_response_and_wrong_method_rejected(self):
        raw_path = Path(self.tmp.name) / "crossing.json"
        raw_path.write_text(json.dumps(dict(method="wrong", verdict="pass")))
        validation = pr.load_validation(self.registry)
        self.assertFalse(validation["crossing"]["passed"])
        self.assertIn("response_hash_mismatch", validation["crossing"]["errors"])
        self.assertIn("referee_method_mismatch", validation["crossing"]["errors"])

    def test_measured_input_rejects_synthetic_validation(self):
        with self.assertRaisesRegex(ValueError, "synthetic validation"):
            self.report(dict(self.data, kind="measured"))

    def test_relabeling_registry_does_not_promote_synthetic_pass_files(self):
        registry = pr.read_json(self.registry)
        registry["kind"] = "referee"
        self.registry.write_text(json.dumps(registry))
        validation = pr.load_validation(self.registry)
        self.assertTrue(all(not v["passed"] for v in validation.values()))
        self.assertTrue(all("synthetic_response_not_referee_evidence" in v["errors"]
                            for v in validation.values()))

    def test_plain_seed_spread_and_paired_differences_are_separate(self):
        for row in self.data["rows"]:
            if row["arm"] == "plain":
                for r in row["tools"].values():
                    r["period_s"] = [1, 2, 3][pr.SEEDS.index(row["seed"])]
        result = self.report()
        for summary in result["descriptive_seed_dispersion"]:
            if summary["arm"] == "plain":
                for values in summary["complete_seed_summary_by_tool"].values():
                    self.assertEqual(values["mean_s"], 2)
                    self.assertEqual(values["sample_sd_s"], 1)
                    self.assertEqual(values["cv"], .5)
        for pair in result["guided_pairs"]:
            for delta in pair["accepted_wrong_minus_proxy_s"].values():
                self.assertAlmostEqual(delta, 2.0162-1.186)

    def test_actual_289_fail_response_stays_unvalidated(self):
        # No referee request and no planted clip is opened by this test.
        actual_path = Path(__file__).parent / "fixtures" / "actual_289_referee_response.json"
        if not actual_path.exists():
            self.fail("packaged raw289 FAIL fixture missing")
        response = actual_path.read_bytes()
        raw = pr.read_json(actual_path)
        self.assertEqual(raw["verdict"], "fail")
        self.assertEqual(raw["pass_rate"], 1)
        destination = Path(self.tmp.name) / "actual_response.json"
        destination.write_bytes(response)
        registry = pr.read_json(self.registry)
        entry = registry["tools"]["crossing"]
        entry.update(method=raw["method"],
                     source_sha256="d5bb5a444754253751b145b776dce9e5a1e4124b0f63235e9337894350547e8c",
                     referee_response_path=destination.name,
                     referee_response_sha256=pr.digest(response),
                     evidence_url="https://github.com/srirangam-r/cosmos-swarm/blob/0f135ad/work/ro-sol1/t289/referee_response.json")
        self.registry.write_text(json.dumps(registry))
        for row in self.data["rows"]:
            row["tools"]["crossing"].update(method=entry["method"], source_sha256=entry["source_sha256"])
        validation = pr.load_validation(self.registry)
        self.assert_suppressed(self.report(validation=validation), 0)
        self.assertEqual(self.report(validation=validation)["coverage"]["technical_clean"], 18)

    def test_duplicates_unknown_slots_and_mislabeled_ids_rejected(self):
        data = copy.deepcopy(self.data)
        data["rows"].append(data["rows"][0])
        with self.assertRaisesRegex(ValueError, "duplicate planned slot"):
            self.report(data)
        for field, value in (("scene", "real99"), ("seed", 999), ("seed", True),
                             ("arm", "extra"), ("id", "wrong")):
            data = copy.deepcopy(self.data)
            data["rows"][0][field] = value
            with self.assertRaises(ValueError):
                self.report(data)

    def test_strict_json_and_finite_output(self):
        path = Path(self.tmp.name) / "bad.json"
        for raw in ('{"rows":[],"rows":[]}', '{"x":NaN}', '{"x":Infinity}'):
            path.write_text(raw)
            with self.assertRaises(ValueError):
                pr.read_json(path)
        json.dumps(self.report(), allow_nan=False)

    def test_cli_end_to_end_records_input_source_hashes(self):
        directory = Path(self.tmp.name)
        obs, out = directory / "observations.json", directory / "report.json"
        obs.write_text(json.dumps(self.data))
        subprocess.run([sys.executable, str(Path(pr.__file__).resolve()), str(obs),
                        "--validation", str(self.registry), "--out", str(out)], check=True)
        result = pr.read_json(out)
        self.assertEqual(result["input_sha256"], pr.digest(obs.read_bytes()))
        self.assertEqual(result["report_source_sha256"], pr.digest(Path(pr.__file__).read_bytes()))
        self.assertEqual(result["coverage"]["planned"], 18)


if __name__ == "__main__":
    unittest.main(verbosity=2)
