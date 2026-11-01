import json
import unittest

import numpy as np

import mocap_alignment as audit


class AlignmentTests(unittest.TestCase):
    def test_recovers_exact_clock_and_projection(self):
        times = np.arange(90) / 30.0
        height = 400.0 - 100.0 * times + 20.0 * np.sin(7.0 * times)
        frames = np.arange(20, 65)
        true_offset = 10.0
        values = 360.0 - 0.55 * np.interp((frames - true_offset) / 25.0, times, height)
        loss, offset, coefficients = audit.align(
            frames, values, height, 30.0, [9.5, 10.0, 10.5])
        self.assertAlmostEqual(loss, 0.0, places=18)
        self.assertEqual(offset, true_offset)
        np.testing.assert_allclose(coefficients, [360.0, -0.55], atol=1e-10)

    def test_rejects_temporal_extrapolation(self):
        with self.assertRaises(ValueError):
            audit.align(np.array([0, 1, 2]), np.array([1, 2, 3]),
                        np.arange(30), 30.0, [1.0])

    def test_real_annotation_frames_held_out(self):
        for ball in range(1, 5):
            result = audit.evaluate(ball)
            annotated = {row["frame"] for row in result["heldout_annotated_centers"]}
            self.assertEqual(len(annotated), 4)
            self.assertFalse(annotated.intersection(result["fit_frames"]))
            self.assertFalse(annotated.intersection(result["sensitivity_common_fit_frames"]))
            json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
