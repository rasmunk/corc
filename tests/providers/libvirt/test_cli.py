import os
import subprocess
import unittest
import copy
from corc.config import load_from_env_or_config, gen_config_prefix


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
        self.config_path = os.path.join(self.test_dir, "config")

        self.provider_name = "Libvirt_"
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

    def test_cli_libvirt_config_help(self):
        args = ["corc", "config", "libvirt", "-h"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    def test_cli_libvirt_config_generate(self):
        args = ["corc", "config", "libvirt", "generate", "--config-path", self.config_path]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

        # Check that the config is generated
        self.assertTrue(os.path.exists(self.config_path))
        # Clean up
        os.remove(self.config_path)
        self.assertFalse(os.path.exists(self.config_path))

    def test_cli_instance_help(self):
        args = ["corc", "instance", "orchestration", "libvirt", "-h"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    def test_cli_instance_start(self):
        args = ["corc", "instance", "orchestration", "libvirt"]

        # Start an instance
        start_args = copy.deepcopy(args)
        start_args.extend(["start", "--instance-name", self.instance_name])
        start_result = subprocess.run(start_args)
        self.assertIsNotNone(start_result)
        self.assertTrue(hasattr(start_result, "returncode"))
        self.assertEqual(start_result.returncode, 0)

    def test_cli_instance_get(self):
        args = ["corc", "instance", "orchestration", "libvirt"]
        
        # Get the started instance
        get_args = copy.deepcopy(args)
        get_args.extend(["get", "--instance-name", self.instance_name])
        get_result = subprocess.run(get_args)
        self.assertIsNotNone(get_result)
        self.assertTrue(hasattr(get_result, "returncode"))
        self.assertEqual(get_result.returncode, 0)

    def test_clit_instance_stop(self):
        args = ["corc", "instance", "orchestration", "libvirt"]

        # Stop the started instance
        stop_args = copy.deepcopy(args)
        stop_args.extend(["stop", "--instance-name", self.instance_name])
        stop_result = subprocess.run(stop_args)
        self.assertIsNotNone(stop_result)
        self.assertTrue(hasattr(stop_result, "returncode"))
        self.assertEqual(stop_result.returncode, 0)

    # def test_cli_instance_delete(self):
    #     args = ["corc", "instance", "orchestration", "libvirt"]

    #     # Delete the instance
    #     delete_args = copy.deepcopy(args)
    #     delete_args.extend(["delete", "--instance-name", self.instance_name])
    #     delete_result = subprocess.run(delete_args)
    #     self.assertIsNotNone(delete_result)
    #     self.assertTrue(hasattr(delete_result, "returncode"))
    #     self.assertEqual(delete_result.returncode, 0)

if __name__ == "__main__":
    unittest.main()
