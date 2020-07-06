import unittest
from oci.core import (
    ComputeClient,
    ComputeClientCompositeOperations,
    VirtualNetworkClient,
    VirtualNetworkClientCompositeOperations,
)
from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from corc.config import load_from_env_or_config, gen_config_provider_prefix
from corc.providers.oci.helpers import new_client, get, get_kubernetes_version
from corc.providers.oci.cluster import (
    new_cluster_stack,
    get_cluster_stack,
    get_cluster_by_name,
    delete_cluster_stack,
    valid_cluster_stack,
    gen_cluster_stack_details,
    list_entities,
)
from corc.providers.oci.network import new_vcn_stack, delete_vcn_stack, valid_vcn_stack


class TestClusterStack(unittest.TestCase):
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

        oci_options = {
            "profile": {"compartment_id": oci_compartment_id, "name": oci_name}
        }
        # oci_options = dict(compartment_id=oci_compartment_id, name=oci_name,)

        test_name = "Test_Cluster"
        cluster_name = test_name
        node_name = test_name + "_Node"
        vcn_name = test_name + "_Network"
        subnet_name = test_name + "_Subnet"

        # Add unique test postfix
        test_id = load_from_env_or_config(
            {"test": {"id": {}}}, prefix=gen_config_provider_prefix(prefix)
        )
        if test_id:
            cluster_name += test_id
            node_name += test_id
            vcn_name += test_id
            subnet_name += test_id

        image_options = dict(display_name="Oracle-Linux-7.7-2020.03.23-0")
        node_options = dict(
            availability_domain="lfcb:EU-FRANKFURT-1-AD-1",
            name=node_name,
            size=1,
            node_shape="VM.Standard1.1",
            image=image_options,
        )
        vcn_options = dict(
            cidr_block="10.0.0.0/16", display_name=vcn_name, dns_label="ku",
        )
        subnet_options = dict(
            cidr_block="10.0.2.0/24", display_name=subnet_name, dns_label="workers"
        )

        self.container_engine_client = new_client(
            ContainerEngineClient,
            composite_class=ContainerEngineClientCompositeOperations,
            name=oci_name,
        )

        cluster_options = dict(
            name=cluster_name,
            kubernetes_version=get_kubernetes_version(self.container_engine_client),
            node=node_options,
        )

        self.compute_client = new_client(
            ComputeClient,
            composite_class=ComputeClientCompositeOperations,
            name=oci_name,
        )

        self.network_client = new_client(
            VirtualNetworkClient,
            composite_class=VirtualNetworkClientCompositeOperations,
            name=oci_name,
        )

        self.options = dict(
            oci=oci_options,
            cluster=cluster_options,
            vcn=vcn_options,
            subnet=subnet_options,
        )

    def tearDown(self):
        # Validate that the vcn stack is gone
        deleted = delete_cluster_stack(
            self.container_engine_client, self.cluster_stack["id"], delete_vcn=True
        )
        self.assertTrue(deleted)

        # Delete all vcn with display_name
        vcns = list_entities(
            self.network_client,
            "list_vcns",
            self.options["oci"]["profile"]["compartment_id"],
            display_name=self.options["vcn"]["display_name"],
        )

        for vcn in vcns:
            deleted = delete_vcn_stack(
                self.network_client,
                self.options["oci"]["profile"]["compartment_id"],
                vcn=vcn,
            )
            self.assertTrue(deleted)

    def test_cluster_stack(self):
        # Need vcn stack for the cluster stack
        self.vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["oci"]["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            subnet_kwargs=self.options["subnet"],
        )
        self.assertTrue(valid_vcn_stack(self.vcn_stack))

        # Available images
        available_images = list_entities(
            self.compute_client,
            "list_images",
            self.options["oci"]["profile"]["compartment_id"],
            **self.options["cluster"]["node"]["image"]
        )

        if not available_images:
            raise ValueError(
                "No valid image could be found with options: {}".format(
                    self.options["cluster"]["node"]["image"]
                )
            )

        if len(available_images) > 1:
            raise ValueError(
                "More than 1 image was found with options: {}".format(
                    self.options["cluster"]["node"]["image"]
                )
            )

        image = available_images[0]

        # Prepare cluster details
        cluster_details = gen_cluster_stack_details(
            self.vcn_stack["id"], self.vcn_stack["subnets"], image, **self.options
        )

        self.cluster_stack = new_cluster_stack(
            self.container_engine_client,
            cluster_details["create_cluster"],
            cluster_details["create_node_pool"],
        )

        self.assertTrue(valid_cluster_stack(self.cluster_stack))

        _cluster_stack = get_cluster_stack(
            self.container_engine_client,
            self.options["oci"]["profile"]["compartment_id"],
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
            self.options["oci"]["profile"]["compartment_id"],
            self.cluster_stack["cluster"].name,
        )

        self.assertEqual(self.cluster_stack["id"], new_cluster_id.id)
        self.assertEqual(self.cluster_stack["cluster"], new_cluster_name)


if __name__ == "__main__":
    unittest.main()
