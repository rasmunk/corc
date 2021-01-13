class Orchestrator:

    options = None
    _is_ready = False
    _is_reachable = False
    _resource_id = None

    def __init__(self, options):
        self.options = options

    def is_ready(self):
        return self._is_ready

    def is_reachable(self):
        return self._is_reachable

    def endpoint(self, select=None):
        raise NotImplementedError

    def poll(self):
        raise NotImplementedError

    def setup(self, resource_config=None, credentials=None):
        raise NotImplementedError

    def resource_id(self):
        return self._resource_id

    def get_resource(self):
        raise NotImplementedError

    def tear_down(self):
        raise NotImplementedError

    @classmethod
    def adapt_options(cls, **kwargs):
        """Used to adapt the orchestrators options if required
        before they are passed to the validate_options"""
        return {}

    @classmethod
    def load_config_options(cls, provider="", path=None):
        raise NotImplementedError

    @classmethod
    def make_resource_config(cls, **kwargs):
        raise NotImplementedError

    @classmethod
    def make_credentials(cls, **kwargs):
        raise NotImplementedError

    @classmethod
    def validate_options(cls, options):
        raise NotImplementedError
