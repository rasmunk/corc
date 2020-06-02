import os
import unittest
from corc.configurer import AnsibleConfigurer
from corc.oci.instance import OCIInstanceOrchestrator


# ansible_repo_path = os.path.join(os.sep, "home", "rasmus", "repos", "nbi_machines")

current_dir = os.path.dirname(os.path.abspath(__file__))
playbook_path = os.path.join(current_dir, "res", "configurer", "playbook.yml")


class TestInstanceConfigurer(unittest.TestCase):
    def setUp(self):
        oci_options = dict(
            compartment_id="ocid1.compartment.oc1..aaaaaaaashnazvohptud5u"
            "p2i5dxbqbsnwp3bgcubjj75qkqw3zvgxlvoq5a",
            profile_name="KU",
        )

        compute_options = dict(
            availability_domain="lfcb:EU-FRANKFURT-1-AD-1",
            shape="VM.Standard2.1",
            operating_system="CentOS",
            operating_system_version="7",
            display_name="Test Node",
        )

        compute_metadata_options = dict(
            ssh_authorized_keys=[
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpRktqNSSLq1ARcMAuuTq3I8/K3CgcPJ3"
                "CVlXfU2mxg1zSrIwFOEb+foW2jUqEFcwdCmY/gI+XxBaJHxQLIqzowl0C4d6FVtbnRCfNSh"
                "SbWr4p7xY0FDJvDMD7B7f7XT8zQoCX7Qnugo/afTPxz1R8mAfLFKU97Cy5zr3Bh8mW/ipgK"
                "NfH573k50Qe9CN/S9GjtGB2bGPZGSIFpQ6tfmkssBQIkmym7UxfNgQfeV/1drc02GTqH850"
                "d7jIXsMCO8XpxQaeVl/G+1/wwAxv+Nna2s143wH6MmAzrklRyb1jQ+ip/fhVF+l4Kk8a2E+"
                "DmWsBWj5vmpRLL7hS2MHPszkp"
            ]
        )

        vcn_options = dict(
            cidr_block="10.0.0.0/16",
            display_name="Test Instance Network 2",
            dns_label="ku",
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
        self.orchestrator.setup()
        self.assertTrue(self.orchestrator.is_ready())

    def test_instance_ansible_configure(self):
        # Extract the ip of the instance
        endpoint = self.orchestrator.endpoint()
        options = dict(playbook_path=playbook_path, hosts=[endpoint],)
        configurer = AnsibleConfigurer(options)
        configurer.apply()


if __name__ == "__main__":
    unittest.main()
