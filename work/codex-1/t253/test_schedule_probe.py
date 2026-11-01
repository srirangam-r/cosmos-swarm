import unittest
from schedule_probe import trace_schedule


class Scheduler:
    def __init__(self):
        self.timesteps = [9, 5, 1]
        self.sigmas = [0.9, 0.5, 0.1, 0.0]

    def step(self, output, timestep, sample):
        return output + timestep + sample


class TestTrace(unittest.TestCase):
    def test_capture_is_a_snapshot_and_does_not_change_steps(self):
        s = Scheduler()
        with trace_schedule(s) as trace:
            results = [s.step(2, t, 3) for t in s.timesteps]
        s.timesteps[0] = 999
        s.sigmas[0] = 999
        self.assertEqual(results, [14, 10, 6])
        self.assertEqual(trace['timesteps'], [9, 5, 1])
        self.assertEqual(trace['sigmas'], [0.9, 0.5, 0.1, 0.0])
        self.assertEqual(trace['step_timesteps'], [9, 5, 1])
        self.assertNotIn('step', vars(s))

    def test_no_steps_and_exception_restore_original(self):
        s = Scheduler()
        with self.assertRaisesRegex(RuntimeError, 'test'):
            with trace_schedule(s) as trace:
                raise RuntimeError('test')
        self.assertIsNone(trace['timesteps'])
        self.assertNotIn('step', vars(s))
        self.assertEqual(s.step(2, 1, 3), 6)

    def test_instance_override_is_restored(self):
        s = Scheduler()
        fn = lambda *args: 7
        s.step = fn
        with trace_schedule(s):
            self.assertEqual(s.step(1, 2, 3), 7)
        self.assertIs(s.step, fn)


if __name__ == '__main__':
    unittest.main()
