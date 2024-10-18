import unittest
from io import StringIO
from unittest.mock import patch
from corc.cli.return_codes import SUCCESS
from corc.cli.cli import main


class TestCLILibvirt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider_name = "libvirt_provider"

    @patch("sys.stdout", new_callable=StringIO)
    def test_cli_orchestration_add_provider_libvirt(self, mock_stdout):
        return_code = main(["orchestration", "add_provider", self.provider_name])
        self.assertEqual(return_code, SUCCESS)

        # Verify that the provider is added
        list_return_code = main(["orchestration", "list_providers"])
        self.assertEqual(list_return_code, SUCCESS)
        list_output = mock_stdout.getvalue()
        self.assertIn(self.provider_name, list_output)

    def test_cli_orchestration_remove_provider_libvirt(self):
        add_return_code = main(["orchestration", "add_provider", self.provider_name])
        self.assertEqual(add_return_code, SUCCESS)

        remove_return_code = main(
            ["orchestration", "remove_provider", self.provider_name]
        )
        self.assertEqual(remove_return_code, SUCCESS)


if __name__ == "__main__":
    unittest.main()
