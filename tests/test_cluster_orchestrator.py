import unittest
from corc.config import load_from_env_or_config, gen_config_provider_prefix
from corc.providers.oci.cluster import OCIClusterOrchestrator

# import json
# from libcloud.container.types import Provider
# from libcloud.container.providers import get_driver
# from libcloud.container.drivers.ecs import ROOT
# from corc.providers.defaults import ECS, KUBERNETES, CONTAINER_CLUSTER
# from corc.providers.types import get_orchestrator


class TestClusterOrchestrator(unittest.TestCase):
    def setUp(self):
        # Load compartment_id from the env
        prefix = ("oci",)
        oci_compartment_id = load_from_env_or_config(
            {"profile": {"compartment_id": {}}},
            prefix=gen_config_provider_prefix(prefix),
            throw=True,
        )

        oci_name = load_from_env_or_config(
            {"profile": {"name": {}}},
            prefix=gen_config_provider_prefix(prefix),
            throw=True,
        )

        oci_profile_options = {"compartment_id": oci_compartment_id, "name": oci_name}

        test_name = "Test_C_Orch"
        cluster_name = test_name
        node_name = test_name + "_Node"
        vcn_name = test_name + "_Network"
        internet_gateway_name = test_name + "_Internet_Gateway"
        subnet_name = test_name + "_Subnet"

        # Add unique test postfix
        test_id = load_from_env_or_config(
            {"test": {"id": {}}}, prefix=gen_config_provider_prefix(prefix)
        )
        if test_id:
            cluster_name += test_id
            node_name += test_id
            vcn_name += test_id
            internet_gateway_name += test_id
            subnet_name += test_id

        internet_gateway_options = dict(
            display_name=internet_gateway_name, is_enabled=True
        )
        route_table_options = dict(
            routerules=[
                dict(
                    cidr_block=None,
                    destination="0.0.0.0/0",
                    destination_type="CIDR_BLOCK",
                )
            ]
        )

        # Sort order in ascending to ensure that complex images
        # such as GPU powered shapes are not selected.
        # These are typically not supported by the cluster
        image_options = dict(
            operating_system="Oracle Linux",
            operating_system_version="7.8",
            limit="1",
            sort_order="ASC",
        )

        node_options = dict(
            availability_domain="lfcb:EU-FRANKFURT-1-AD-1",
            name=node_name,
            size=1,
            node_shape="VM.Standard1.1",
            image=image_options,
        )

        cluster_options = dict(name=cluster_name, node=node_options)

        vcn_options = dict(
            cidr_block="10.0.0.0/16", display_name=vcn_name, dns_label="ku",
        )

        subnet_options = dict(
            cidr_block="10.0.1.0/24", display_name=subnet_name, dns_label="workers"
        )

        self.options = dict(
            profile=oci_profile_options,
            cluster=cluster_options,
            vcn=vcn_options,
            internetgateway=internet_gateway_options,
            routetable=route_table_options,
            subnet=subnet_options,
        )

        OCIClusterOrchestrator.validate_options(self.options)
        self.orchestrator = OCIClusterOrchestrator(self.options)
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
#         test_name = "Test_C_Orch"
#         cluster_name = test_name
#         cluster_options = dict(name=cluster_name)

#         ClusterOrchestrator, options = get_orchestrator(CONTAINER_CLUSTER, KUBERNETES)
#         options["cluster"] = cluster_options
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
