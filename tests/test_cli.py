import unittest
from corc.cli.return_codes import SUCCESS
from corc.cli.cli import main


class TestCLI(unittest.TestCase):

    def test_cli_help(self):
        return_code = None
        try:
            return_code = main(["-h"])
        except SystemExit as e:
            return_code = e.code
        self.assertEqual(return_code, SUCCESS)
