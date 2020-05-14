class Scheduler:
    def prepare(self, config):
        raise NotImplementedError

    def submit(self, task):
        raise NotImplementedError

    def retrieve(self, job_id):
        raise NotImplementedError
