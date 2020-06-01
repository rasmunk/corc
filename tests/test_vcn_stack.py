import os
import unittest
from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from corc.oci.helpers import new_client, get, list_entities
from corc.oci.network import (
    new_vcn_stack,
    delete_vcn_stack,
    valid_vcn_stack,
    get_vcn_stack,
    get_vcn_by_name,
)


class TestVCNStack(unittest.TestCase):
    def setUp(self):
        oci_options = dict(
            compartment_id="ocid1.compartment.oc1..aaaaaaaashnazvohptud5up2i5dxbqbsnwp3bgcubjj75qkqw3zvgxlvoq5a",
            profile_name="KU",
        )

        self.vcn_display_name = "Test VCN Network"
        self.subnet_display_name = "Test VCN Subnet"

        vcn_options = dict(
            cidr_block="10.0.0.0/16",
            display_name=self.vcn_display_name,
            dns_label="ku",
        )

        subnet_options = dict(
            display_name=self.subnet_display_name, dns_label="workers"
        )

        self.options = dict(oci=oci_options, vcn=vcn_options, subnet=subnet_options,)

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
            display_name=self.vcn_display_name,
        )

        for vcn in vcns:
            deleted = delete_vcn_stack(
                self.network_client, self.options["oci"]["compartment_id"], vcn=vcn
            )
            self.assertTrue(deleted)

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

        new_vcn_name = get_vcn_by_name(
            self.network_client,
            self.options["oci"]["compartment_id"],
            self.options["vcn"]["display_name"],
        )

        self.assertEqual(self.vcn_stack["id"], new_vcn_name.id)
        self.assertEqual(self.vcn_stack["vcn"], new_vcn_name)


if __name__ == "__main__":
    unittest.main()
