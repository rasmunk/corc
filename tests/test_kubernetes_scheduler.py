import sys
import os

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_path, "orchestration"))

import unittest
from cluster import OCIClusterOrchestrator


class TestKubernetesScheduler(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
