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
from corc.cli.return_codes import SUCCESS
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.orchestration.pool.remove_instance import remove_instance
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
        pool = DictDatabase(self.name, directory=CURRENT_TEST_DIR)
        for node in await pool.items():
            removed, response = await remove_instance(self.client, node.id)
            self.assertTrue(removed)
        self.assertTrue(await pool.flush())
        self.assertEqual(len(await pool.items()), 0)
        self.assertTrue(await pool.remove_persistence())

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

    async def test_pool_persistence_path(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"
        create_pool_args = copy.deepcopy(self.base_args)
        create_pool_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])

        return_code = execute_func_in_future(main, create_pool_args)
        self.assertEqual(return_code, SUCCESS)

        pool = DictDatabase(name, directory=CURRENT_TEST_DIR)
        self.assertIsNotNone(pool)
        self.assertEqual(pool.name, name)

        # Verify that the persistence database exists in the expected path
        self.assertTrue(exists(pool.get_database_path()))

    async def test_dummy_pool_create(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"
        create_pool_args = copy.deepcopy(self.base_args)
        create_pool_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])
        return_code = execute_func_in_future(main, create_pool_args)
        self.assertEqual(return_code, SUCCESS)

        # Check that the pool exists
        pool = DictDatabase(name, directory=CURRENT_TEST_DIR)
        self.assertIsNotNone(pool)
        self.assertEqual(pool.name, name)
        self.assertTrue(exists(pool.get_database_path()))

        # Remove and validate that it is gone
        self.assertTrue(await pool.flush())
        self.assertTrue(await pool.remove_persistence())
        self.assertFalse(await pool.exists())

    async def test_dummy_pool_remove(self):
        # Create a pool that can be removed by the CLI
        test_id = str(uuid.uuid4())
        pool_name = "dummy-remove-test-{}".format(test_id)
        remove_pool = DictDatabase(pool_name, directory=CURRENT_TEST_DIR)
        self.assertTrue(await remove_pool.touch())
        self.assertTrue(exists(remove_pool.get_database_path()))

        remove_pool_args = copy.deepcopy(self.base_args)
        remove_pool_args.extend(["remove", pool_name, "--directory", CURRENT_TEST_DIR])

        return_code = execute_func_in_future(main, remove_pool_args)
        self.assertEqual(return_code, SUCCESS)
        self.assertFalse(await remove_pool.exists())
        self.assertFalse(exists(remove_pool.get_database_path()))

    @patch("sys.stdout", new_callable=StringIO)
    async def test_dummy_pool_list_empty(self, mock_stdout):
        list_pools_args = copy.deepcopy(self.base_args)
        list_pools_args.extend(["ls", "--directory", CURRENT_TEST_DIR])

        list_return_code = execute_func_in_future(main, list_pools_args)
        self.assertEqual(list_return_code, SUCCESS)
        list_output = mock_stdout.getvalue()
        self.assertListEqual(json.loads(list_output)["pools"], [])

    async def test_dummy_pool_create_multiple(self):
        test_id = str(uuid.uuid4())
        # Add pools
        pool1, pool2, pool3 = (
            DictDatabase(f"{test_id}-{self.name}-1", directory=CURRENT_TEST_DIR),
            DictDatabase(f"{test_id}-{self.name}-2", directory=CURRENT_TEST_DIR),
            DictDatabase(f"{test_id}-{self.name}-3", directory=CURRENT_TEST_DIR),
        )
        pools = [pool1, pool2, pool3]
        for pool in pools:
            create_pool_args = copy.deepcopy(self.base_args)
            create_pool_args.extend(
                ["create", pool.name, "--directory", pool.directory]
            )

            return_code = execute_func_in_future(main, create_pool_args)
            self.assertEqual(return_code, SUCCESS)

        for pool in pools:
            # Check that the pool exists
            self.assertIsNotNone(pool)
            self.assertTrue(await pool.exists())

    async def test_dummy_pool_remove_multiple(self):
        test_id = str(uuid.uuid4())
        # Add pools
        pool1, pool2, pool3 = (
            f"{test_id}-{self.name}-1",
            f"{test_id}-{self.name}-2",
            f"{test_id}-{self.name}-3",
        )
        pools = [pool1, pool2, pool3]
        for pool in pools:
            create_pool_args = copy.deepcopy(self.base_args)
            create_pool_args.extend(["create", pool, "--directory", CURRENT_TEST_DIR])

            return_code = execute_func_in_future(main, create_pool_args)
            self.assertEqual(return_code, SUCCESS)

        for pool in pools:
            # Remove pools
            remove_pool_args = copy.deepcopy(self.base_args)
            remove_pool_args.extend(["remove", pool, "--directory", CURRENT_TEST_DIR])

            return_code = execute_func_in_future(main, remove_pool_args)
            self.assertEqual(return_code, SUCCESS)

    async def test_dummy_pool_add_instance(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"
        # Create the pool
        create_pool_args = copy.deepcopy(self.base_args)
        create_pool_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])
        return_code = execute_func_in_future(main, create_pool_args)
        self.assertEqual(return_code, SUCCESS)

        created_pool = DictDatabase(name, directory=CURRENT_TEST_DIR)
        self.assertTrue(created_pool.get_database_path())

        # Add instance to the pool
        add_instance_args = copy.deepcopy(self.base_args)
        instance_name = f"dummy-instance-{test_id}"
        add_instance_args.extend(
            ["add_instance", name, instance_name, "--directory", CURRENT_TEST_DIR]
        )
        return_code = execute_func_in_future(main, add_instance_args)
        self.assertEqual(return_code, SUCCESS)

    async def test_dummy_pool_remove_instance(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"
        # Create the pool
        create_pool_args = copy.deepcopy(self.base_args)
        create_pool_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])
        return_code = execute_func_in_future(main, create_pool_args)
        self.assertEqual(return_code, SUCCESS)

        created_pool = DictDatabase(name, directory=CURRENT_TEST_DIR)
        self.assertTrue(exists(created_pool.get_database_path()))

        # Add instance to the pool
        add_instance_args = copy.deepcopy(self.base_args)
        instance_name = f"dummy-instance-{test_id}"
        add_instance_args.extend(
            ["add_instance", name, instance_name, "--directory", CURRENT_TEST_DIR]
        )
        return_code = execute_func_in_future(main, add_instance_args)
        self.assertEqual(return_code, SUCCESS)

        # Remove instance from the pool
        remove_instance_args = copy.deepcopy(self.base_args)
        remove_instance_args.extend(
            ["remove_instance", name, instance_name, "--directory", CURRENT_TEST_DIR]
        )
        return_code = execute_func_in_future(main, remove_instance_args)
        self.assertEqual(return_code, SUCCESS)
