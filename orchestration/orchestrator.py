class OCIOrchestrator:

    options = None
    _is_ready = False

    def __init__(self, options):
        self.options = options

    def is_ready(self):
        return self._is_ready

    def prepare(self):
        raise NotImplementedError

    def setup_scheduler(self):
        raise NotImplementedError

    def schedule(self, task):
        raise NotImplementedError

    def tear_down(self):
        raise NotImplementedError

    @classmethod
    def validate_options(cls, options):
        raise NotImplementedError


class OCITask:

    is_ready = False
    is_scheduled = False
    is_completed = False
