import os
import subprocess
import unittest
from corc.config import load_from_env_or_config, gen_config_prefix


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
        self.config_path = os.path.join(self.test_dir, "config")

        self.test_name = "Test_CLI"
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

    def test_cli_help(self):
        args = ["corc", "-h"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    def test_cli_config(self):
        args = ["corc", "config"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    def test_cli_config_oci_generate(self):
        args = ["corc", "config", "oci", "generate", "--config-path", self.config_path]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

        # Check that the config is generated
        self.assertTrue(os.path.exists(self.config_path))
        # Clean up
        os.remove(self.config_path)
        self.assertFalse(os.path.exists(self.config_path))

    def test_cli_config_ec2_generate(self):
        args = ["corc", "config", "ec2", "generate", "--config-path", self.config_path]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

        # Check that the config is generated
        self.assertTrue(os.path.exists(self.config_path))
        # Clean up
        os.remove(self.config_path)
        self.assertFalse(os.path.exists(self.config_path))

    def test_cli_oci_help(self):
        args = ["corc", "oci", "-h"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    def test_cli_ec2_help(self):
        args = ["corc", "ec2", "-h"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    # def test_cli_oci_orchestration_instance(self):
    #     # Ensure that a config exist with the proper
    #     # provider settings
    #     # TODO, make it so that the provider specific
    #     # profile options can be set as part of the provider
    #     # positional argument so we don't have to:
    #     # load -> save -> load

    #     # TODO Create test compartment
    #     base_args = ["corc", "oci", "orchestration", "instance"]
    #     get_args = copy.deepcopy(base_args)
    #     get_args.extend(["get"])

    #     list_args = copy.deepcopy(base_args)
    #     list_args.extend(["list"])

    #     start_args = copy.deepcopy(base_args)
    #     start_args.extend(["start", "--instance-display-name", self.instance_name])

    #     stop_args = copy.deepcopy(base_args)
    #     stop_args.extend(["stop"])

    #     # List args (should be empty)
    #     result = subprocess.run(list_args, capture_output=True)
    #     self.assertIsNotNone(result)
    #     self.assertTrue(hasattr(result, "returncode"))
    #     self.assertEqual(result.returncode, 0, result.stderr)
    #     content = json.loads(result.stdout.decode("utf-8"))
    #     self.assertIn(
    #         "instances", content, "{}: did not have instances".format(content)
    #     )

    #     # Start an instance
    #     result = subprocess.run(start_args, capture_output=True)
    #     self.assertIsNotNone(result)
    #     self.assertTrue(hasattr(result, "returncode"))
    #     self.assertEqual(result.returncode, 0, result.stderr)
    #     content = json.loads(result.stdout.decode("utf-8"))
    #     self.assertIn("id", content, "id is missing from {}".format(content))
    #     assigned_id = content["id"]
    #     self.assertIsNotNone(assigned_id)

    #     get_args.extend(["--instance-id", assigned_id])
    #     # Get the instance
    #     result = subprocess.run(get_args, capture_output=True)
    #     self.assertIsNotNone(result)
    #     self.assertTrue(hasattr(result, "returncode"))
    #     self.assertEqual(result.returncode, 0, result.stderr)
    #     content = json.loads(result.stdout.decode("utf-8"))
    #     self.assertIn("id", content, "id is missing from {}".format(content))
    #     self.assertEqual(content["id"], assigned_id)

    #     # Stop the instance
    #     stop_args.extend(["--instance-id", assigned_id])
    #     result = subprocess.run(stop_args, capture_output=True)
    #     self.assertIsNotNone(result)
    #     self.assertTrue(hasattr(result, "returncode"))
    #     self.assertEqual(result.returncode, 0, result.stderr)
    #     content = json.loads(result.stdout.decode("utf-8"))
    #     self.assertIn("id", content, "id is missing from {}".format(content))

    #     # List args (should be empty)
    #     result = subprocess.run(get_args, capture_output=True)
    #     self.assertIsNotNone(result)
    #     self.assertTrue(hasattr(result, "returncode"))
    #     self.assertEqual(result.returncode, 0, result.stderr)
    #     content = json.loads(result.stdout.decode("utf-8"))
    #     # Assure that it is terminating
    #     self.assertIn("id", content, "id is missing from {}".format(content))
    #     self.assertEqual(content["id"], assigned_id)
    #     self.assertIn("instance", content, "{}: did not have instance".format(content))
    #     state = content["instance"][0]["lifecycle_state"]
    #     self.assertIn(state, ["TERMINATING", "TERMINATED"])

    # def test_cli_oci_orchestration_cluster(self):
    #     # TODO Create test compartment
    #     base_args = ["corc", "oci", "orchestration", "cluster"]
    #     get_args = copy.deepcopy(base_args)
    #     get_args.extend(["get"])

    #     list_args = copy.deepcopy(base_args)
    #     list_args.extend(["list"])

    #     start_args = copy.deepcopy(base_args)
    #     start_args.extend(["start", "--cluster-name", self.cluster_name])

    #     stop_args = copy.deepcopy(base_args)
    #     stop_args.extend(["stop"])

    #     # List args (should be empty)
    #     result = subprocess.run(list_args, capture_output=True)
    #     self.assertIsNotNone(result)
    #     self.assertTrue(hasattr(result, "returncode"))
    #     self.assertEqual(result.returncode, 0, result.stderr)
    #     content = json.loads(result.stdout.decode("utf-8"))
    #     self.assertIn("clusters", content, "{}: did not have clusters".format(content))

    #     # Start an instance
    #     result = subprocess.run(start_args, capture_output=True)
    #     self.assertIsNotNone(result)
    #     self.assertTrue(hasattr(result, "returncode"))
    #     self.assertEqual(result.returncode, 0, result.stderr)
    #     content = json.loads(result.stdout.decode("utf-8"))
    #     self.assertIn("id", content, "{}: did not have id".format(content))
    #     assigned_id = content["id"]
    #     self.assertIsNotNone(assigned_id)

    #     get_args.extend(["--cluster-id", assigned_id])
    #     # Get the instance
    #     result = subprocess.run(get_args, capture_output=True)
    #     self.assertIsNotNone(result)
    #     self.assertTrue(hasattr(result, "returncode"))
    #     self.assertEqual(result.returncode, 0, result.stderr)
    #     content = json.loads(result.stdout.decode("utf-8"))
    #     self.assertIn("id", content, "{}: did not have id".format(content))
    #     self.assertEqual(content["id"], assigned_id)

    #     # Stop the instance
    #     stop_args.extend(["--cluster-id", assigned_id])
    #     result = subprocess.run(stop_args, capture_output=True)
    #     self.assertIsNotNone(result)
    #     self.assertTrue(hasattr(result, "returncode"))
    #     self.assertEqual(result.returncode, 0, result.stderr)
    #     content = json.loads(result.stdout.decode("utf-8"))
    #     self.assertIn("id", content, "{}: did not have id".format(content))
    #     self.assertEqual(content["id"], assigned_id)

    #     # List args (should be empty)
    #     result = subprocess.run(get_args, capture_output=True)
    #     self.assertIsNotNone(result)
    #     self.assertTrue(hasattr(result, "returncode"))
    #     self.assertEqual(result.returncode, 0, result.stderr)
    #     content = json.loads(result.stdout.decode("utf-8"))
    #     # Assure that it is terminating
    #     self.assertIn("id", content, "{}: did not have id".format(content))
    #     self.assertEqual(content["id"], assigned_id)
    #     self.assertIn("cluster", content, "{}: did not have cluster".format(content))
    #     state = content["cluster"][0]["lifecycle_state"]
    #     self.assertIn(state, ["DELETED", "DELETING"])


if __name__ == "__main__":
    unittest.main()
