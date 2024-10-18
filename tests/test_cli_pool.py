import copy
import unittest
import uuid
import json
from io import StringIO
from unittest.mock import patch
from corc.cli.cli import main
from corc.cli.return_codes import SUCCESS
from corc.core.orchestration.pool.models import Pool
from corc.core.orchestration.pool.remove_instance import remove_instance

# Because the main function spawns an event loop, we cannot execute the
# main function directly in the current event loop.
# Therefore we execute the function in a separate thread such
# that it will instantiate its own event loop
from tests.utils import execute_func_in_future


class TestCliPool(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.name = "pool"
        self.base_args = ["orchestration", self.name]

    async def asyncTearDown(self):
        # Ensure that any pool is destroyed
        pool = Pool(self.name)
        for node in await pool.items():
            removed, response = await remove_instance(self.client, node.id)
            self.assertTrue(removed)
        self.assertTrue(await pool.flush())
        self.assertEqual(len(await pool.items()), 0)
        self.assertTrue(await pool.remove_persistence())

    async def test_dummy_pool_create(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"
        create_pool_args = copy.deepcopy(self.base_args)
        create_pool_args.extend(["create", name])

        return_code = execute_func_in_future(main, create_pool_args)
        self.assertEqual(return_code, SUCCESS)

        # Check that the pool exists
        pool = Pool(name)
        self.assertIsNotNone(pool)
        self.assertEqual(pool.name, name)

        # Remove and validate that it is gone
        self.assertTrue(await pool.flush())
        self.assertTrue(await pool.remove_persistence())
        self.assertFalse(await pool.exists())

    async def test_dummy_pool_remove(self):
        # Create a pool that can be removed by the CLI
        test_id = str(uuid.uuid4())
        pool_name = "dummy-remove-test-{}".format(test_id)
        remove_pool = Pool(pool_name)
        self.assertTrue(await remove_pool.touch())

        remove_pool_args = copy.deepcopy(self.base_args)
        remove_pool_args.extend(["remove", pool_name])

        return_code = execute_func_in_future(main, remove_pool_args)
        self.assertEqual(return_code, SUCCESS)

    @patch("sys.stdout", new_callable=StringIO)
    async def test_dummy_pool_list_empty(self, mock_stdout):
        list_pools_args = copy.deepcopy(self.base_args)
        list_pools_args.extend(["ls"])

        list_return_code = execute_func_in_future(main, list_pools_args)
        self.assertEqual(list_return_code, SUCCESS)
        list_output = mock_stdout.getvalue()
        self.assertListEqual(json.loads(list_output)["pools"], [])

    async def test_dummy_pool_create_multiple(self):
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
            create_pool_args.extend(["create", pool])

            return_code = execute_func_in_future(main, create_pool_args)
            self.assertEqual(return_code, SUCCESS)

        for pool in pools:
            # Check that the pool exists
            pool = Pool(pool)
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
            create_pool_args.extend(["create", pool])

            return_code = execute_func_in_future(main, create_pool_args)
            self.assertEqual(return_code, SUCCESS)

        for pool in pools:
            # Remove pools
            remove_pool_args = copy.deepcopy(self.base_args)
            remove_pool_args.extend(["remove", pool])

            return_code = execute_func_in_future(main, remove_pool_args)
            self.assertEqual(return_code, SUCCESS)
