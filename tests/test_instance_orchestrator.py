import unittest
from corc.config import load_from_env_or_config, gen_config_provider_prefix
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

        oci_options = dict(compartment_id=oci_compartment_id, name=oci_name,)

        test_name = "Test_Instance_Orch"
        node_name = test_name + "_Node"
        vcn_name = test_name + "_Network"
        subnet_name = test_name + "_Subnet"

        # Add unique test postfix
        test_id = load_from_env_or_config(
            {"test": {"id": {}}}, prefix=gen_config_provider_prefix(prefix)
        )
        if test_id:
            node_name += test_id
            vcn_name += test_id
            subnet_name += test_id

        compute_options = dict(
            availability_domain="lfcb:EU-FRANKFURT-1-AD-2",
            shape="VM.Standard1.1",
            operating_system="CentOS",
            operating_system_version="7",
            display_name=node_name,
        )

        vcn_options = dict(display_name=vcn_name, dns_label="ku",)
        subnet_options = dict(display_name=subnet_name, dns_label="workers")

        self.options = dict(
            oci=oci_options,
            compute=compute_options,
            vcn=vcn_options,
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

    def test_setup_instance_resource_config(self):
        required_num_cpus = 4.0
        required_gb_mem = 8.0

        resource_config = OCIInstanceOrchestrator.make_resource_config(
            oci_options=self.options["oci"],
            oci_availability_domain=self.options["compute"]["availability_domain"],
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

    def test_teardown_instance(self):
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())


if __name__ == "__main__":
    unittest.main()
