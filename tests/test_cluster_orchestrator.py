import unittest
from corc.config import load_from_env_or_config, gen_config_provider_prefix
from corc.providers.oci.cluster import OCIClusterOrchestrator


class TestClusterOrchestrator(unittest.TestCase):
    def setUp(self):
        # Load compartment_id from the env
        # Load compartment_id from the env
        oci_compartment_id = load_from_env_or_config(
            {"profile": {"compartment_id": {}}},
            prefix=gen_config_provider_prefix({"oci": {}}),
            throw=True,
        )

        oci_profile_name = load_from_env_or_config(
            {"profile": {"profile_name": {}}},
            prefix=gen_config_provider_prefix({"oci": {}}),
            throw=True,
        )

        oci_options = dict(
            compartment_id=oci_compartment_id, profile_name=oci_profile_name,
        )

        test_name = "Test_C_Orch"
        cluster_name = test_name
        node_name = test_name + "_Node"
        vcn_name = test_name + "_Network"
        subnet_name = test_name + "_Subnet"

        # Add unique test postfix
        test_id = load_from_env_or_config(
            {"test": {"id": {}}}, prefix=gen_config_provider_prefix({"oci": {}})
        )
        if test_id:
            cluster_name += test_id
            node_name += test_id
            vcn_name += test_id
            subnet_name += test_id

        cluster_options = dict(name=cluster_name,)
        image_options = dict(display_name="Oracle-Linux-7.7-2020.03.23-0",)

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

        subnet_options = dict(display_name=subnet_name, dns_label="workers")

        self.options = dict(
            oci=oci_options,
            cluster=cluster_options,
            node=node_options,
            vcn=vcn_options,
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


if __name__ == "__main__":
    unittest.main()
