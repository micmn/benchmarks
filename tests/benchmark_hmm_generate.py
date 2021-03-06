'''
  @file benchmark_hmm_generate.py
  @author Marcus Edel

  Test for the Hidden Markov Model Sequence Generator scripts.
'''

import unittest

import os, sys, inspect

# Import the util path, this method even works if the path contains
# symlinks to modules.
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(
  os.path.split(inspect.getfile(inspect.currentframe()))[0], '../util')))
if cmd_subfolder not in sys.path:
  sys.path.insert(0, cmd_subfolder)

from loader import *

'''
Test the mlpack Hidden Markov Model Sequence Generator script.
'''
class HMMGENERATE_MLPACK_TEST(unittest.TestCase):

  '''
  Test initialization.
  '''
  def setUp(self):
    self.verbose = False
    self.timeout = 9000

    # Create the hmm model file used to test the hmm generate method.
    self.dataset = 'datasets/iris.csv'
    module = Loader.ImportModuleFromPath("methods/mlpack/hmm_train.py")
    obj = getattr(module, "HMMTRAIN")
    self.instance = obj(self.dataset, verbose=self.verbose, timeout=self.timeout)
    result = self.instance.RunMetrics("-t gaussian -n 2 -o datasets/iris_hmm.xml")

    self.dataset = 'datasets/iris_hmm.xml'
    module = Loader.ImportModuleFromPath("methods/mlpack/hmm_generate.py")
    obj = getattr(module, "HMMGENERATE")
    self.instance = obj(self.dataset, verbose=self.verbose, timeout=self.timeout)

  '''
  Test the constructor.
  '''
  def test_Constructor(self):
    # The mlpack script should set the description value.
    self.assertTrue(self.instance.description != "")
    self.assertEqual(self.instance.verbose, self.verbose)
    self.assertEqual(self.instance.timeout, self.timeout)
    self.assertEqual(self.instance.dataset, self.dataset)

  '''
  Test the 'RunMetrics' function.
  '''
  def test_RunMetrics(self):
    result = self.instance.RunMetrics("-l 1")
    self.assertTrue(result["Runtime"] > 0)

  '''
  Test the destructor.
  '''
  def test_Destructor(self):
    del self.instance

    clean = True
    filelist = ["gmon.out", "output.csv"]
    for f in filelist:
      if os.path.isfile(f):
        clean = False

    self.assertTrue(clean)

if __name__ == '__main__':
  unittest.main()
