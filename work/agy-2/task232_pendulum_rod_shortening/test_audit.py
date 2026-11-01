#!/usr/bin/env python3
"""
Unit regression tests for Task 232 Independent Kinematic Audit.
Tests exact McNemar statistic, Fisher exact test, and geometric mean calculations.
"""

import unittest
import numpy as np
from scipy import stats

class TestAuditStats(unittest.TestCase):
    def test_mcnemar_exact(self):
        # 7 losses, 0 gains -> binomial(7, 0, 0.5) * 2 = 2 * (1/128) = 1/64 = 0.015625
        n = 7
        k = 0
        p_val = 2.0 * stats.binom.cdf(k, n, 0.5)
        self.assertAlmostEqual(p_val, 0.015625, places=6)
        
    def test_fisher_exact(self):
        # Orig: 8 pass, 2 fail; L50: 1 pass, 9 fail
        table = [[8, 2], [1, 9]]
        odds, p_val = stats.fisher_exact(table)
        self.assertAlmostEqual(odds, 36.0, places=4)
        self.assertAlmostEqual(p_val, 0.005477, places=5)
        
    def test_geometric_mean(self):
        vals = [2.0, 8.0]
        gm = float(np.exp(np.mean(np.log(vals))))
        self.assertAlmostEqual(gm, 4.0, places=5)

if __name__ == '__main__':
    unittest.main()
