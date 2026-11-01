import unittest,numpy as np
from reference import onset,cross_cycles,turning_cycles
class ReferenceChecks(unittest.TestCase):
 def test_period_with_offset_and_trendfree_decay(self):
  t=np.arange(600)/30;T=1.17
  x=.25*np.cos(2*np.pi*t/T+.3)
  for offset in [-2,0,10]:
   r=cross_cycles(t,x+offset,2,8);q=turning_cycles(t,x+offset,2,8,30)
   self.assertLess(abs(r['period_s']-T),.001)
   self.assertLess(abs(q['period_s']-T),.001)
 def test_turning_period_survives_amplitude_decay(self):
  t=np.arange(600)/30;T=1.17;x=.25*np.exp(-.08*t)*np.cos(2*np.pi*t/T+.4)
  self.assertLess(abs(turning_cycles(t,x,2,8,30)['period_s']-T),.001)
 def test_window_limits_retained_cycles(self):
  t=np.arange(600)/30;x=.25*np.cos(2*np.pi*t/1.2)
  r=cross_cycles(t,x,2.5,5.5)
  self.assertTrue(all(2.5<=v<=5.5 for row in r['crossing_times_s'] for v in row))
  self.assertEqual(cross_cycles(t,x,2.5,2.6)['period_s'],None)
 def test_sustained_onset(self):
  x=np.zeros(25);x[3]=.1;x[10:]=.02
  self.assertEqual(onset(x,.005),10)
if __name__=='__main__':unittest.main()
