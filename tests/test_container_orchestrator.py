import unittest
from corc.providers.apache.container import ApacheContainerOrchestrator
from corc.providers.defaults import CONTAINER, LOCAL
from corc.providers.types import get_orchestrator


class TestLocalContainerOrchestrator(unittest.TestCase):
    def setUp(self):
        test_name = "test_container"
        container_name = test_name
        container_image = "nielsbohr/python-notebook:latest"
        container_options = {"name": container_name, "image": {"name": container_image}}

        ClusterOrchestrator, options = get_orchestrator(CONTAINER, LOCAL)
        options["container"] = container_options
        options["driver"]["kwargs"] = dict(port=2345)
        # If we don't set the command, libcloud will set it to None (ehhh)
        options["container"]["kwargs"] = dict(command="start-notebook.sh")
        self.options = options

        ApacheContainerOrchestrator.validate_options(self.options)
        self.orchestrator = ApacheContainerOrchestrator(self.options)
        # Should not be ready at this point
        self.assertFalse(self.orchestrator.is_ready())

    def tearDown(self):
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())

        resource_id, resource = self.orchestrator.get_resource()
        self.assertIsNone(resource_id)
        self.assertIsNone(resource)

        self.orchestrator = None
        self.options = None

    def test_setup(self):
        self.orchestrator.setup()
        self.assertTrue(self.orchestrator.is_ready())

        resource_id, resource = self.orchestrator.get_resource()
        self.assertIsNotNone(resource_id)
        self.assertIsNotNone(resource)

    def test_teardown(self):
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())

        resource_id, resource = self.orchestrator.get_resource()
        self.assertIsNone(resource_id)
        self.assertIsNone(resource)


# class TestClusterOrchestratorECS(unittest.TestCase):
#     def setUp(self):
#         test_name = "Test_C_Orch"
#         cluster_name = test_name

#         # (access_id, secret, region)
#         ecs_args = ()

#         cluster_options = dict(name=cluster_name)
#         # cls = get_driver(Provider.ECS)
#         # driver = cls(ecs_args[0], ecs_args[1], ecs_args[2])
#         # driver.connection.connection.host = driver.connection.host
#         # NOTE, the ECS drivers internal driver.connection.connection is not
#       # properly defined. The region is not interpolated into the sub connection state.
#         AWSClusterOrchestrator, options = get_orchestrator(CONTAINER_CLUSTER, ECS)
#         options["cluster"] = cluster_options
#         options["driver"]["args"] = ecs_args
#         AWSClusterOrchestrator.validate_options(options)
#         self.options = options
#         self.orchestrator = AWSClusterOrchestrator(options)
#         # Should not be ready at this point
#         self.assertFalse(self.orchestrator.is_ready())

#     def tearDown(self):
#         self.orchestrator.tear_down()
#         self.assertFalse(self.orchestrator.is_ready())
#         self.orchestrator = None
#         self.options = None

#     def test_setup_cluster(self):
#         self.orchestrator.setup()
#         self.assertTrue(self.orchestrator.is_ready())

#     def test_teardown_cluster(self):
#         self.assertFalse(self.orchestrator.is_ready())
#         self.orchestrator.tear_down()
#         self.assertFalse(self.orchestrator.is_ready())


# class TestClusterOrchestrationKubernetes(unittest.TestCase):
#     def setUp(self):
# test_name = "Test_C_Orch"
# cluster_name = test_name
# cluster_options = dict(name=cluster_name)

# ClusterOrchestrator, options = get_orchestrator(CONTAINER_CLUSTER, KUBERNETES)
# options["cluster"] = cluster_options
#         ClusterOrchestrator.validate_options(options)
#         self.options = options
#         self.orchestrator = ClusterOrchestrator(options)
#         # Should not be ready at this point
#         self.assertFalse(self.orchestrator.is_ready())

#     def tearDown(self):
#         self.orchestrator.tear_down()
#         self.assertFalse(self.orchestrator.is_ready())
#         self.orchestrator = None
#         self.options = None

#     def test_setup_cluster(self):
#         self.orchestrator.setup()
#         self.assertTrue(self.orchestrator.is_ready())

#     def test_teardown_cluster(self):
#         self.assertFalse(self.orchestrator.is_ready())
#         self.orchestrator.tear_down()
#         self.assertFalse(self.orchestrator.is_ready())


if __name__ == "__main__":
    unittest.main()
