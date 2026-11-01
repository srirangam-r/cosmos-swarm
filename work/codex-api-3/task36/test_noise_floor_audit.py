import unittest

import numpy as np

import noise_floor_audit as audit


class NoiseFloorAuditTests(unittest.TestCase):
    def test_design_reproduces_independent_intercepts_with_shared_curvature(self):
        segments = [np.arange(29, 37), np.arange(38, 48)]
        design = audit.design_for_segments(segments)
        coefficients = np.array([3.0, 2.0, 100.0, -4.0, 250.0])
        projection = np.eye(len(design)) - design @ np.linalg.pinv(design)
        self.assertEqual(np.linalg.matrix_rank(design), 5)
        np.testing.assert_allclose(projection @ (design @ coefficients), 0, atol=1e-10)
        np.testing.assert_allclose(projection @ projection, projection, atol=1e-10)

    def test_single_flight_quadratic_has_zero_residual(self):
        segment = np.arange(7, 14)
        values = np.zeros(14)
        values[segment] = 2 * segment ** 2 - 3 * segment + 5
        result = audit.separate_fit(values, segment)
        self.assertLess(result['rmse_px'], 1e-10)
        self.assertEqual(result['n'], 7)

    def test_rejection_increases_with_noise_scale(self):
        segments = [np.arange(8), np.arange(9, 19)]
        design = audit.design_for_segments(segments)
        values = np.zeros(19)
        values[np.concatenate(segments)] = design @ np.array([1, 2, 3, 4, 5])
        output = audit.simulate_gate(values, segments, np.random.default_rng(0))['noise_models']
        self.assertLess(output['1.0']['rejection_fraction'], 0.02)
        self.assertGreater(output['2.3']['rejection_fraction'], 0.90)
        self.assertGreater(output['3.0']['rejection_fraction'], output['2.3']['rejection_fraction'])


if __name__ == '__main__':
    unittest.main()
