import unittest
from corc.providers.defaults import EC2, INSTANCE
from corc.providers.types import get_orchestrator


class TestEC2InstanceOrchestrator(unittest.TestCase):
    def setUp(self):
        test_name = "Test_Instance_Orch"
        node_name = test_name + "_Node"

        compute_options = dict(name=node_name)
        # (access_key_id)
        ec2_args = ("AKIAT7Z3YSHTWQ5UMZS2",)
        ec2_kwargs = {"secret": "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"}

        self.options = dict(compute=compute_options)
        EC2Orchestrator, options = get_orchestrator(INSTANCE, EC2)
        options["driver"]["args"] = ec2_args
        options["driver"]["kwargs"] = ec2_kwargs
        self.options.update(options)

        EC2Orchestrator.validate_options(self.options)
        self.orchestrator = EC2Orchestrator(self.options)
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
