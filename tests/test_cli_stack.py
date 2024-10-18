import unittest
import uuid
import copy
from corc.cli.return_codes import SUCCESS
from corc.cli.cli import main
from corc.core.defaults import STACK
from corc.utils.io import join
from corc.core.storage.dictdatabase import DictDatabase

# Because the main function spawns an event loop, we cannot execute the
# main function directly in the current event loop.
# Therefore we execute the function in a separate thread such
# that it will instantiate its own event loop
from tests.utils import execute_func_in_future


class TestCliStack(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.name = "dummy"
        self.base_args = ["orchestration", STACK]

    async def asyncTearDown(self):
        # Ensure that any pool is destroyed
        stack_db = DictDatabase(STACK)
        self.assertTrue(await stack_db.flush())
        self.assertEqual(len(await stack_db.items()), 0)
        self.assertTrue(await stack_db.remove_persistence())
        self.assertFalse(await stack_db.exists())

    async def test_dummy_stack_deploy(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"
        deploy_file = join("tests", "res", "test-stack.yml")
        create_stack_args = copy.deepcopy(self.base_args)
        create_stack_args.extend(["deploy", name, deploy_file])

        return_code = execute_func_in_future(main, create_stack_args)
        self.assertEqual(return_code, SUCCESS)

        # Check that the stack exists
        stack_db = DictDatabase(STACK)
        self.assertTrue(await stack_db.exists())
        stack = await stack_db.get(name)
        self.assertIsNotNone(stack)
        self.assertEqual(stack["name"], name)

        # Remove and validate that it is gone
        self.assertTrue(await stack_db.flush())
        self.assertTrue(await stack_db.remove_persistence())
        self.assertFalse(await stack_db.exists())

    async def test_dummy_stack_destroy(self):
        # Create a stack that can be removed by the CLI
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"
        stack_db = DictDatabase(STACK)
        self.assertTrue(await stack_db.touch())

        # Create stack instance to be removed
        deploy_file = join("tests", "res", "test-stack.yml")
        create_stack_args = copy.deepcopy(self.base_args)
        create_stack_args.extend(["deploy", name, deploy_file])

        return_code = execute_func_in_future(main, create_stack_args)
        self.assertEqual(return_code, SUCCESS)

        remove_stack_args = copy.deepcopy(self.base_args)
        remove_stack_args.extend(["destroy", name])

        return_code = execute_func_in_future(main, remove_stack_args)
        self.assertEqual(return_code, SUCCESS)

        # Check that the stack is empty
        self.assertTrue(await stack_db.is_empty())
