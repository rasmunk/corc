import os
import time
import unittest

# from corc.providers.types import get_orchestrator, CONTAINER, LOCAL
from corc.authenticator import SSHAuthenticator, gen_ssh_credentials
from corc.config import load_from_env_or_config, gen_config_provider_prefix
from corc.configurer import AnsibleConfigurer
from corc.providers.oci.instance import OCIInstanceOrchestrator


current_dir = os.path.dirname(os.path.abspath(__file__))
playbook_path = os.path.join(current_dir, "res", "configurer", "playbook.yml")


class TestInstanceConfigurer(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
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
        oci_profile_options = dict(compartment_id=oci_compartment_id, name=oci_name,)

        test_name = "Test_Instance_Conf"
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
            availability_domain="lfcb:EU-FRANKFURT-1-AD-1",
            shape="VM.Standard1.1",
            operating_system="CentOS",
            operating_system_version="7",
            display_name=node_name,
        )

        credentials = gen_ssh_credentials(
            ssh_dir_path=os.path.join(self.test_dir, "ssh")
        )
        self.authenticator = SSHAuthenticator(credentials=credentials)
        self.authenticator.store_credentials()

        instance_metadata_options = dict(
            ssh_authorized_keys=[self.authenticator.credentials.public_key]
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

        vcn_options = dict(
            cidr_block="10.0.0.0/16", display_name=vcn_name, dns_label="ku",
        )
        subnet_options = dict(display_name=subnet_name, dns_label="workers")

        self.options = dict(
            profile=oci_profile_options,
            instance=instance_options,
            instance_metadata=instance_metadata_options,
            vcn=vcn_options,
            internetgateway=internet_gateway_options,
            routetable=route_table_options,
            subnet=subnet_options,
        )

        OCIInstanceOrchestrator.validate_options(self.options)
        self.orchestrator = OCIInstanceOrchestrator(self.options)
        # Should not be ready at this point
        self.orchestrator.setup(credentials=[self.authenticator.credentials])
        self.assertTrue(self.orchestrator.is_ready())
        # Ensure that the orchestrated instance is reachable
        reachable = self.orchestrator.is_reachable()
        num_waited, max_wait = 0, 60

        while not reachable:
            self.orchestrator.poll()
            reachable = self.orchestrator.is_reachable()
            if num_waited > max_wait:
                print(
                    "The maximum number of waits: '{}' for the orchestrated instance to "
                    "be reachable was exceeded".format(max_wait)
                )
                break
            time.sleep(1)
            num_waited += 1
        self.assertTrue(reachable)
        self.endpoint = self.orchestrator.endpoint()
        self.assertIsNotNone(self.endpoint)
        self.assertTrue(self.authenticator.prepare(self.endpoint))

    def tearDown(self):
        self.assertTrue(self.authenticator.cleanup(self.endpoint))
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator = None
        self.endpoint = None
        self.options = None

    def test_instance_ansible_configure(self):
        # Extract the ip of the instance
        options = dict(
            host_variables=dict(
                ansible_user="opc",
                ansible_become="yes",
                ansible_become_method="sudo",
                verbosity=4,
            ),
            host_settings=dict(group="compute", port="22"),
            apply_kwargs=dict(playbook_path=playbook_path),
        )

        configurer = AnsibleConfigurer()
        configuration = configurer.gen_configuration(options)
        configurer.apply(
            self.endpoint,
            configuration=configuration,
            credentials=self.authenticator.credentials,
        )


if __name__ == "__main__":
    unittest.main()
