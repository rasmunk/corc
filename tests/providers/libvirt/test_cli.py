# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

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
