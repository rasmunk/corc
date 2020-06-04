class Orchestrator:

    options = None
    _is_ready = False
    _is_reachable = False

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

    def setup(self):
        raise NotImplementedError

    def tear_down(self):
        raise NotImplementedError

    @classmethod
    def validate_options(cls, options):
        raise NotImplementedError
