import unittest
from corc.core.plugins.storage import install, remove, load


class TestPluginInstall(unittest.TestCase):
    def setUp(self):
        self.plugin_type = "orchestration"
        self.plugin_name = "libvirt_provider"

    def tearDown(self):
        self.assertTrue(remove(self.plugin_type, self.plugin_name))

    def test_install_libvirt(self):
        installed = install(self.plugin_type, self.plugin_name)
        self.assertTrue(installed)
        plugin = load(self.plugin_name)
        self.assertEqual(plugin.name, self.plugin_name)

    def test_remove_libvirt(self):
        removed = remove(self.plugin_type, self.plugin_name)
        self.assertTrue(removed)
        plugin = load(self.plugin_name)
        self.assertFalse(plugin)


if __name__ == "__main__":
    unittest.main()
