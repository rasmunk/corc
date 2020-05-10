from kubernetes import client, config
from orchestration.scheduler import Scheduler
from orchestration.kubernetes.config import kube_config_loaded
from orchestration.kubernetes.job import create_job, prepare_job


class KubenetesScheduler(Scheduler):
    def __init__(self):
        loaded = kube_config_loaded()
        if not loaded:
            raise RuntimeError
        self.client = client.BatchV1Api()

        self.pending_jobs = []
        self.running_jobs = []
        self.finished_jobs = []

    def submit(self, task):
        if not task:
            return False

        job = prepare_job(task)
        if not job:
            return False

        # Ready to schedule
        job_created = create_job(self.scheduler_client, job)
        if not job_created:
            return False

        self.pending_jobs.append(job_created)
        return True

    def start(self):
        pass

    def stop(self):
        pass

    def retrieve(self, job_od):
        pass
