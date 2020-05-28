import unittest
from corc.oci.instance import OCIInstanceOrchestrator


class TestInstanceOrchestrator(unittest.TestCase):
    def setUp(self):
        oci_options = dict(
            compartment_id="ocid1.compartment.oc1..aaaaaaaashnazvohptud5up2i5dxbqbsnwp3bgcubjj75qkqw3zvgxlvoq5a",
            profile_name="KU",
        )

        compute_options = dict(
            availability_domain="lfcb:EU-FRANKFURT-1-AD-1",
            shape="VM.Standard2.1",
            operating_system="CentOS",
            operating_system_version="7",
            display_name="Test Node",
        )

        vcn_options = dict(display_name="Test Instance Network 1", dns_label="ku",)
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
