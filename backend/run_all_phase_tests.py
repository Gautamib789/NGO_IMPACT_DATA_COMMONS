import unittest
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

test_modules = [
    "test_phase2_schema",
    "test_phase3_gov_verify",
    "test_phase4_doc_tamper",
    "test_phase5_admin_review",
    "test_phase6_project_tracking",
    "test_phase7_frontend_integration",
    "test_phase8_public_profile",
    "test_phase9_audit_and_consistency"
]

loader = unittest.TestLoader()
suite = unittest.TestSuite()

for mod in test_modules:
    try:
        loaded = loader.loadTestsFromName(mod)
        suite.addTest(loaded)
    except Exception as e:
        print(f"Error loading {mod}: {e}")

runner = unittest.TextTestRunner(verbosity=1)
result = runner.run(suite)

print("\n================ SUMMARY ================")
print(f"Total Tests Run: {result.testsRun}")
print(f"Failures: {len(result.failures)}")
print(f"Errors: {len(result.errors)}")

if not result.wasSuccessful():
    sys.exit(1)
