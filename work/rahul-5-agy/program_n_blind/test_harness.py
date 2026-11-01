#!/usr/bin/env python3
"""Unit tests for Program N Blind Coding Harness."""

import os
import tempfile
import unittest
import math
from harness import (
    compute_sha256,
    freeze_file,
    validate_contact_row,
    validate_motion_row,
    compute_cohen_kappa,
    evaluate_planted_controls,
)


class TestHarness(unittest.TestCase):
    def test_sha256_and_freeze(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("test_content_for_hash")
            tmp_path = f.name
        try:
            sha = compute_sha256(tmp_path)
            self.assertEqual(len(sha), 64)
            hash_path = f"{tmp_path}.FROZEN.sha256"
            freeze_file(tmp_path)
            self.assertTrue(os.path.exists(hash_path))
            with open(hash_path) as hf:
                content = hf.read()
            self.assertIn(sha, content)
            os.remove(hash_path)
        finally:
            os.remove(tmp_path)

    def test_validate_contact_row(self):
        # Valid row
        valid_row = {
            "id": "clip_001",
            "end_state": "REST",
            "clone": "N",
            "growth": "N",
            "retether": "N",
            "confidence": "H"
        }
        self.assertEqual(validate_contact_row(valid_row, 1), [])

        # Invalid end_state and confidence
        invalid_row = {
            "id": "clip_002",
            "end_state": "FLOATING",
            "clone": "MAYBE",
            "growth": "N",
            "confidence": "X"
        }
        errors = validate_contact_row(invalid_row, 2)
        self.assertEqual(len(errors), 3)

    def test_validate_motion_row(self):
        valid_row = {
            "id": "pend_01",
            "motion_direction": "SWINGING_NORMAL",
            "text_compliance": "COMPLIANT"
        }
        self.assertEqual(validate_motion_row(valid_row, 1), [])

        invalid_row = {
            "id": "pend_02",
            "motion_direction": "WARPING",
            "text_compliance": "UNKNOWN"
        }
        errors = validate_motion_row(invalid_row, 2)
        self.assertEqual(len(errors), 2)

    def test_compute_cohen_kappa(self):
        # Perfect agreement
        r1 = ["REST", "MOVING", "REST", "HELD"]
        r2 = ["REST", "MOVING", "REST", "HELD"]
        res = compute_cohen_kappa(r1, r2)
        self.assertEqual(res["observed_agreement"], 1.0)
        self.assertEqual(res["kappa"], 1.0)

        # Partial agreement
        r1 = ["REST", "REST", "MOVING", "MOVING"]
        r2 = ["REST", "MOVING", "REST", "MOVING"]
        res = compute_cohen_kappa(r1, r2)
        self.assertEqual(res["observed_agreement"], 0.5)
        self.assertTrue(res["kappa"] <= 0.1)

    def test_evaluate_planted_controls(self):
        codes = [
            {"id": "plant_1", "end_state": "REST"},
            {"id": "plant_2", "end_state": "MOVING"},
            {"id": "unknown_3", "end_state": "REST"},
        ]
        gt = {
            "plant_1": "REST",
            "plant_2": "MOVING"
        }
        res = evaluate_planted_controls(codes, gt)
        self.assertEqual(res["total_controls"], 2)
        self.assertEqual(res["correct"], 2)
        self.assertEqual(res["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
