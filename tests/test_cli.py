import subprocess
import unittest
import uuid


class TestCLI(unittest.TestCase):
    def setUp(self):
        # Add unique test postfix
        test_id = str(uuid.uuid4())
        self.instance_name = "instance-{}".format(test_id)
        self.cluster_name = "instance-{}".format(test_id)

        # Install the cli
        args = ["pip3", "install", ".", "-q"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    def tearDown(self):
        pass

    def test_cli_help(self):
        args = ["corc", "-h"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
