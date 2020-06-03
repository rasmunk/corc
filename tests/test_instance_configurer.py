import os
import unittest
from corc.configurer import AnsibleConfigurer
from corc.oci.instance import OCIInstanceOrchestrator


# ansible_repo_path = os.path.join(os.sep, "home", "rasmus", "repos", "nbi_machines")

current_dir = os.path.dirname(os.path.abspath(__file__))
playbook_path = os.path.join(current_dir, "res", "configurer", "playbook.yml")


class TestInstanceConfigurer(unittest.TestCase):
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

        test_name = "Test_Instance_Conf"
        node_name = test_name + "_Node"
        vcn_name = test_name + "_Network"
        subnet_name = test_name + "_Subnet"

        # Add unique test postfix
        if "OCI_TEST_ID" in os.environ:
            node_name += os.environ["OCI_TEST_ID"]
            vcn_name += os.environ["OCI_TEST_ID"]
            subnet_name += os.environ["OCI_TEST_ID"]

        compute_options = dict(
            availability_domain="lfcb:EU-FRANKFURT-1-AD-1",
            shape="VM.Standard1.1",
            operating_system="CentOS",
            operating_system_version="7",
            display_name=node_name,
        )

        pub_file = None
        # TODO, add OCI_INSTANCE_PUB_PATH

        if "OCI_INSTANCE_PUB_KEY" in os.environ:
            pub_file = os.environ["OCI_INSTANCE_PUB_KEY"]

        if "OCI_INSTANCE_PUB_PATH" in os.environ:
            pub_path = os.environ["OCI_INSTANCE_PUB_PATH"]
            if not os.path.exists(pub_path):
                raise ValueError(
                    "The specified OCI_INSTANCE_PUB_PATH path: {} does not exist".format(
                        pub_path
                    )
                )

            with open(pub_path, "r") as pub_file:
                pub_file = pub_file.read()

        if not pub_file:
            raise ValueError(
                "Either OCI_INSTANCE_PUB_KEY or OCI_INSTANCE_PUB_PATH"
                "environment variable must be set"
            )

        compute_metadata_options = dict(ssh_authorized_keys=[pub_file])

        vcn_options = dict(
            cidr_block="10.0.0.0/16", display_name=vcn_name, dns_label="ku",
        )
        subnet_options = dict(display_name=subnet_name, dns_label="workers")

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

    def tearDown(self):
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator = None
        self.options = None

    def test_instance_ansible_configure(self):
        # Extract the ip of the instance
        endpoint = self.orchestrator.endpoint()
        options = dict(playbook_path=playbook_path, hosts=[endpoint],)
        configurer = AnsibleConfigurer(options)
        configurer.apply()


if __name__ == "__main__":
    unittest.main()
