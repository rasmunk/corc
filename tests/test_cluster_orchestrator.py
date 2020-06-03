import os
import unittest
from corc.oci.cluster import OCIClusterOrchestrator


class TestClusterOrchestrator(unittest.TestCase):
    def setUp(self):
        # Load compartment_id from the env
        if "OCI_COMPARTMENT_ID" not in os.environ:
            raise ValueError("Missing required environment variable OCI_COMPARTMENT_ID")

        if "OCI_PROFILE_NAME" in os.environ:
            profile_name = os.environ["OCI_PROFILE_NAME"]
        else:
            profile_name = "DEFAULT"

        oci_options = dict(
            compartment_id=os.environ["OCI_COMPARTMENT_ID"], profile_name=profile_name,
        )

        test_name = "Test_C_Orch"
        cluster_name = test_name
        node_name = test_name + "_Node"
        vcn_name = test_name + "_Network"
        subnet_name = test_name + "_Subnet"

        # Add unique test postfix
        if "OCI_TEST_ID" in os.environ:
            cluster_name += os.environ["OCI_TEST_ID"]
            node_name += os.environ["OCI_TEST_ID"]
            vcn_name += os.environ["OCI_TEST_ID"]
            subnet_name += os.environ["OCI_TEST_ID"]

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
