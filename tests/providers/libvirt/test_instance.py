import copy
import subprocess
import unittest
import uuid
import wget
from corc.utils.io import copy as copy_file
from corc.utils.io import remove, exists, makedirs, join


class TestCLILibvirtInstance(unittest.TestCase):

    def setUp(self):
        self.provider_name = "libvirt_provider"
        self.test_name = self.provider_name + "Test_CLI"
        test_id = uuid.uuid4()
        self.instance_name = "instance-{}".format(test_id)

        # Prepare test image disks
        self.architecture = "amd64"
        self.images_dir = join("tests", "images", self.architecture)
        if not exists(self.images_dir):
            self.assertTrue(makedirs(self.images_dir))

        self.image = join(self.images_dir, f"{self.test_name}.qcow2")
        if not exists(self.image):
            # Download the image
            url = f"https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-{self.architecture}.qcow2"
            try:
                print(f"Downloading image: {url} for testing")
                wget.download(url, self.image)
            except Exception as err:
                print(f"Failed to download image: {url} - {err}")
                self.assertFalse(True)
        self.assertTrue(exists(self.image))

        # Copy the image to the test directory
        self.test_instance_image = join(self.images_dir, f"{self.instance_name}.qcow2")
        self.assertTrue(copy_file(self.image, self.test_instance_image))

        # Install the CLI
        args = ["pip3", "install", ".", "-q"]
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

        self.base_args = ["corc", "orchestration", self.provider_name, "instance"]

    def tearDown(self):
        # Remove the test image
        if exists(self.test_instance_image):
            self.assertTrue(remove(self.test_instance_image))

    def test_cli_instance_create_libvirt(self):
        args = copy.deepcopy(self.base_args).extend(["create", self.instance_name])
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

        # Verify that the instance is created
        list_args = copy.deepcopy(self.base_args).extend(["list"])
        list_result = subprocess.run(list_args, capture_output=True)
        self.assertIsNotNone(list_result)
        self.assertTrue(hasattr(list_result, "returncode"))
        self.assertEqual(list_result.returncode, 0)
        self.assertIn(self.instance_name, str(list_result.stdout))

        remove_args = copy.deepcopy(self.base_args).extend(
            ["remove", self.instance_name]
        )
        remove_result = subprocess.run(remove_args)
        self.assertIsNotNone(remove_result)
        self.assertTrue(hasattr(remove_result, "returncode"))
        self.assertEqual(remove_result.returncode, 0)

    def test_cli_instance_remove_libvirt(self):
        args = copy.deepcopy(self.base_args).extend(["create", self.instance_name])
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

        args = copy.deepcopy(self.base_args).extend(["remove", self.instance_name])
        result = subprocess.run(args)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "returncode"))
        self.assertEqual(result.returncode, 0)

    def test_cli_instance_list_libvirt(self):
        test_instance_1 = "instance-{}".format(uuid.uuid4())
        test_instance_2 = "instance-{}".format(uuid.uuid4())
        test_instance_3 = "instance-{}".format(uuid.uuid4())

        create_args_1 = copy.deepcopy(self.base_args).extend(
            ["create", test_instance_1]
        )
        create_args_2 = copy.deepcopy(self.base_args).extend(
            ["create", test_instance_2]
        )
        create_args_3 = copy.deepcopy(self.base_args).extend(
            ["create", test_instance_3]
        )

        instance_args = [create_args_1, create_args_2, create_args_3]
        for instance_arg in instance_args:
            result = subprocess.run(instance_arg)
            self.assertIsNotNone(result)
            self.assertTrue(hasattr(result, "returncode"))
            self.assertEqual(result.returncode, 0)

        list_args = copy.deepcopy(self.base_args).extend(["list"])
        list_result = subprocess.run(list_args, capture_output=True)
        self.assertIsNotNone(list_result)
        self.assertTrue(hasattr(list_result, "returncode"))
        self.assertEqual(list_result.returncode, 0)
        self.assertIn(test_instance_1, str(list_result.stdout))

        remove_args_1 = copy.deepcopy(self.base_args).extend(
            ["remove", test_instance_1]
        )
        remove_args_2 = copy.deepcopy(self.base_args).extend(
            ["remove", test_instance_2]
        )
        remove_args_3 = copy.deepcopy(self.base_args).extend(
            ["remove", test_instance_3]
        )

        remove_args = [remove_args_1, remove_args_2, remove_args_3]
        for remove_arg in remove_args:
            result = subprocess.run(remove_arg)
            self.assertIsNotNone(result)
            self.assertTrue(hasattr(result, "returncode"))
            self.assertEqual(result.returncode, 0)
