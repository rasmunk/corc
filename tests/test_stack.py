import unittest
from corc.core.orchestration.stack.models import Stack
from corc.core.orchestration.pool.models import Pool, Instance
from corc.core.orchestration.pool.add_instance import add_instance
from corc.core.orchestration.pool.remove_instance import remove_instance


class TestStack(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.name = "dummy"

    async def asyncTearDown(self):
        # Ensure that any pool is destroyed
        pool = Pool(self.name)
        for node in await pool.items():
            removed, response = await remove_instance(self.name, node.id)
            self.assertTrue(removed)
        self.assertTrue(await pool.flush())
        self.assertEqual(len(await pool.items()), 0)
        self.assertTrue(await pool.remove_persistence())
