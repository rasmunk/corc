import copy
import os
import unittest
from corc.config import (
    load_from_env_or_config,
    gen_config_provider_prefix,
    generate_default_config,
    save_config,
    remove_config,
)
from corc.providers.oci.network import get_subnet_in_vcn_stack
from corc.providers.oci.config import generate_oci_config
from corc.providers.oci.instance import OCIInstanceOrchestrator


class TestInstanceOrchestrator(unittest.TestCase):
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
        oci_profile_options = dict(
            compartment_id=oci_compartment_id,
            name=oci_name,
        )

        test_name = "Test_Instance_Orch"
        node_name = test_name + "_Node"
        vcn_name = test_name + "_Network"
        internet_gateway_name = test_name + "_Internet_Gateway"
        subnet_name = test_name + "_Subnet"

        # Add unique test postfix
        test_id = load_from_env_or_config(
            {"test": {"id": {}}}, prefix=gen_config_provider_prefix(prefix)
        )
        if test_id:
            node_name += test_id
            vcn_name += test_id
            internet_gateway_name += test_id
            subnet_name += test_id

        instance_options = dict(
            availability_domain="lfcb:EU-FRANKFURT-1-AD-2",
            shape="VM.Standard1.1",
            operating_system="CentOS",
            operating_system_version="7",
            display_name=node_name,
        )

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

        vcn_options = dict(display_name=vcn_name, dns_label="ku")
        subnet_options = dict(
            cidr_block="10.0.1.0/24", display_name=subnet_name, dns_label="workers"
        )

        self.options = dict(
            profile=oci_profile_options,
            instance=instance_options,
            vcn=vcn_options,
            internetgateway=internet_gateway_options,
            routetable=route_table_options,
            subnet=subnet_options,
        )

        OCIInstanceOrchestrator.validate_options(self.options)
        self.orchestrator = OCIInstanceOrchestrator(self.options)
        # Should not be ready at this point
        self.assertFalse(self.orchestrator.is_ready())

    def tearDown(self):
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator = None
        self.options = None

    def test_setup_instance(self):
        self.orchestrator.setup()
        self.assertTrue(self.orchestrator.is_ready())

    def test_valid_load_instance_config(self):
        test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
        config_path = os.path.join(test_dir, "config")
        config = generate_default_config()
        oci_config = generate_oci_config()

        config["corc"]["providers"].update(oci_config)
        self.assertTrue(save_config(config, path=config_path))
        options = OCIInstanceOrchestrator.load_config_options(path=config_path)
        self.assertIsNone(OCIInstanceOrchestrator.validate_options(options))
        self.assertTrue(remove_config(config_path))

    def test_setup_instance_resource_config(self):
        required_num_cpus = 4.0
        required_gb_mem = 8.0

        provider_kwargs = dict(
            availability_domain=self.options["instance"]["availability_domain"]
        )
        resource_config = OCIInstanceOrchestrator.make_resource_config(
            provider_profile=self.options["profile"],
            provider_kwargs=provider_kwargs,
            cpu=required_num_cpus,
            memory=required_gb_mem,
        )
        self.assertIsNotNone(resource_config)
        self.assertNotEqual(resource_config, {})
        self.orchestrator.setup(resource_config)
        self.assertTrue(self.orchestrator.is_ready())

        identifer, resource = self.orchestrator.get_resource()
        self.assertIsNotNone(identifer)
        self.assertIsNotNone(resource)

        # Correct spec?
        self.assertGreaterEqual(resource.shape_config.ocpus, required_num_cpus)
        self.assertGreaterEqual(resource.shape_config.memory_in_gbs, required_gb_mem)

    def test_add_new_subnet(self):
        # Setup first configuration
        self.orchestrator.setup()
        self.assertTrue(self.orchestrator.is_ready())
        # Extract the existing gateway and pass it on
        # Update configuration
        new_subnet = dict(
            cidr_block="10.0.2.0/24",
            display_name=self.options["subnet"]["display_name"],
            dns_label="workers2",
            freeform_tags=dict(Hello="World"),
        )

        options = copy.deepcopy(self.options)
        options["subnet"] = new_subnet
        OCIInstanceOrchestrator.validate_options(options)
        new_orchestrator = OCIInstanceOrchestrator(options)
        self.assertFalse(new_orchestrator.is_ready())
        new_orchestrator.setup()
        self.assertTrue(new_orchestrator.is_ready())

        vcn_stack = new_orchestrator._get_vcn_stack()
        self.assertIn("subnets", vcn_stack)

        subnet = get_subnet_in_vcn_stack(
            vcn_stack,
            subnet_kwargs=new_subnet,
            optional_value_kwargs=["id", "display_name"],
        )
        self.assertIsNotNone(subnet)
        self.assertTrue(hasattr(subnet, "freeform_tags"))
        self.assertEqual(getattr(subnet, "freeform_tags"), new_subnet["freeform_tags"])

    def test_teardown_instance(self):
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())


# class TestEC2InstanceOrchestrator(unittest.TestCase):
#     def setUp(self):
#         test_name = "Test_Instance_Orch"
#         node_name = test_name + "_Node"

#         compute_options = dict(name=node_name)
#         # (access_key_id)
#         ec2_args = ("",)
#         ec2_kwargs = {"secret": ""}

#         self.options = dict(compute=compute_options)
#         EC2Orchestrator, options = get_orchestrator(INSTANCE, EC2)
#         options["driver"]["args"] = ec2_args
#         options["driver"]["kwargs"] = ec2_kwargs
#         self.options.update(options)

#         EC2Orchestrator.validate_options(self.options)
#         self.orchestrator = EC2Orchestrator(self.options)
#         # Should not be ready at this point
#         self.assertFalse(self.orchestrator.is_ready())

#     def tearDown(self):
#         self.orchestrator.tear_down()
#         self.assertFalse(self.orchestrator.is_ready())
#         self.orchestrator = None
#         self.options = None

#     def test_setup_instance(self):
#         self.orchestrator.setup()
#         self.assertTrue(self.orchestrator.is_ready())

#     def test_teardown_instance(self):
#         self.assertFalse(self.orchestrator.is_ready())
#         self.orchestrator.tear_down()
#         self.assertFalse(self.orchestrator.is_ready())


if __name__ == "__main__":
    unittest.main()
