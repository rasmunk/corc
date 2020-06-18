import os
import unittest
from corc.config.config import (
    generate_default_config,
    save_config,
    load_config,
    remove_config
)
from corc.config.defaults import default_config


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
        self.config_path = os.path.join(self.test_dir, "config")

    def tearDown(self):
        self.assertTrue(remove_config(self.config_path))

    def test_generate_config(self):
        self.assertDictEqual(generate_default_config(), default_config)

    def test_save_config(self):
        config = generate_default_config()
        self.assertTrue(save_config(config, path=self.config_path))

    def test_load_config(self):
        config = generate_default_config()
        self.assertTrue(save_config(config, path=self.config_path))
        loaded_config = load_config(self.config_path)
        self.assertIsInstance(loaded_config, dict)
        self.assertDictEqual(config, loaded_config)

    # def test_valid_config(self):
    #     config = generate_default_config()
    #     self.assertTrue(valid_config(config, verbose=True, throw=True))
