import os
import subprocess
import unittest


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
        self.config_path = os.path.join(self.test_dir, "config")
        # Install the cli
        args = ["python3", "setup.py", "install"]
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

    def test_cli_ec2_help(self):
        args = ["corc", "ec2", "-h"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
