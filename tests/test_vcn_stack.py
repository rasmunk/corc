import os
import unittest
from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from corc.oci.helpers import new_client, get
from corc.oci.network import new_vcn_stack, delete_vcn_stack, valid_vcn_stack, get_vcn_stack, get_vcn_by_name


class TestInstanceConfigurer(unittest.TestCase):
    def setUp(self):
        oci_options = dict(
            compartment_id="ocid1.compartment.oc1..aaaaaaaashnazvohptud5up2i5dxbqbsnwp3bgcubjj75qkqw3zvgxlvoq5a",
            profile_name="KU",
        )

        vcn_options = dict(
            cidr_block="10.0.0.0/16",
            display_name="Unique VCN Name",
            dns_label="ku",
        )

        subnet_options = dict(
            display_name="Test Instance Subnet",
            dns_label="workers")

        self.options = dict(
            oci=oci_options,
            vcn=vcn_options,
            subnet=subnet_options,
        )

        self.network_client = new_client(
            VirtualNetworkClient,
            composite_class=VirtualNetworkClientCompositeOperations,
            profile_name=self.options["oci"]["profile_name"],
        )

    def test_vcn_stack(self):
        # Extract the ip of the instance
        vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            subnet_kwargs=self.options["subnet"])
        
        self.assertTrue(valid_vcn_stack(vcn_stack))
        _vcn_stack = get_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            vcn_stack["id"]
        )
        self.assertTrue(valid_vcn_stack(_vcn_stack))
        self.assertEqual(vcn_stack["id"], _vcn_stack["id"])
        self.assertEqual(vcn_stack["vcn"], _vcn_stack["vcn"])
        self.assertListEqual(vcn_stack["internet_gateways"], _vcn_stack["internet_gateways"])
        self.assertListEqual(vcn_stack["subnets"], _vcn_stack["subnets"])

        new_vcn_id = get(
            self.network_client,
            'get_vcn',
            vcn_stack["id"]
        )

        self.assertEqual(vcn_stack["id"], new_vcn_id.id)
        self.assertEqual(vcn_stack["vcn"], new_vcn_id)

        new_vcn_name = get_vcn_by_name(
            self.network_client,
            self.options["oci"]["compartment_id"],
            self.options["vcn"]["display_name"]
        )

        self.assertEqual(vcn_stack["id"], new_vcn_name.id)
        self.assertEqual(vcn_stack["vcn"], new_vcn_name)


if __name__ == "__main__":
    unittest.main()
