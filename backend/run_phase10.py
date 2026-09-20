import unittest
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import test_phase10_final_validation

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(test_phase10_final_validation)
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    res = runner.run(suite)
    if not res.wasSuccessful():
        sys.exit(1)
