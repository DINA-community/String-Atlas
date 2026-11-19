import unittest
import os

# Testdatei zu sys.path hinzufügen
test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tests'))
test_loader = unittest.TestLoader()
test_suite = test_loader.discover(start_dir=test_dir, pattern='test_*.py')

test_runner = unittest.TextTestRunner()
test_runner.run(test_suite)