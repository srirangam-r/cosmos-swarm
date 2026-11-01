import tempfile
import unittest
from pathlib import Path

import numpy as np

import analyze_capture as analysis
import fetch_captures


class CaptureTests(unittest.TestCase):
    def test_complete_matrix_and_paired_contrasts(self):
        with tempfile.TemporaryDirectory() as directory:
            ball = np.zeros((24, 4096))
            ball[:, 0] = 1
            for scene in analysis.SCENES:
                for seed in analysis.SEEDS:
                    for arm in analysis.ARMS:
                        capture = np.zeros((24, 4096))
                        if arm == "R":
                            capture[:, 0] = 1
                        elif arm == "N2":
                            capture[:, 1] = 1
                        keys = {f"s{step:03d}_cond_L12_mean": capture for step in analysis.STEPS}
                        np.savez(Path(directory) / f"t145_{scene}_{arm}_s{seed}.npz", **keys)
            result = analysis.analyze(directory, ball)
            self.assertEqual(len(result["rows"]), 24)
            self.assertAlmostEqual(result["rows"][0]["R_minus_M"], 1)
            self.assertAlmostEqual(result["rows"][0]["N2_minus_N"], 0)
            self.assertAlmostEqual(result["rows"][0]["primary_difference"], 1)
            self.assertEqual(result["scene_summaries"][0]["primary_difference"]["n"], 3)
            self.assertEqual(result["across_scenes"][0]["primary_difference"]["n"], 4)

    def test_rejects_zero_direction_and_missing_capture(self):
        with self.assertRaises(ValueError):
            analysis.cosine(np.zeros(5), np.ones(5))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                analysis.analyze(directory, np.ones((24, 4096)))

    def test_local_queue_endpoint_and_artifact_id_validation(self):
        sidecar = {"endpoint_url": "http://127.0.0.1:8044", "artifact_ids": ["act_a12b"]}
        self.assertEqual(fetch_captures.artifact_url(sidecar), "http://100.111.167.68:8044/v1/artifacts/act_a12b")
        for endpoint in ("http://example.com:8044", "https://127.0.0.1:8044", "http://127.0.0.1:80"):
            with self.assertRaises(ValueError):
                fetch_captures.artifact_url({**sidecar, "endpoint_url": endpoint})
        with self.assertRaises(ValueError):
            fetch_captures.artifact_url({**sidecar, "artifact_ids": ["act_../../other"]})


if __name__ == "__main__":
    unittest.main()
