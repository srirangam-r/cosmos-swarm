"""Manufactured E3 gates and train/test separation; no Cosmos outcomes."""
import itertools
import json
from pathlib import Path
import unittest
from score import QC_FIELDS,analyze_complete,joint_success,native_success

class Tests(unittest.TestCase):
    def setUp(self): self.y={k:'Y' for k in QC_FIELDS}
    def test_unknown_preserved(self):
        self.assertIsNone(native_success(None))
        self.assertIsNone(native_success(dict(self.y,rigid='U')))
        self.assertIsNone(joint_success('pass',self.y,{'flag':'check','period_s':1},1)['value'])
    def test_definite_failure_without_inventing_period(self):
        r=joint_success('pass',dict(self.y,single='N'),None,1)
        self.assertEqual(r['value'],0); self.assertNotIn('ratio',r)
        self.assertEqual(native_success(dict(self.y,single='N',rigid='U')),0)
    def test_missing_contract_not_model_failure(self):
        self.assertIsNone(joint_success('pending',dict(self.y,single='N'),None,1)['value'])
        self.assertIsNone(joint_success('invalid',self.y,{'flag':'ok','period_s':1},1)['value'])
    def test_boundary_and_nonfinite(self):
        for t,score in [(.8,1),(1.2,1),(.799,0),(1.201,0)]:
            self.assertEqual(joint_success('pass',self.y,{'flag':'ok','period_s':t},1)['value'],score)
        for t in [None,float('nan'),float('inf'),0,-1]:
            self.assertIsNone(joint_success('pass',self.y,{'flag':'ok','period_s':t},1)['value'])
    def test_full_cube_and_no_test_leakage(self):
        seeds=list(range(601,609))
        cells={(s,i):dict(state='known',value=int(s<603)) for s in seeds for i in ['pend10','pend11','pend14']}
        a=analyze_complete(cells,seeds,20,100)['result']
        self.assertEqual(a['top_seed_ids'],[601,602]); self.assertEqual(a['top_minus_random_pool'],.75)
        for s in seeds:
            for i in ['pend11','pend14']: cells[s,i]['value']=1-cells[s,i]['value']
        b=analyze_complete(cells,seeds,20,100)['result']
        self.assertEqual(a['top_seed_ids'],b['top_seed_ids']); self.assertEqual(b['top_minus_random_pool'],-.75)
    def test_unknown_blocks_no_shrink(self):
        seeds=list(range(601,609)); cells={(s,i):dict(state='known',value=0) for s in seeds for i in ['pend10','pend11','pend14']}
        cells[601,'pend14']=dict(state='unknown',value=None)
        r=analyze_complete(cells,seeds,20,100)
        self.assertEqual(r['status'],'blocked'); self.assertIsNone(r['raw_p']);self.assertEqual(len(r['missing']),1)
        del cells[601,'pend14']
        with self.assertRaises(ValueError): analyze_complete(cells,seeds,20,100)
    def test_ties_and_static(self):
        seeds=list(range(601,625)); cells={(s,i):dict(state='known',value=0) for s in seeds for i in ['pend10','pend11','pend14']}
        r=analyze_complete(cells,seeds,20,100)['result']
        self.assertEqual(r['top_seed_ids'],seeds[:6]);self.assertEqual(r['bottom_seed_ids'],seeds[-6:])
        self.assertFalse(r['training_has_ranking_signal']);self.assertEqual(r['top_minus_random_pool'],0)
        self.assertEqual(r['permutation']['p_one_sided'],1)
    def test_independent_exact_bank_reference(self):
        from analyze import scalar_reference
        ss=list(range(601,609));train=[1,1,0,0,0,0,0,0]
        test=[[v,v] for v in train]
        r=scalar_reference(train,test,ss)
        self.assertEqual(r['total_random_banks'],28)
        self.assertEqual(r['exceedances'],1);self.assertEqual(r['p_exact'],1/28)
        self.assertEqual(r['lift'],.75);self.assertEqual(r['equally_training_ranked_banks'],1)
        tied=scalar_reference([0]*8,test,ss)
        self.assertEqual(tied['equally_training_ranked_banks'],28)
        self.assertEqual(tied['top_seed_ids'],ss[:2])
    def test_full24_exact_reference(self):
        from analyze import scalar_reference
        ss=list(range(601,625));train=[int(j<6) for j in range(24)]
        r=scalar_reference(train,[[v,v] for v in train],ss)
        self.assertEqual(r['total_random_banks'],134596);self.assertEqual(r['exceedances'],1)
        self.assertEqual(r['lift'],.75)
    def test_reject_inconsistent_missing_records(self):
        seeds=list(range(601,609));cells={(s,i):dict(state='known',value=0) for s in seeds for i in ['pend10','pend11','pend14']}
        cells[601,'pend14']=dict(state='unknown',value=0)
        with self.assertRaises(ValueError): analyze_complete(cells,seeds,20,100)
    def test_native_contract_decoder(self):
        import cv2,numpy as np,tempfile
        from prepare import decode,finite
        with tempfile.TemporaryDirectory(prefix='e3-manufactured-') as tmp:
            root=Path(tmp)
            for name,hz,n in [('valid',24,93),('fps',12,93),('frames',24,92)]:
                path=root/(name+'.avi');writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'FFV1'),hz,(832,480))
                self.assertTrue(writer.isOpened())
                for j in range(n): writer.write(np.full((480,832,3),j,dtype=np.uint8))
                writer.release()
                if name=='valid':
                    values,contract=decode(path)
                    self.assertEqual(values.dtype,np.float32)
                    self.assertEqual(values.shape,(93,480,832,3))
                    self.assertEqual(contract['frames'],93)
                    self.assertTrue(np.all(values[37]==37));del values
                else:
                    with self.assertRaises(ValueError): decode(path)
        self.assertEqual(finite({'a':np.float64(float('nan')),'b':np.array([1,2])}),{'a':None,'b':[1,2]})

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    Path(__file__).with_name('synthetic_verification.json').write_text(json.dumps(dict(
        scope='manufactured arrays/gates, not planted or Cosmos data',tests=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),success=result.wasSuccessful()),indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
