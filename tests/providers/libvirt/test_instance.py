import unittest
from corc.core.orchestration.defaults import LIBVIRT_PROVIDER, VIRTUAL_MACHINE
from corc.core.providers.types import get_orchestrator


class TestLibvirtInstanceOrchestrator(unittest.TestCase):
    def setUp(self):
        self.provider = "libvirt"
        test_name = "Test_Instance_Orch_Libvirt"
        node_name = test_name + "_Node"

        profile_options = dict(name="default")

        image = ""
        size = ""
        options = dict(
            provider=self.providFer,
            provider_kwargs=dict(profile=profile_options),
            kwargs=dict(instance=dict(name=node_name, image=image, size=size)),
        )

        self.options = options
        ApacheLibvirtOrchestrator, options = get_orchestrator(
            VIRTUAL_MACHINE, LIBVIRT_PROVIDER
        )
        self.options.update(options)

        ApacheLibvirtOrchestrator.validate_options(self.options)
        self.orchestrator = ApacheLibvirtOrchestrator(self.options)
        # Should not be ready at this point
        self.assertFalse(self.orchestrator.is_ready())

    def tearDown(self):
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator = None
        self.options = None

    def test_setup_instance(self):
        self.orchestrator.setup()
        self.assertTrue(self.orchestrator.is_ready())

    def test_teardown_instance(self):
        self.assertFalse(self.orchestrator.is_ready())
        self.orchestrator.tear_down()
        self.assertFalse(self.orchestrator.is_ready())


if __name__ == "__main__":
    unittest.main()
