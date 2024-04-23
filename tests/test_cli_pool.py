import copy
import subprocess
import unittest
import uuid
from corc.core.orchestration.pool.models import Pool
from corc.core.orchestration.pool.remove_instance import remove_instance


class TestCliPool(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.name = "pool"
        self.base_args = ["corc", "orchestration", "pool"]

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
        create_pool_args = copy.deepcopy(self.base_args).extend(["create", self.name])
        result = subprocess.run(create_pool_args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

        # Check that the pool exists
        pool = Pool(self.name)
        self.assertIsNotNone(pool)
        self.assertEqual(pool.name, self.name)

        # Remove and validate that it is gone
        self.assertTrue(pool.flush())
        self.assertTrue(pool.remove_persistence())
        self.assertFalse(pool.exists())

    async def test_dummy_pool_remove(self):
        # Create a pool that can be removed by the CLI
        test_id = str(uuid.uuid4())
        pool_name = "dummy-remove-test-{}".format(test_id)
        remove_pool = Pool(pool_name)
        self.assertTrue(remove_pool.touch())

        remove_pool_args = copy.deepcopy(self.base_args).extend(["remove", self.name])
        result = subprocess.run(remove_pool_args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    async def test_dummy_pool_list(self):
        test_id = str(uuid.uuid4())
        list_pools = copy.deepcopy(self.base_args).extend(["list"])
        result = subprocess.run(list_pools, capture_output=True)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

        current_pools = dict(result.stdout)["pools"]
        self.assertListEqual(current_pools, [])

        # Add pools
        pool1, pool2, pool3 = (
            f"{test_id}-{self.name}-1",
            f"{test_id}-{self.name}-2",
            f"{test_id}-{self.name}-3",
        )
        pools = [pool1, pool2, pool3]
        for pool in pools:
            create_pool_args = copy.deepcopy(self.base_args).extend(["create", pool])
            result = subprocess.run(create_pool_args)
            self.assertIsNotNone(result)
            self.assertTrue(hasattr(result, "returncode"))
            self.assertEqual(result.returncode, 0)

        for pool in pools:
            # Check that the pool exists
            pool = Pool(pool)
            self.assertIsNotNone(pool)
            self.assertEqual(pool.name, self.name)

        for pool in pools:
            # Remove pools
            remove_pool_args = copy.deepcopy(self.base_args).extend(["remove", pool])
            result = subprocess.run(remove_pool_args)
            self.assertIsNotNone(result)
            self.assertTrue(hasattr(result, "returncode"))
            self.assertEqual(result.returncode, 0)

        # TODO, check that the pools are removed
