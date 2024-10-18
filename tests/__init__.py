import sys
import os

# Ensure that the package source directory is in the system path such that tests
# can import the package modules for testing
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
