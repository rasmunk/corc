import copy
import subprocess
import unittest
import uuid
import json
from corc.core.orchestration.pool.models import Pool
from corc.core.orchestration.pool.remove_instance import remove_instance


class TestCliPool(unittest.IsolatedAsyncioTestCase):

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

    async def asyncSetUp(self):
        self.name = "pool"
        self.base_args = ["corc", "orchestration", self.name]

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
        result = subprocess.run(create_pool_args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

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
        result = subprocess.run(remove_pool_args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    async def test_dummy_pool_list(self):
        test_id = str(uuid.uuid4())
        list_pools = copy.deepcopy(self.base_args)
        list_pools.extend(["ls"])
        result = subprocess.run(list_pools, capture_output=True)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)
        self.assertListEqual(json.loads(result.stdout)["pools"], [])

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
            result = subprocess.run(create_pool_args)
            self.assertIsNotNone(result)
            self.assertTrue(hasattr(result, "returncode"))
            self.assertEqual(result.returncode, 0)

        for pool in pools:
            # Check that the pool exists
            pool = Pool(pool)
            self.assertIsNotNone(pool)
            self.assertTrue(await pool.exists())

        for pool in pools:
            # Remove pools
            remove_pool_args = copy.deepcopy(self.base_args)
            remove_pool_args.extend(["remove", pool])
            result = subprocess.run(remove_pool_args)
            self.assertIsNotNone(result)
            self.assertTrue(hasattr(result, "returncode"))
            self.assertEqual(result.returncode, 0)

        # TODO, check that the pools are removed
        post_result = subprocess.run(list_pools, capture_output=True)
        self.assertIsNotNone(post_result)
        self.assertTrue(hasattr(post_result, "returncode"))
        self.assertEqual(post_result.returncode, 0)
        self.assertEqual(json.loads(post_result.stdout)["pools"], [])
