class Scheduler:
    def submit(self, task):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def retrieve(self, job_id):
        raise NotImplementedError
