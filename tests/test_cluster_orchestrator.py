import sys
import os

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_path, "orchestration"))

import unittest
from cluster import OCIClusterOrchestrator


class TestClusterOrchestrator(unittest.TestCase):
    def setUp(self):
        oci_options = dict(
            compartment_id="ocid1.tenancy.oc1..aaaaaaaakfmksyrf7hl2gfexmjpb6pbyrirm6k3ro7wd464y2pr7atpxpv4q",
            profile_name="XNOVOTECH",
        )
        cluster_options = dict(name="Test XNOVOTECH Cluster",)
        node_options = dict(
            availability_domain="Xfze:eu-amsterdam-1-AD-1",
            name="test_xnovotech_cluster",
            size=1,
            node_shape="VM.Standard2.1",
            node_image_name="Oracle-Linux-7.7",
        )

        vcn_options = dict(
            cidr_block="10.0.0.0/16", display_name="Test XNOVOTECH Network"
        )
        self.options = dict(
            oci=oci_options, cluster=cluster_options, node=node_options, vcn=vcn_options
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

    def test_prepare_cluster(self):
        self.orchestrator.prepare()
        self.assertTrue(self.orchestrator.is_ready())

    def test_teardown_cluster(self):
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())

    def test_schedule_task(self):
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()