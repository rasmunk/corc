import os
import subprocess
import unittest
from corc.core.config import load_from_env_or_config, gen_config_prefix


class TestCLILibvirt(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
        self.config_path = os.path.join(self.test_dir, "config")

        self.provider_name = "libvirt_provider"
        self.test_name = self.provider_name + "Test_CLI"
        self.instance_name = self.test_name + "_Instance"
        self.cluster_name = self.test_name + "_Cluster"

        # Add unique test postfix
        test_id = load_from_env_or_config(
            {"test": {"id": {}}}, prefix=gen_config_prefix()
        )
        if test_id:
            self.instance_name += test_id
            self.cluster_name += test_id

        # Install the cli
        args = ["pip3", "install", ".", "-q"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.assertFalse(os.path.exists(self.config_path))

    def test_cli_orchestration_add_provider_libvirt(self):
        args = ["corc", "orchestration", "add_provider", self.provider_name]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

        # Verify that the provider is added
        args = ["corc", "orchestration", "list_providers"]
        result = subprocess.run(args)
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
