import unittest

import numpy as np

from mocap_rebounds import fit_rebounds, synthetic


class ReboundTests(unittest.TestCase):
    def test_noiseless_sampled_flights(self):
        rng = np.random.default_rng(303)
        for _ in range(100):
            height, expected = synthetic(rng, 0)
            self.assertAlmostEqual(fit_rebounds(height)["ratio"], expected, places=8)

    def test_static_signal_is_rejected(self):
        with self.assertRaises(ValueError):
            fit_rebounds(np.ones(75) * 43)

    def test_clock_scale_cancels_in_ratio(self):
        height, _ = synthetic(np.random.default_rng(23), 0)
        self.assertAlmostEqual(fit_rebounds(height, 30)["ratio"],
                               fit_rebounds(height, 25)["ratio"], places=10)


if __name__ == "__main__":
    unittest.main()
