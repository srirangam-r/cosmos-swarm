import json
import tempfile
import unittest
from pathlib import Path
from motion_fidelity import calculate


class MotionFidelityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        rows = {str(i): {'dd_binary': x, 'fps': 24} for i, x in enumerate([0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0])}
        (self.root / 'scores.json').write_text(json.dumps(rows))
        self.entry = lambda k: {'file': 'scores.json', 'key': str(k)}
        def prompt(name, ids):
            return {'id': name, 'clips': [dict(self.entry(k), seed=i) for i, k in enumerate(ids)]}
        self.data = {'bands': [{'id': '24fps', 'reference': [self.entry(0), self.entry(1)], 'prompts': [prompt('001', [2, 3, 4]), prompt('011', [5, 6, 7]), prompt('111', [8, 9, 10]), prompt('000', [11, 12, 13])]}]}

    def tearDown(self):
        self.tmp.cleanup()

    def calc(self, ddof=0, zero='zero'):
        return calculate(self.data, ddof, zero, self.root)

    def test_hand_calculated(self):
        band = self.calc()['bands'][0]
        for actual, expected in zip([p['mc'] for p in band['prompts']], [2/3, 1/3, 0, 0]):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(band['generated_dd'], .5)
        self.assertAlmostEqual(band['reference_dd'], .5)
        self.assertAlmostEqual(band['mf'], .75)
        self.assertTrue(band['prompts'][3]['zero_denominator'])
        sample = self.calc(ddof=1)['bands'][0]['prompts']
        self.assertAlmostEqual(sample[0]['mc'], .75)
        self.assertAlmostEqual(sample[1]['mc'], 3/7)
        with self.assertRaises(ValueError):
            self.calc(zero='error')

    def test_invalid_inputs(self):
        p = self.data['bands'][0]['prompts'][0]
        p['clips'][1]['seed'] = 0
        with self.assertRaises(ValueError): self.calc()
        p['clips'][1]['seed'] = 1
        p['clips'][1]['key'] = p['clips'][0]['key']
        with self.assertRaises(ValueError): self.calc()
        p['clips'][1]['key'] = '3'
        p['clips'].pop()
        with self.assertRaises(ValueError): self.calc()

    def test_fps_mismatch(self):
        path = self.root / 'scores.json'
        data = json.loads(path.read_text())
        data['1']['fps'] = 30
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError): self.calc()

if __name__ == '__main__': unittest.main()
