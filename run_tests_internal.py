
import sys
import os
import unittest

# Set the project root to sys.path
project_root = r"D:\شغل\CAC 6_October\Tools\Carrier_Selection_Tool"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the test class
from tests.test_new_features import TestNewFeatures

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNewFeatures)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
