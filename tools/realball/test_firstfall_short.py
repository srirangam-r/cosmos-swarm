"""Regression for incomplete tracks; no claim of tracker or physics validation."""
import unittest
from unittest.mock import patch
import numpy as np
import firstfall

class ShortTrack(unittest.TestCase):
    def run_track(self, y):
        n = len(y)
        def fake(F, point, pframe):
            return np.arange(n, dtype=float), np.array(y, dtype=float), np.ones(n)*100, {'minor': np.ones(n)*10}
        F = np.zeros((n, 8, 8, 3), dtype=np.uint8)
        with patch.object(firstfall, 'track', fake):
            return firstfall.measure(F, 24, ppm=100, nboot=10)[0]

    def test_short_tracks_flag_lost(self):
        for n in range(1, 6):
            with self.subTest(n=n):
                self.assertEqual(self.run_track(np.arange(n))['flag'], 'lost')

    def test_sufficient_track_fits(self):
        r = self.run_track(np.arange(20, dtype=float)**2)
        self.assertIn(r['flag'], ('ok', 'weak', 'no_free_fall'))
        self.assertTrue(np.isfinite(r['g']))

if __name__ == '__main__': unittest.main()
