import unittest
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import test_phase9_audit_and_consistency

suite = unittest.TestLoader().loadTestsFromModule(test_phase9_audit_and_consistency)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

print("\n================ FAILURE DETAILS ================")
for test, failure in result.failures:
    print(f"\n--- FAILURE in {test} ---")
    print(failure)

for test, err in result.errors:
    print(f"\n--- ERROR in {test} ---")
    print(err)

if not result.wasSuccessful():
    sys.exit(1)
