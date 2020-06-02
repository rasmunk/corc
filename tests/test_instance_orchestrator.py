import os
import unittest
from corc.oci.instance import OCIInstanceOrchestrator


class TestInstanceOrchestrator(unittest.TestCase):
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

        compute_options = dict(
            availability_domain="lfcb:EU-FRANKFURT-1-AD-1",
            shape="VM.Standard2.1",
            operating_system="CentOS",
            operating_system_version="7",
            display_name="Test Node",
        )

        vcn_options = dict(display_name="Test Instance Network", dns_label="ku",)
        subnet_options = dict(display_name="Test Instance Subnet", dns_label="workers")

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

    def test_teardown_instance(self):
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())


if __name__ == "__main__":
    unittest.main()
