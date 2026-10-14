"""Shared setup for the web app tests: make the repo root and the test fakes importable."""

import os
import sys

TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(TESTS_DIR))  # repo root
sys.path.insert(0, TESTS_DIR)  # so `import test_client_form` finds the fakes
