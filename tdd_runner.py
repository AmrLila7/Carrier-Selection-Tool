
import sys
import os
import unittest

# Add the project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import tests.test_tdd_final
try:
    from tests.test_tdd_final import TestCarrierTDD
    print("Successfully imported TestCarrierTDD")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarrierTDD)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
