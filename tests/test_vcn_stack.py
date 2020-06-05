import os
import unittest
from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from corc.oci.helpers import new_client, get, list_entities, stack_was_deleted
from corc.oci.network import (
    new_vcn_stack,
    delete_vcn_stack,
    valid_vcn_stack,
    get_vcn_stack,
    get_vcn_by_name,
    equal_vcn_stack,
    refresh_vcn_stack,
)


class TestVCNStack(unittest.TestCase):
    def setUp(self):
        # Load compartment_id from the env
        if "OCI_COMPARTMENT_ID" not in os.environ:
            raise ValueError("Missing required environment variable OCI_COMPARTMENT_ID")

        if "OCI_PROFILE_NAME" in os.environ:
            profile_name = os.environ["OCI_PROFILE_NAME"]
        else:
            profile_name = "DEFAULT"

        self.oci_options = dict(
            compartment_id=os.environ["OCI_COMPARTMENT_ID"], profile_name=profile_name,
        )

        test_name = "Test_VCN"
        vcn_name = test_name + "_Network"
        subnet_name = test_name + "_Subnet"

        # Add unique test postfix
        if "OCI_TEST_ID" in os.environ:
            vcn_name += os.environ["OCI_TEST_ID"]
            subnet_name += os.environ["OCI_TEST_ID"]

        self.vcn_options = dict(
            cidr_block="10.0.0.0/16", display_name=vcn_name, dns_label="ku",
        )

        self.subnet_options = dict(display_name=subnet_name, dns_label="workers")

        self.options = dict(
            oci=self.oci_options, vcn=self.vcn_options, subnet=self.subnet_options,
        )

        self.network_client = new_client(
            VirtualNetworkClient,
            composite_class=VirtualNetworkClientCompositeOperations,
            profile_name=self.options["oci"]["profile_name"],
        )

    def tearDown(self):
        # Delete all vcn with display_name
        vcns = list_entities(
            self.network_client,
            "list_vcns",
            self.options["oci"]["compartment_id"],
            display_name=self.vcn_options["display_name"],
        )

        for vcn in vcns:
            deleted_stack = delete_vcn_stack(
                self.network_client, self.options["oci"]["compartment_id"], vcn=vcn
            )
            self.assertTrue(stack_was_deleted(deleted_stack))

    def test_vcn_stack(self):
        # Extract the ip of the instance
        self.vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            subnet_kwargs=self.options["subnet"],
        )

        self.assertTrue(valid_vcn_stack(self.vcn_stack))
        _vcn_stack = get_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            self.vcn_stack["id"],
        )
        self.assertTrue(valid_vcn_stack(_vcn_stack))
        self.assertEqual(self.vcn_stack["id"], _vcn_stack["id"])
        self.assertEqual(self.vcn_stack["vcn"], _vcn_stack["vcn"])
        self.assertListEqual(
            self.vcn_stack["internet_gateways"], _vcn_stack["internet_gateways"]
        )
        self.assertListEqual(self.vcn_stack["subnets"], _vcn_stack["subnets"])

        new_vcn_id = get(self.network_client, "get_vcn", self.vcn_stack["id"])

        self.assertEqual(self.vcn_stack["id"], new_vcn_id.id)
        self.assertEqual(self.vcn_stack["vcn"], new_vcn_id)

        # Custom equal check
        self.assertTrue(equal_vcn_stack(self.vcn_stack, _vcn_stack))

        new_vcn_name = get_vcn_by_name(
            self.network_client,
            self.options["oci"]["compartment_id"],
            self.options["vcn"]["display_name"],
        )

        self.assertEqual(self.vcn_stack["id"], new_vcn_name.id)
        self.assertEqual(self.vcn_stack["vcn"], new_vcn_name)

    def test_vcn_delete_stack(self):
        # Extract the ip of the instance
        self.vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            subnet_kwargs=self.options["subnet"],
        )

        self.assertTrue(valid_vcn_stack(self.vcn_stack))

        created_vcn_stack = get_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            self.vcn_stack["id"],
        )

        self.assertTrue(valid_vcn_stack(created_vcn_stack))
        self.assertTrue(equal_vcn_stack(self.vcn_stack, created_vcn_stack))

        deleted_stack = delete_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            self.vcn_stack["id"],
        )
        self.assertTrue(stack_was_deleted(deleted_stack))

    def test_vcn_refresh_stack(self):
        # Extract the ip of the instance
        self.vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            subnet_kwargs=self.options["subnet"],
        )

        self.assertTrue(valid_vcn_stack(self.vcn_stack))
        refresh_stack = {"id": self.vcn_stack["id"]}

        refreshed_vcn = refresh_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            vcn_kwargs=refresh_stack,
        )
        self.assertTrue(valid_vcn_stack(refreshed_vcn))
        self.assertTrue(equal_vcn_stack(self.vcn_stack, refreshed_vcn))

        refresh_stack = {"display_name": self.vcn_stack["vcn"].display_name}

        refreshed_vcn = refresh_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            vcn_kwargs=refresh_stack,
        )
        self.assertTrue(valid_vcn_stack(refreshed_vcn))
        self.assertTrue(equal_vcn_stack(self.vcn_stack, refreshed_vcn))


if __name__ == "__main__":
    unittest.main()
