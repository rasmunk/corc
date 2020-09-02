import unittest
from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from corc.config import load_from_env_or_config, gen_config_provider_prefix
from corc.providers.oci.helpers import new_client, get, list_entities, stack_was_deleted
from corc.providers.oci.network import (
    new_vcn_stack,
    delete_vcn_stack,
    ensure_vcn_stack,
    valid_vcn_stack,
    get_vcn_stack,
    get_vcn_by_name,
    equal_vcn_stack,
    refresh_vcn_stack,
    update_vcn_stack,
    get_subnet_in_vcn_stack,
)


class TestVCNStack(unittest.TestCase):
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

        self.oci_profile_options = {
            "compartment_id": oci_compartment_id,
            "name": oci_name,
        }

        test_name = "Test_VCN"
        vcn_name = test_name + "_Network"
        internet_gateway_name = test_name + "_Internet_Gateway"
        subnet_name = test_name + "_Subnet"

        # Add unique test postfix
        test_id = load_from_env_or_config(
            {"test": {"id": {}}}, prefix=gen_config_provider_prefix(prefix)
        )
        if test_id:
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

        self.vcn_options = dict(
            cidr_block="10.0.0.0/16", display_name=vcn_name, dns_label="ku",
        )

        self.subnet_options = dict(display_name=subnet_name, dns_label="workers")

        self.options = dict(
            profile=self.oci_profile_options,
            vcn=self.vcn_options,
            internetgateway=internet_gateway_options,
            routetable=route_table_options,
            subnet=self.subnet_options,
        )

        self.network_client = new_client(
            VirtualNetworkClient,
            composite_class=VirtualNetworkClientCompositeOperations,
            name=self.options["profile"]["name"],
        )

    def tearDown(self):
        # Delete all vcn with display_name
        vcns = list_entities(
            self.network_client,
            "list_vcns",
            self.options["profile"]["compartment_id"],
            display_name=self.vcn_options["display_name"],
        )

        for vcn in vcns:
            deleted_stack = delete_vcn_stack(
                self.network_client, self.options["profile"]["compartment_id"], vcn=vcn,
            )
            self.assertTrue(stack_was_deleted(deleted_stack))

    def test_vcn_stack(self):
        # Extract the ip of the instance
        self.vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            internet_gateway_kwargs=self.options["internetgateway"],
            route_table_kwargs=self.options["routetable"],
            subnet_kwargs=self.options["subnet"],
        )

        self.assertTrue(valid_vcn_stack(self.vcn_stack))
        _vcn_stack = get_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            self.vcn_stack["id"],
        )
        self.assertTrue(valid_vcn_stack(_vcn_stack))
        self.assertEqual(self.vcn_stack["id"], _vcn_stack["id"])
        self.assertEqual(self.vcn_stack["vcn"], _vcn_stack["vcn"])
        self.assertDictEqual(
            self.vcn_stack["internet_gateways"], _vcn_stack["internet_gateways"]
        )
        self.assertDictEqual(self.vcn_stack["subnets"], _vcn_stack["subnets"])

        new_vcn_id = get(self.network_client, "get_vcn", self.vcn_stack["id"])

        self.assertEqual(self.vcn_stack["id"], new_vcn_id.id)
        self.assertEqual(self.vcn_stack["vcn"], new_vcn_id)

        # Custom equal check
        self.assertTrue(equal_vcn_stack(self.vcn_stack, _vcn_stack))

        new_vcn_name = get_vcn_by_name(
            self.network_client,
            self.options["profile"]["compartment_id"],
            self.options["vcn"]["display_name"],
        )

        self.assertEqual(self.vcn_stack["id"], new_vcn_name.id)
        self.assertEqual(self.vcn_stack["vcn"], new_vcn_name)

    def test_vcn_delete_stack(self):
        # Extract the ip of the instance
        self.vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            internet_gateway_kwargs=self.options["internetgateway"],
            route_table_kwargs=self.options["routetable"],
            subnet_kwargs=self.options["subnet"],
        )

        self.assertTrue(valid_vcn_stack(self.vcn_stack))

        created_vcn_stack = get_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            self.vcn_stack["id"],
        )

        self.assertTrue(valid_vcn_stack(created_vcn_stack))
        self.assertTrue(equal_vcn_stack(self.vcn_stack, created_vcn_stack))

        deleted_stack = delete_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            self.vcn_stack["id"],
        )
        self.assertTrue(stack_was_deleted(deleted_stack))

    def test_vcn_refresh_stack(self):
        # Extract the ip of the instance
        self.vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            internet_gateway_kwargs=self.options["internetgateway"],
            route_table_kwargs=self.options["routetable"],
            subnet_kwargs=self.options["subnet"],
        )

        self.assertTrue(valid_vcn_stack(self.vcn_stack))
        vcn_id_stack = {"id": self.vcn_stack["id"]}

        refreshed_vcn = refresh_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=vcn_id_stack,
        )
        self.assertTrue(valid_vcn_stack(refreshed_vcn))
        self.assertTrue(equal_vcn_stack(self.vcn_stack, refreshed_vcn))

        vcn_name_stack = {"display_name": self.vcn_stack["vcn"].display_name}

        refreshed_vcn = refresh_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=vcn_name_stack,
        )
        self.assertTrue(valid_vcn_stack(refreshed_vcn))
        self.assertTrue(equal_vcn_stack(self.vcn_stack, refreshed_vcn))

    def test_vcn_stack_update_ig(self):
        self.vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            internet_gateway_kwargs=self.options["internetgateway"],
            route_table_kwargs=self.options["routetable"],
            subnet_kwargs=self.options["subnet"],
        )

        self.assertTrue(valid_vcn_stack(self.vcn_stack))
        # Created the default internet gateway
        self.assertEqual(len(self.vcn_stack["internet_gateways"]), 1)
        default_ig_id, default_ig = self.vcn_stack["internet_gateways"].popitem()
        vcn_kwargs = {"id": self.vcn_stack["id"]}

        # Update the VCN Internet Gateway display_name and disable it
        new_gateway_kwargs = {
            "id": default_ig_id,
            "display_name": "New Gateway Name",
            "is_enabled": False,
        }

        updated_stack = update_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=vcn_kwargs,
            internet_gateway_kwargs=new_gateway_kwargs,
        )

        self.assertEqual(len(updated_stack["internet_gateways"]), 1)
        self.assertIn(default_ig_id, updated_stack["internet_gateways"])
        updated_ig = updated_stack["internet_gateways"][default_ig_id]

        self.assertEqual(updated_ig.display_name, new_gateway_kwargs["display_name"])
        self.assertEqual(updated_ig.is_enabled, new_gateway_kwargs["is_enabled"])

        deleted_stack = delete_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            self.vcn_stack["id"],
        )
        self.assertTrue(stack_was_deleted(deleted_stack))

    def test_vcn_stack_update_base_vcn(self):
        # Create detault ie and subnets
        vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            internet_gateway_kwargs=self.options["internetgateway"],
            route_table_kwargs=self.options["routetable"],
        )

        self.assertTrue(valid_vcn_stack(vcn_stack))
        subnet_id, subnet = vcn_stack["subnets"].popitem()

        # Apply updates to the subnets
        subnet_options = {}
        subnet_options["display_name"] = self.options["subnet"]["display_name"]
        subnet_options["id"] = subnet_id
        required_subnets = [subnet_options]

        self.assertFalse(valid_vcn_stack(vcn_stack, required_subnets=required_subnets))

        updated_vcn_stack = update_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            internet_gateway_kwargs=self.options["internetgateway"],
            route_table_kwargs=self.options["routetable"],
            subnet_kwargs=subnet_options,
        )

        self.assertTrue(valid_vcn_stack(updated_vcn_stack))
        self.assertTrue(
            valid_vcn_stack(updated_vcn_stack, required_subnets=required_subnets)
        )

    def test_vcn_stack_ensure(self):
        # Create detault ie and subnets
        vcn_stack = new_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            internet_gateway_kwargs=self.options["internetgateway"],
            route_table_kwargs=self.options["routetable"],
        )

        self.assertTrue(valid_vcn_stack(vcn_stack))

        subnet_kwargs = dict(
            cidr_block="10.0.20.0/24",
            display_name="Ensure Subnet",
            dns_label="workers2",
        )

        # Get the created Internet Gateway id
        ensured = ensure_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            internet_gateway_kwargs=self.options["internetgateway"],
            route_table_kwargs=self.options["routetable"],
            subnet_kwargs=subnet_kwargs,
        )
        self.assertTrue(ensured)

        refreshed_vcn_stack = refresh_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
        )

        new_subnet = get_subnet_in_vcn_stack(
            refreshed_vcn_stack,
            subnet_kwargs=subnet_kwargs,
            optional_value_kwargs=["id", "display_name"],
        )
        self.assertEqual(new_subnet.cidr_block, subnet_kwargs["cidr_block"])
        self.assertEqual(new_subnet.display_name, subnet_kwargs["display_name"])
        self.assertEqual(new_subnet.dns_label, subnet_kwargs["dns_label"])


if __name__ == "__main__":
    unittest.main()
