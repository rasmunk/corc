import subprocess
import unittest


class TestCLI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Install the cli
        args = ["pip3", "install", ".", "-q"]
        result = subprocess.run(args)
        assert result is not None
        assert hasattr(result, "returncode")
        assert result.returncode == 0

    @classmethod
    def tearDownClass(cls):
        args = ["pip3", "uninstall", "corc", "-y"]
        result = subprocess.run(args)
        assert result is not None
        assert hasattr(result, "returncode")
        assert result.returncode == 0

    def test_cli_help(self):
        args = ["corc", "-h"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
