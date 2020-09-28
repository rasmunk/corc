import uuid
from corc.config import default_config_path
from corc.orchestrator import Orchestrator
from corc.util import ping


class LocalOrchestrator(Orchestrator):
    def __init__(self, options):
        super().__init__(options)
        self.instance = None
        self.resource_id = None

    def endpoint(self, select=None):
        return "127.0.0.1"

    def poll(self):
        target_endpoint = self.endpoint()
        if target_endpoint:
            if ping(target_endpoint):
                self._is_reachable = True

    def setup(self, resource_config=None):
        # Since it is local, it is already setup
        if not self.instance:
            self.instance = True

        if not self.resource_id:
            self.resource_id = str(uuid.uuid4())

        self._is_ready = True

    def get_resource(self):
        return self.resource_id, self.instance

    def tear_down(self):
        self._is_ready = False

    @classmethod
    def load_config_options(cls, provider="", path=default_config_path):
        return {}

    @classmethod
    def make_resource_config(cls, **kwargs):
        return {}

    @classmethod
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise TypeError("options is not a dictionary")
