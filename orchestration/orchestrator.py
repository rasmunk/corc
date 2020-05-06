class OCIOrchestrator:

    config = None
    is_ready = False

    def __init__(self, config):
        self.config = config

    def prepare(self):
        raise NotImplementedError

    def is_ready(self):
        return self.is_ready

    def schedule(self, task):
        raise NotImplementedError

    def tear_down(self):
        raise NotImplementedError

    @classmethod
    def validate_config(cls, config):
        raise NotImplementedError


class OCITask:

    is_ready = False
    is_scheduled = False
    is_completed = False
