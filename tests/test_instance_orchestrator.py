import unittest
from corc.oci.instance import OCIInstanceOrchestrator


class TestInstanceOrchestrator(unittest.TestCase):
    def setUp(self):
        oci_options = dict(
            compartment_id="ocid1.tenancy.oc1..aaaaaaaakfmksyrf7hl2gfexmjpb6pbyrirm6k3ro7wd464y2pr7atpxpv4q",
            profile_name="XNOVOTECH",
        )

        compute_options = dict(
            availability_domain="Xfze:eu-amsterdam-1-AD-1",
            shape="VM.Standard2.1",
            operating_system="CentOS",
            operating_system_version="7",
            display_name="Test Node",
        )

        compute_metadata_options = dict(
            ssh_authorized_keys=[
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpRktqNSSLq1ARcMAuuTq3I8/K3CgcPJ3CVlXfU2mxg1zSrIwFOEb+foW2jUqEFcwdCmY/gI+XxBaJHxQLIqzowl0C4d6FVtbnRCfNShSbWr4p7xY0FDJvDMD7B7f7XT8zQoCX7Qnugo/afTPxz1R8mAfLFKU97Cy5zr3Bh8mW/ipgKNfH573k50Qe9CN/S9GjtGB2bGPZGSIFpQ6tfmkssBQIkmym7UxfNgQfeV/1drc02GTqH850d7jIXsMCO8XpxQaeVl/G+1/wwAxv+Nna2s143wH6MmAzrklRyb1jQ+ip/fhVF+l4Kk8a2E+DmWsBWj5vmpRLL7hS2MHPszkp"
            ]
        )

        vcn_options = dict(
            cidr_block="10.0.0.0/16",
            display_name="Test Instance Network",
            dns_label="xnovotech",
        )
        subnet_options = dict(display_name="Test Instance Subnet", dns_label="workers")

        self.options = dict(
            oci=oci_options,
            compute=compute_options,
            compute_metadata=compute_metadata_options,
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
