from kubernetes import client
from orchestration.scheduler import Scheduler
from orchestration.kubernetes.config import load_kube_config
from orchestration.kubernetes.job import create_job, prepare_job
from orchestration.kubernetes.secret import prepare_secret
from orchestration.kubernetes.storage import prepare_volume


class KubenetesScheduler(Scheduler):
    def __init__(self):
        loaded = load_kube_config()
        if not loaded:
            raise RuntimeError("Failed to load the kubernetes config")
        self.client = client.BatchV1Api()

    def prepare(self, **config):
        if not config:
            return False

        secrets_prepared = prepare_secret(**config)
        if not secrets_prepared:
            return False

        volume_prepared = prepare_volume(**config)
        if not volume_prepared:
            return False

        return True

    def submit(self, **task):
        if not task:
            return False

        job = prepare_job(**task)
        if not job:
            return False

        # Schedule job on cluster
        job_created = create_job(self.client, job)
        if not job_created:
            return False
        return True

    def retrieve(self, job_id):
        return self.jobs[job_id]
