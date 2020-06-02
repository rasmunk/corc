import unittest
from corc.oci.cluster import OCIClusterOrchestrator


class TestClusterOrchestrator(unittest.TestCase):
    def setUp(self):
        oci_options = dict(
            compartment_id="ocid1.compartment.oc1..aaaaaaaashnazvohptud5up2i5dxbqbsnwp3b"
            "gcubjj75qkqw3zvgxlvoq5a",
            profile_name="KU",
        )
        cluster_options = dict(name="Test KU Orchestration Cluster",)

        image_options = dict(display_name="Oracle-Linux-7.7-2020.03.23-0",)
        node_options = dict(
            availability_domain="lfcb:EU-FRANKFURT-1-AD-1",
            name="test_ku_cluster_orchestration",
            size=1,
            node_shape="VM.Standard2.1",
            image=image_options,
        )

        vcn_options = dict(
            cidr_block="10.0.0.0/16",
            display_name="Test Cluster Orchestration Network",
            dns_label="ku",
        )

        subnet_options = dict(dns_label="workers")

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
