import unittest
import json
from libcloud.container.types import Provider
from libcloud.container.providers import get_driver
from libcloud.container.drivers.ecs import ROOT
from corc.providers.defaults import ECS, KUBERNETES
from corc.providers.types import get_orchestrator, CONTAINER_CLUSTER


class TestClusterOrchestratorECS(unittest.TestCase):
    def setUp(self):
        test_name = "Test_C_Orch"
        cluster_name = test_name

        # (access_id, secret, region)
        ecs_args = ()

        cluster_options = dict(name=cluster_name)
        # cls = get_driver(Provider.ECS)
        # driver = cls(ecs_args[0], ecs_args[1], ecs_args[2])
        # driver.connection.connection.host = driver.connection.host
        # NOTE, the ECS drivers internal driver.connection.connection is not
        # properly defined. The region is not interpolated into the sub connection state.
        AWSClusterOrchestrator, options = get_orchestrator(CONTAINER_CLUSTER, ECS)
        options["cluster"] = cluster_options
        options["driver"]["args"] = ecs_args
        AWSClusterOrchestrator.validate_options(options)
        self.options = options
        self.orchestrator = AWSClusterOrchestrator(options)
        # Should not be ready at this point
        self.assertFalse(self.orchestrator.is_ready())

    def tearDown(self):
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator = None
        self.options = None

    def test_setup_cluster(self):
        self.orchestrator.setup()
        self.assertTrue(self.orchestrator.is_ready())

    def test_teardown_cluster(self):
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())


class TestClusterOrchestrationKubernetes(unittest.TestCase):
    def setUp(self):
        test_name = "Test_C_Orch"
        cluster_name = test_name

        cluster_options = dict(name=cluster_name)
        ClusterOrchestrator, options = get_orchestrator(CONTAINER_CLUSTER, KUBERNETES)
        options["cluster"] = cluster_options
        ClusterOrchestrator.validate_options(options)
        self.options = options
        self.orchestrator = ClusterOrchestrator(options)
        # Should not be ready at this point
        self.assertFalse(self.orchestrator.is_ready())

    def tearDown(self):
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator = None
        self.options = None

    def test_setup_cluster(self):
        self.orchestrator.setup()
        self.assertTrue(self.orchestrator.is_ready())

    def test_teardown_cluster(self):
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())


if __name__ == "__main__":
    unittest.main()
