from kubernetes import client
from corc.scheduler import Scheduler
from corc.kubernetes.config import load_kube_config
from corc.kubernetes.job import create_job, prepare_job
from corc.kubernetes.storage import (
    prepare_volume,
    prepare_secret,
    create_secret,
    create_volume,
)


class KubenetesScheduler(Scheduler):
    def __init__(self):
        loaded = load_kube_config()
        if not loaded:
            raise RuntimeError("Failed to load the kubernetes config")
        self.batch_client = client.BatchV1Api()
        self.core_client = client.CoreV1Api()

    def prepare(self, **config):
        if not config:
            return False

        if "secret_kwargs" in config:
            secret_prepared = prepare_secret(**config)
            if not secret_prepared:
                return False

            # create secret
            secret_created = create_secret(self.core_client, secret_prepared)
            if not secret_created:
                return False

        if "volume_kwargs" in config:
            volume_prepared = prepare_volume(**config)
            if not volume_prepared:
                return False

            volume_created = create_volume(self.core_client, volume_prepared)
            if not volume_created:
                return False

        return True

    def submit(self, **task):
        if not task:
            return False

        job = prepare_job(**task)
        if not job:
            return False

        # Schedule job on cluster
        job_created = create_job(self.batch_client, job)
        if not job_created:
            return False
        return True

    def retrieve(self, job_id):
        return self.jobs[job_id]
