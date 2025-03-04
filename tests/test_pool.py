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
import unittest
from corc.core.defaults import POOL
from corc.core.storage.dictdatabase import DictDatabase
from corc.core.orchestration.pool.models import Instance
from corc.core.orchestration.pool.create import create
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
        pool_db = DictDatabase(POOL, directory=CURRENT_TEST_DIR)
        self.assertTrue(await pool_db.flush())
        self.assertEqual(len(await pool_db.items()), 0)
        self.assertTrue(await pool_db.remove_persistence())

        if exists(CURRENT_TEST_DIR):
            self.assertTrue(removedirs(CURRENT_TEST_DIR, recursive=True))

    async def test_create_dummy_pool_database(self):
        pool_db = DictDatabase(POOL, directory=CURRENT_TEST_DIR)
        self.assertIsNotNone(pool_db)
        self.assertEqual(pool_db.name, POOL)
        self.assertEqual(pool_db.directory, CURRENT_TEST_DIR)
        self.assertFalse(await pool_db.exists())
        self.assertTrue(await pool_db.touch())
        self.assertTrue(await pool_db.exists())
        self.assertTrue(await pool_db.is_empty())

    async def test_create_dummy_pool(self):
        pool_db = DictDatabase(POOL, directory=CURRENT_TEST_DIR)
        self.assertTrue(await pool_db.touch())
        created_pool, created_response = await create(
            self.name, directory=CURRENT_TEST_DIR
        )
        self.assertTrue(created_pool)
        self.assertTrue(created_response)
        self.assertIn(self.name, await pool_db.keys())
        self.assertIsNotNone(await pool_db.get(self.name))

    async def test_dummy_pool(self):
        pool_db = DictDatabase(POOL, directory=CURRENT_TEST_DIR)
        self.assertTrue(await pool_db.touch())

        created_pool, created_response = await create(
            self.name, directory=CURRENT_TEST_DIR
        )
        self.assertTrue(created_pool)

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

        updated_pool = await pool_db.get(self.name)
        self.assertIn("instances", updated_pool)
        instances = sorted(
            updated_pool["instances"], key=lambda instance: instance.name
        )
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

        removed1, response1 = await remove_instance(
            self.name, instances[0].name, directory=CURRENT_TEST_DIR
        )
        self.assertTrue(removed1)
        removed2, response2 = await remove_instance(
            self.name, instances[1].name, directory=CURRENT_TEST_DIR
        )
        self.assertTrue(removed2)
        removed3, response3 = await remove_instance(
            self.name, instances[2].name, directory=CURRENT_TEST_DIR
        )
        self.assertTrue(removed3)

        new_pool_state = await pool_db.get(self.name)
        self.assertIn("instances", new_pool_state)
        self.assertEqual(len(new_pool_state["instances"]), 0)
