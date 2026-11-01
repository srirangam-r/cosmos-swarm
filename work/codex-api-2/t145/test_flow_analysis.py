import unittest

import numpy as np

from flow_analysis import affine_fit, describe_motion, summary


class FlowAnalysisTests(unittest.TestCase):
    def test_affine_matches_reference_code(self):
        flow = np.random.default_rng(27).normal(size=(240, 416, 2)).astype(np.float32)
        height, width = 240, 416
        yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
        design = np.stack([np.ones(height * width), xx.ravel() / width, yy.ravel() / height], 1)
        flat = flow.reshape(-1, 2)
        indices = np.arange(0, len(flat), 7)
        coefficients = np.linalg.lstsq(design[indices], flat[indices], rcond=None)[0]
        residuals = np.linalg.norm(design[indices] @ coefficients - flat[indices], axis=1)
        keep = indices[residuals < np.quantile(residuals, 0.8)]
        coefficients = np.linalg.lstsq(design[keep], flat[keep], rcond=None)[0]
        expected = (design @ coefficients).reshape(height, width, 2)
        np.testing.assert_array_equal(affine_fit(flow), expected)

    def test_windows_threshold_and_log(self):
        motion = np.arange(92, dtype=float) / 100
        actual = describe_motion(motion)
        self.assertEqual(actual["early"], float(motion[10:41].mean()))
        self.assertEqual(actual["late"], float(motion[60:].mean()))
        self.assertEqual(actual["late_log_plus_0_05"], float(np.log(motion[60:].mean() + 0.05)))
        self.assertEqual(actual["late_smoothed_max"], float(np.convolve(motion, np.ones(5) / 5, "valid")[60:].max()))
        self.assertFalse(actual["rest_proxy_threshold_0_5"])
        self.assertTrue(describe_motion(np.zeros(92))["rest_proxy_threshold_0_5"])

    def test_sample_standard_error(self):
        result = summary([1, 2, 3])
        self.assertEqual(result["n"], 3)
        self.assertAlmostEqual(result["mean"], 2)
        self.assertAlmostEqual(result["se"], 1 / np.sqrt(3))


if __name__ == "__main__":
    unittest.main()
