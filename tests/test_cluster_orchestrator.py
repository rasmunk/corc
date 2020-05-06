import pytest
import unittest
from orchestration.cluster import OCIClusterOrchestrator


class TestClusterOrchestrator(unittest.TestCase):
    def setUp(self):
        self.config = {}

        self.orchestrator = OCIClusterOrchestrator(self.config)
        # Should not be ready at this point
        self.assertFalse(self.orchestrator.is_ready())
        OCIClusterOrchestrator.validate_config(self.config)

    def tearDown(self):
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator = None
        self.config = None

    def test_cluster_orchestrator(self):
        pass

    def test_prepare_cluster(self):
        prepared = self.orchestrator.prepare()
        self.assertTrue(prepared)
        self.assertTrue(self.orchestrator.is_ready())

    def test_schedule_job_on_cluster(self):
        pass
