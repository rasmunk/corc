import os
import unittest
from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from corc.oci.helpers import new_client, get, get_kubernetes_version
from corc.oci.cluster import (
    new_cluster_stack,
    get_cluster_stack,
    get_cluster_by_name,
    delete_cluster_stack,
    valid_cluster_stack,
    gen_cluster_stack_details,
)
from corc.oci.network import new_vcn_stack, delete_vcn_stack, valid_vcn_stack


class TestClusterStack(unittest.TestCase):
    def setUp(self):
        oci_options = dict(
            compartment_id="ocid1.compartment.oc1..aaaaaaaashnazvohptud5up2i5dxbqbsnwp3bgcubjj75qkqw3zvgxlvoq5a",
            profile_name="KU",
        )
        cluster_options = dict(name="Test KU Cluster",)
        node_options = dict(
            availability_domain="lfcb:EU-FRANKFURT-1-AD-1",
            name="test_ku_cluster",
            size=1,
            node_shape="VM.Standard2.1",
            node_image_name="Oracle-Linux-7.7",
        )

        vcn_options = dict(
            cidr_block="10.0.0.0/16", display_name="Test KU Network 1", dns_label="ku",
        )

        subnet_options = dict(dns_label="workers")

        self.options = dict(
            oci=oci_options,
            cluster=cluster_options,
            node=node_options,
            vcn=vcn_options,
            subnet=subnet_options,
        )

        self.network_client = new_client(
            VirtualNetworkClient,
            composite_class=VirtualNetworkClientCompositeOperations,
            profile_name=self.options["oci"]["profile_name"],
        )

        self.container_engine_client = new_client(
            ContainerEngineClient,
            composite_class=ContainerEngineClientCompositeOperations,
            profile_name=self.options["oci"]["profile_name"],
        )

    def tearDown(self):
        deleted = delete_cluster_stack(
            self.container_engine_client, self.cluster_stack["id"], delete_vcn=True
        )

        # Validate that the vcn stack is gone

    def test_cluster_stack(self):
        # Need vcn stack for the cluster stack
        self.vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            subnet_kwargs=self.options["subnet"],
        )
        self.assertTrue(valid_vcn_stack(self.vcn_stack))
        # Prepare cluster details

        cluster_details = gen_cluster_stack_details(
            self.vcn_stack["id"],
            self.vcn_stack["subnets"],
            get_kubernetes_version(self.container_engine_client),
            **self.options
        )

        self.cluster_stack = new_cluster_stack(
            self.container_engine_client,
            cluster_details["create_cluster"],
            cluster_details["create_node_pool"],
        )

        self.assertTrue(valid_cluster_stack(self.cluster_stack))

        _cluster_stack = get_cluster_stack(
            self.container_engine_client,
            self.options["oci"]["compartment_id"],
            self.cluster_stack["id"],
        )
        self.assertTrue(valid_cluster_stack(_cluster_stack))
        self.assertEqual(self.cluster_stack["id"], _cluster_stack["id"])
        self.assertEqual(self.cluster_stack["cluster"], _cluster_stack["cluster"])
        self.assertListEqual(
            self.cluster_stack["node_pools"], _cluster_stack["node_pools"]
        )

        new_cluster_id = get(
            self.container_engine_client, "get_cluster", self.cluster_stack["id"]
        )

        new_cluster_name = get_cluster_by_name(
            self.container_engine_client,
            self.options["oci"]["compartment_id"],
            self.cluster_stack["display_name"],
        )

        self.assertEqual(self.cluster_stack["id"], new_cluster_id.id)
        self.assertEqual(self.cluster_stack["cluster"], new_cluster_name)


if __name__ == "__main__":
    unittest.main()
