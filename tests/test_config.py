import copy
import os
import unittest
from corc.config import (
    generate_default_config,
    save_config,
    load_config,
    remove_config,
    valid_config,
)
from corc.config import default_corc_config
from corc.providers.config import get_provider_profile, set_provider_profile
from corc.providers.oci.config import generate_oci_config, valid_oci_config


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
        self.config_path = os.path.join(self.test_dir, "config")

    def tearDown(self):
        self.assertTrue(remove_config(self.config_path))

    def test_generate_config(self):
        self.assertDictEqual(generate_default_config(), default_corc_config)

    def test_save_config(self):
        config = generate_default_config()
        self.assertTrue(save_config(config, path=self.config_path))

    def test_load_config(self):
        config = generate_default_config()
        self.assertTrue(save_config(config, path=self.config_path))
        loaded_config = load_config(self.config_path)
        self.assertIsInstance(loaded_config, dict)
        self.assertDictEqual(config, loaded_config)

    def test_valid_config(self):
        config = generate_default_config()
        local_copy = copy.deepcopy(config)
        self.assertTrue(valid_config(config, verbose=True))
        self.assertDictEqual(local_copy, config)

    def test_oci_config(self):
        config = generate_oci_config()
        local_copy = copy.deepcopy(config)
        self.assertTrue(valid_oci_config(config, verbose=True))
        self.assertDictEqual(local_copy, config)

    def test_provider_profile(self):
        provider = "oci"
        config = generate_default_config()
        save_config(config, path=self.config_path)

        profile = get_provider_profile(provider, config_path=self.config_path)
        self.assertDictEqual(profile, {})
        test_profile = {"name": "DEFAULT", "compartment_id": "test"}
        self.assertTrue(
            set_provider_profile(provider, test_profile, config_path=self.config_path)
        )
        profile = get_provider_profile(provider, config_path=self.config_path)
        self.assertDictEqual(profile, test_profile)
        self.assertTrue(valid_config(config))
        self.assertTrue(remove_config(path=self.config_path))
