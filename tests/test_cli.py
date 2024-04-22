import os
import subprocess
import unittest


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
        self.test_name = "Test_CLI"

        # Add unique test postfix
        test_id = str(uuid.uuid4())
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


if __name__ == "__main__":
    unittest.main()
