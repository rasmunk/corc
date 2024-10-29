import os
import unittest
from corc.core.orchestration.pool.models import Pool, Instance
from corc.core.orchestration.pool.add_instance import add_instance
from corc.core.orchestration.pool.remove_instance import remove_instance
from corc.utils.io import exists, makedirs, removedirs
from tests.common import TMP_TEST_PATH


TEST_NAME = os.path.basename(__file__).split(".")[0]
CURRENT_TEST_DIR = os.path.join(TMP_TEST_PATH, TEST_NAME)


class TestPool(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.name = "dummy"
        if not exists(CURRENT_TEST_DIR):
            self.assertTrue(makedirs(CURRENT_TEST_DIR))

    async def asyncTearDown(self):
        # Ensure that any pool is destroyed
        pool = Pool(self.name)
        for node in await pool.items():
            removed, response = await remove_instance(self.name, node.id)
            self.assertTrue(removed)
        self.assertTrue(await pool.flush())
        self.assertEqual(len(await pool.items()), 0)
        self.assertTrue(await pool.remove_persistence())

        if exists(CURRENT_TEST_DIR):
            self.assertTrue(removedirs(CURRENT_TEST_DIR, recursive=True))

    async def test_dummy_pool(self):
        pool = Pool(self.name, directory=CURRENT_TEST_DIR)
        self.assertIsNotNone(pool)
        self.assertEqual(pool.name, self.name)
        self.assertEqual(pool.directory, CURRENT_TEST_DIR)
        self.assertTrue(await pool.touch())
        self.assertTrue(await pool.exists())

        instance_name_1 = "dummy-test-name-1"
        instance_kwargs_1 = {
            "directory": CURRENT_TEST_DIR,
            "image": "dummy-image-1",
            "size": "dummy-size-1",
        }

        instance_name_2 = "dummy-test-name-2"
        instance_kwargs_2 = {
            "directory": CURRENT_TEST_DIR,
            "image": "dummy-image-2",
            "size": "dummy-size-2",
        }

        instance_name_3 = "dummy-test-name-3"
        instance_kwargs_3 = {
            "directory": CURRENT_TEST_DIR,
            "image": "dummy-image-3",
            "size": "dummy-size-3",
        }

        created1, response1 = await add_instance(
            self.name, instance_name_1, **instance_kwargs_1
        )
        self.assertTrue(created1)

        created2, response2 = await add_instance(
            self.name, instance_name_2, **instance_kwargs_2
        )
        self.assertTrue(created2)

        created3, response3 = await add_instance(
            self.name, instance_name_3, **instance_kwargs_3
        )
        self.assertTrue(created3)

        instances = sorted(await pool.items(), key=lambda instance: instance.name)
        self.assertEqual(len(instances), 3)

        for instance in instances:
            self.assertIsInstance(instance, Instance)

        self.assertEqual(instances[0].name, instance_name_1)
        self.assertEqual(instances[0].config["image"], instance_kwargs_1["image"])
        self.assertEqual(instances[0].config["size"], instance_kwargs_1["size"])

        self.assertEqual(instances[1].name, instance_name_2)
        self.assertEqual(instances[1].config["image"], instance_kwargs_2["image"])
        self.assertEqual(instances[1].config["size"], instance_kwargs_2["size"])

        self.assertEqual(instances[2].name, instance_name_3)
        self.assertEqual(instances[2].config["image"], instance_kwargs_3["image"])
        self.assertEqual(instances[2].config["size"], instance_kwargs_3["size"])

        self.assertTrue(await pool.remove(instances[0].id))
        self.assertTrue(await pool.remove(instances[1].id))
        self.assertTrue(await pool.remove(instances[2].id))
        self.assertEqual(len(await pool.items()), 0)
