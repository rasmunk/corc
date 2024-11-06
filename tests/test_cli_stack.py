import os
import unittest
import uuid
import copy
from corc.cli.return_codes import SUCCESS, FAILURE
from corc.cli.cli import main
from corc.core.defaults import STACK
from corc.utils.io import join, exists, makedirs, removedirs
from corc.core.storage.dictdatabase import DictDatabase

# Because the main function spawns an event loop, we cannot execute the
# main function directly in the current event loop.
# Therefore we execute the function in a separate thread such
# that it will instantiate its own event loop
from tests.utils import execute_func_in_future
from tests.common import TMP_TEST_PATH, TEST_RES_DIR

TEST_NAME = os.path.basename(__file__).split(".")[0]
CURRENT_TEST_DIR = join(TMP_TEST_PATH, TEST_NAME)

TEST_BASIC_STACK_FILE = os.path.join(TEST_RES_DIR, "basic-stack.yml")
TEST_ADVANCED_STACK_FILE = os.path.join(TEST_RES_DIR, "advanced-stack.yml")

TEST_BASIC_EXPECTED_POOLS = {"pool01": {"instances": ["instance01"]}}
TEST_BASIC_INSTANCES_EXPECTED = {
    "instance01": {
        "provider": {
            "name": "dummy_provider",
            "driver": "dummy",
        },
        "settings": {
            "args": [
                "instance01",
                "/path/to/predefined/image/file/instance01.qcow2",
            ],
            "kwargs": {"memory_size": "1024mib", "num_vcpus": 1},
        },
    }
}


class TestCliStack(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.name = "dummy"
        self.base_args = [STACK]
        if not exists(CURRENT_TEST_DIR):
            self.assertTrue(makedirs(CURRENT_TEST_DIR))

    async def asyncTearDown(self):
        # Ensure that any pool is destroyed
        stack_db = DictDatabase(STACK, directory=CURRENT_TEST_DIR)
        self.assertTrue(await stack_db.flush())
        self.assertEqual(len(await stack_db.items()), 0)
        self.assertTrue(await stack_db.remove_persistence())
        self.assertFalse(await stack_db.exists())

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

    async def test_dummy_stack_create(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"

        create_stack_args = copy.deepcopy(self.base_args)
        create_stack_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])

        # Create the stack
        return_code = execute_func_in_future(main, create_stack_args)
        self.assertEqual(return_code, SUCCESS)

        # Check that the stack exists
        stack_db = DictDatabase(name, directory=CURRENT_TEST_DIR)
        self.assertTrue(await stack_db.exists())

        stack = await stack_db.get(name)
        self.assertIsNotNone(stack)
        self.assertIsInstance(stack, dict)

        # Validate each expected key and default value
        self.assertIn("id", stack)
        self.assertEqual(stack["id"], name)

        self.assertIn("config", stack)
        self.assertIsInstance(stack["config"], dict)
        self.assertDictEqual(stack["config"], {})

        self.assertIn("instances", stack)
        self.assertIsInstance(stack["instances"], dict)
        self.assertDictEqual(stack["instances"], {})

        self.assertIn("pools", stack)
        self.assertIsInstance(stack["pools"], dict)
        self.assertDictEqual(stack["pools"], {})

    async def test_dummy_stack_create_with_config_file(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"

        create_stack_args = copy.deepcopy(self.base_args)
        create_stack_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])
        create_stack_args.extend(["--config-file", TEST_BASIC_STACK_FILE])

        # Create the stack
        return_code = execute_func_in_future(main, create_stack_args)
        self.assertEqual(return_code, SUCCESS)

        # Check that the stack exists
        stack_db = DictDatabase(name, directory=CURRENT_TEST_DIR)
        self.assertTrue(await stack_db.exists())

        stack = await stack_db.get(name)
        self.assertIsNotNone(stack)
        self.assertEqual(stack["id"], name)

        self.assertIn("config", stack)
        self.assertIn("pools", stack["config"])
        self.assertEqual(stack["config"]["pools"], TEST_BASIC_EXPECTED_POOLS)

        self.assertIn("instances", stack["config"])
        self.assertEqual(stack["config"]["instances"], TEST_BASIC_INSTANCES_EXPECTED)

    async def test_dummy_stack_update(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"

        create_stack_args = copy.deepcopy(self.base_args)
        create_stack_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])

        # Create the stack
        create_return_code = execute_func_in_future(main, create_stack_args)
        self.assertEqual(create_return_code, SUCCESS)

        # Update the stack
        update_stack_args = copy.deepcopy(self.base_args)
        update_stack_args.extend(["update", name, "--directory", CURRENT_TEST_DIR])
        update_stack_args.extend(["--config-file", TEST_BASIC_STACK_FILE])
        update_return_code = execute_func_in_future(main, update_stack_args)
        self.assertEqual(update_return_code, SUCCESS)

        # Check that the stack exists
        stack_db = DictDatabase(name, directory=CURRENT_TEST_DIR)
        self.assertTrue(await stack_db.exists())

        stack = await stack_db.get(name)
        self.assertIsNotNone(stack)

        self.assertIn("config", stack)
        self.assertIn("pools", stack["config"])
        self.assertEqual(stack["config"]["pools"], TEST_BASIC_EXPECTED_POOLS)

        self.assertIn("instances", stack["config"])
        self.assertEqual(stack["config"]["instances"], TEST_BASIC_INSTANCES_EXPECTED)

    async def test_dummy_stack_remove(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"

        # Create stack instance to be removed
        create_stack_args = copy.deepcopy(self.base_args)
        create_stack_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])
        return_code = execute_func_in_future(main, create_stack_args)
        self.assertEqual(return_code, SUCCESS)

        remove_stack_args = copy.deepcopy(self.base_args)
        remove_stack_args.extend(["remove", name, "--directory", CURRENT_TEST_DIR])
        return_code = execute_func_in_future(main, remove_stack_args)
        self.assertEqual(return_code, SUCCESS)

        # Verify that the stack is removed
        show_stack_args = copy.deepcopy(self.base_args)
        show_stack_args.extend(["show", name, "--directory", CURRENT_TEST_DIR])
        show_return_code = execute_func_in_future(main, show_stack_args)
        self.assertEqual(show_return_code, FAILURE)

    async def test_dummy_stack_ls(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"

        create_stack_args = copy.deepcopy(self.base_args)
        create_stack_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])

        # Create the stack
        create_return_code = execute_func_in_future(main, create_stack_args)
        self.assertEqual(create_return_code, SUCCESS)

        # Check that the stack exists
        ls_stack_args = copy.deepcopy(self.base_args)
        ls_stack_args.extend(["ls", "--directory", CURRENT_TEST_DIR])

        ls_return_code = execute_func_in_future(main, ls_stack_args)
        self.assertEqual(ls_return_code, SUCCESS)
        # TODO, validate the output aswell

    async def test_dummy_stack_deploy(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"

        create_stack_args = copy.deepcopy(self.base_args)
        create_stack_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])
        create_stack_args.extend(["--config-file", TEST_BASIC_STACK_FILE])

        return_code = execute_func_in_future(main, create_stack_args)
        self.assertEqual(return_code, SUCCESS)

        # Check that the stack exists
        stack_db = DictDatabase(name, directory=CURRENT_TEST_DIR)
        self.assertTrue(await stack_db.exists())

        stack = await stack_db.get(name)
        self.assertIsNotNone(stack)
        self.assertEqual(stack["id"], name)
        self.assertEqual(stack["config"]["pools"], TEST_BASIC_EXPECTED_POOLS)
        self.assertEqual(stack["config"]["instances"], TEST_BASIC_INSTANCES_EXPECTED)

        deploy_stack_args = copy.deepcopy(self.base_args)
        deploy_stack_args.extend(["deploy", name, "--directory", CURRENT_TEST_DIR])

        # deploy_return_code = execute_func_in_future(main, deploy_stack_args)
        # self.assertEqual(deploy_return_code, SUCCESS)

        # deployed_stack = await stack_db.get(name)
        # self.assertIsNotNone(deployed_stack)
        # self.assertEqual(deployed_stack["id"], name)
        # self.assertEqual(deployed_stack["pools"], deployed_stack["config"]["pools"])
        # self.assertEqual(
        #     deployed_stack["instances"], deployed_stack["config"]["instances"]
        # )

    async def test_dummy_stack_destroy(self):
        # Create a stack that can be removed by the CLI
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"

        create_stack_args = copy.deepcopy(self.base_args)
        create_stack_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])
        create_stack_args.extend(["--config-file", TEST_BASIC_STACK_FILE])

        create_return_code = execute_func_in_future(main, create_stack_args)
        self.assertEqual(create_return_code, SUCCESS)

        # Check that the stack is created and is correctly configured
        stack_db = DictDatabase(name, directory=CURRENT_TEST_DIR)
        self.assertTrue(await stack_db.exists())
        stack = await stack_db.get(name)
        self.assertIsNotNone(stack)
        self.assertEqual(stack["id"], name)

        # Create stack instance to be removed
        deploy_stack_args = copy.deepcopy(self.base_args)
        deploy_stack_args.extend(["deploy", name, "--directory", CURRENT_TEST_DIR])

        deploy_return_code = execute_func_in_future(main, deploy_stack_args)
        self.assertEqual(deploy_return_code, SUCCESS)

        remove_stack_args = copy.deepcopy(self.base_args)
        remove_stack_args.extend(["destroy", name, "--directory", CURRENT_TEST_DIR])

        remove_return_code = execute_func_in_future(main, remove_stack_args)
        self.assertEqual(remove_return_code, SUCCESS)

    async def test_dummy_stack_show(self):
        test_id = str(uuid.uuid4())
        name = f"{self.name}-{test_id}"

        create_stack_args = copy.deepcopy(self.base_args)
        create_stack_args.extend(["create", name, "--directory", CURRENT_TEST_DIR])

        # Create the stack
        return_code = execute_func_in_future(main, create_stack_args)
        self.assertEqual(return_code, SUCCESS)

        # Check that the stack exists
        stack_db = DictDatabase(name, directory=CURRENT_TEST_DIR)
        self.assertTrue(await stack_db.exists())

        show_stack_args = copy.deepcopy(self.base_args)
        show_stack_args.extend(["show", name, "--directory", CURRENT_TEST_DIR])

        show_return_code = execute_func_in_future(main, show_stack_args)
        self.assertEqual(show_return_code, SUCCESS)
        # TODO, validate the output aswell
