import subprocess
import unittest


class TestCLILibvirt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider_name = "libvirt_provider"
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
