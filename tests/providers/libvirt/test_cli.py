import os
import subprocess
import unittest
import uuid


class TestCLILibvirt(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")

        self.provider_name = "libvirt_provider"
        self.test_name = self.provider_name + "Test_CLI"
        test_id = uuid.uuid4().hex

        self.instance_name = "instance-{}".format(test_id)

        # Install the cli
        args = ["pip3", "install", ".", "-q"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    def tearDown(self):
        pass

    def test_cli_orchestration_add_provider_libvirt(self):
        args = ["corc", "orchestration", "add_provider", self.provider_name]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

        # Verify that the provider is added
        args = ["corc", "orchestration", "list_providers"]
        result = subprocess.run(args, capture_output=True)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)
        self.assertIn(self.provider_name, str(result.stdout))

    def test_cli_orchestration_remove_provider_libvirt(self):
        args = ["corc", "orchestration", "remove_provider", self.provider_name]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
