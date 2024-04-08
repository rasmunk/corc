class Scheduler:
    def provision_storage(self, config):
        raise NotImplementedError

    def prepare(self, config):
        raise NotImplementedError

    def submit(self, task):
        raise NotImplementedError

    def list_scheduled(self):
        raise NotImplementedError

    def retrieve(self, job_id):
        raise NotImplementedError

    def remove(self, job_id):
        raise NotImplementedError
