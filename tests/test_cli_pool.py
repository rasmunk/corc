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

import os
import copy
import unittest
import uuid
import json
from io import StringIO
from unittest.mock import patch
from corc.cli.cli import main
from corc.core.defaults import POOL
from corc.cli.return_codes import SUCCESS, FAILURE
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.orchestration.pool.create import create
from corc.utils.io import exists, makedirs, removedirs

# Because the main function spawns an event loop, we cannot execute the
# main function directly in the current event loop.
# Therefore we execute the function in a separate thread such
# that it will instantiate its own event loop
from tests.utils import execute_func_in_future
from tests.common import TMP_TEST_PATH

TEST_NAME = os.path.basename(__file__).split(".")[0]
CURRENT_TEST_DIR = os.path.join(TMP_TEST_PATH, TEST_NAME)


class TestCliDictDatabase(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.name = "pool"
        self.base_args = ["orchestration", self.name]
        if not exists(CURRENT_TEST_DIR):
            self.assertTrue(makedirs(CURRENT_TEST_DIR))

    async def asyncTearDown(self):
        # Ensure that any pool is destroyed
        pool_db = DictDatabase(POOL, directory=CURRENT_TEST_DIR)
        self.assertTrue(await pool_db.flush())
        self.assertEqual(len(await pool_db.items()), 0)
        self.assertTrue(await pool_db.remove_persistence())

        if exists(CURRENT_TEST_DIR):
            self.assertTrue(removedirs(CURRENT_TEST_DIR, recursive=True))

    async def test_help_msg(self):
        help_args = copy.deepcopy(self.base_args)
        help_args.extend(["--help"])

        try:
            _ = execute_func_in_future(main, help_args)
        except SystemExit as e:
            return_code = e.code
        self.assertEqual(return_code, SUCCESS)

    async def test_dummy_pool_create(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"
        create_pool_args = copy.deepcopy(self.base_args)
        create_pool_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])

        with patch("sys.stdout", new=StringIO()) as captured_stdout:
            return_code = execute_func_in_future(main, create_pool_args)
            self.assertEqual(return_code, SUCCESS)

            created_response = json.loads(captured_stdout.getvalue())
            self.assertIsInstance(created_response, dict)
            self.assertIn("id", created_response)
            pool_id = created_response["id"]
            self.assertIn("pool", created_response)
            self.assertIsInstance(created_response["pool"], dict)
            self.assertIn("name", created_response["pool"])
            self.assertEqual(name, created_response["pool"]["name"])

            # Check that the pool exists
            pool_db = DictDatabase(POOL, directory=CURRENT_TEST_DIR)
            created_db_pool = await pool_db.get(pool_id)
            self.assertIsNotNone(created_db_pool)
            self.assertIsInstance(created_db_pool, dict)
            self.assertEqual(created_response["pool"], created_db_pool)

    async def test_dummy_pool_remove(self):
        # Create a pool that can be removed by the CLI
        test_id = str(uuid.uuid4())
        pool_name = "dummy-remove-test-{}".format(test_id)

        created_pool, created_response = await create(
            pool_name, directory=CURRENT_TEST_DIR
        )
        self.assertTrue(created_pool)

        remove_pool_args = copy.deepcopy(self.base_args)
        remove_pool_args.extend(["remove", pool_name, "--directory", CURRENT_TEST_DIR])
        remove_return_code = execute_func_in_future(main, remove_pool_args)
        self.assertEqual(remove_return_code, SUCCESS)

        show_pool_args = copy.deepcopy(self.base_args)
        show_pool_args.extend(["show", pool_name, "--directory", CURRENT_TEST_DIR])
        with patch("sys.stderr", new=StringIO()) as captured_stdout:
            show_return_code = execute_func_in_future(main, show_pool_args)
            self.assertEqual(show_return_code, FAILURE)
            output = json.loads(captured_stdout.getvalue())
            self.assertIsInstance(output, dict)
            self.assertEqual(output["status"], "failed")

    async def test_dummy_pool_list_empty(self):
        list_pools_args = copy.deepcopy(self.base_args)
        list_pools_args.extend(["ls", "--directory", CURRENT_TEST_DIR])

        with patch("sys.stdout", new=StringIO()) as captured_stdout:
            list_return_code = execute_func_in_future(main, list_pools_args)
            self.assertEqual(list_return_code, SUCCESS)
            list_output = captured_stdout.getvalue()
            self.assertListEqual(json.loads(list_output)["pools"], [])

    async def test_dummy_pool_create_multiple(self):
        test_id = str(uuid.uuid4())
        # Add pools
        pools = [
            {"name": f"{test_id}-{self.name}-1", "directory": CURRENT_TEST_DIR},
            {"name": f"{test_id}-{self.name}-2", "directory": CURRENT_TEST_DIR},
            {"name": f"{test_id}-{self.name}-3", "directory": CURRENT_TEST_DIR},
        ]

        created_pools = []
        for pool in pools:
            create_pool_args = copy.deepcopy(self.base_args)
            create_pool_args.extend(
                ["create", pool["name"], "--directory", pool["directory"]]
            )
            with patch("sys.stdout", new=StringIO()) as captured_stdout:
                return_code = execute_func_in_future(main, create_pool_args)
                self.assertEqual(return_code, SUCCESS)
                created_output = json.loads(captured_stdout.getvalue())
                created_pools.append(created_output)

        for pool in created_pools:
            list_pool_args = copy.deepcopy(self.base_args)
            list_pool_args.extend(["show", pool["id"], "--directory", CURRENT_TEST_DIR])

            return_code = execute_func_in_future(main, list_pool_args)
            self.assertEqual(return_code, SUCCESS)

    async def test_dummy_pool_remove_multiple(self):
        test_id = str(uuid.uuid4())
        # Add pools
        pool1, pool2, pool3 = (
            f"{test_id}-{self.name}-1",
            f"{test_id}-{self.name}-2",
            f"{test_id}-{self.name}-3",
        )
        pools = [pool1, pool2, pool3]

        created_pools = []
        for pool in pools:
            create_pool_args = copy.deepcopy(self.base_args)
            create_pool_args.extend(["create", pool, "--directory", CURRENT_TEST_DIR])

            with patch("sys.stdout", new=StringIO()) as captured_stdout:
                return_code = execute_func_in_future(main, create_pool_args)
                self.assertEqual(return_code, SUCCESS)
                created_output = json.loads(captured_stdout.getvalue())
                created_pools.append(created_output)

        for pool in created_pools:
            # Remove pools
            remove_pool_args = copy.deepcopy(self.base_args)
            remove_pool_args.extend(
                ["remove", pool["id"], "--directory", CURRENT_TEST_DIR]
            )

            return_code = execute_func_in_future(main, remove_pool_args)
            self.assertEqual(return_code, SUCCESS)

    async def test_dummy_pool_add_instance(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"
        # Create the pool
        pool_id = None
        create_pool_args = copy.deepcopy(self.base_args)
        create_pool_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])
        with patch("sys.stdout", new=StringIO()) as captured_stdout:
            return_code = execute_func_in_future(main, create_pool_args)
            self.assertEqual(return_code, SUCCESS)
            created_output = json.loads(captured_stdout.getvalue())
            pool_id = created_output["id"]

        # Add instance to the pool
        add_instance_args = copy.deepcopy(self.base_args)
        instance_name = f"dummy-instance-{test_id}"
        add_instance_args.extend(
            ["add_instance", pool_id, instance_name, "--directory", CURRENT_TEST_DIR]
        )
        return_code = execute_func_in_future(main, add_instance_args)
        self.assertEqual(return_code, SUCCESS)

    async def test_dummy_pool_remove_instance(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"
        # Create the pool
        pool_id = None
        create_pool_args = copy.deepcopy(self.base_args)
        create_pool_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])
        with patch("sys.stdout", new=StringIO()) as captured_stdout:
            return_code = execute_func_in_future(main, create_pool_args)
            self.assertEqual(return_code, SUCCESS)
            created_output = json.loads(captured_stdout.getvalue())
            pool_id = created_output["id"]

        # Add instance to the pool
        add_instance_args = copy.deepcopy(self.base_args)
        instance_name = f"dummy-instance-{test_id}"
        add_instance_args.extend(
            ["add_instance", pool_id, instance_name, "--directory", CURRENT_TEST_DIR]
        )
        return_code = execute_func_in_future(main, add_instance_args)
        self.assertEqual(return_code, SUCCESS)

        # Remove instance from the pool
        remove_instance_args = copy.deepcopy(self.base_args)
        remove_instance_args.extend(
            ["remove_instance", pool_id, instance_name, "--directory", CURRENT_TEST_DIR]
        )
        return_code = execute_func_in_future(main, remove_instance_args)
        self.assertEqual(return_code, SUCCESS)
