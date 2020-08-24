from kubernetes import client
from kubernetes.client.models import V1DeleteOptions
from corc.scheduler import Scheduler
from corc.schedulers.kubernetes.config import load_kube_config
from corc.schedulers.kubernetes.crud import request
from corc.schedulers.kubernetes.job import (
    create_job,
    prepare_job,
)
from corc.schedulers.kubernetes.storage import (
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
        self.namespace = "default"

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

        job = {}
        if "metadata" in job_created and "name" in job_created["metadata"]:
            job["id"] = job_created["metadata"]["name"]
        return job

    def list_scheduled(self):
        success, response = request(self.batch_client.list_job_for_all_namespaces)
        if not success:
            return None

        if hasattr(response, "items"):
            return [item.to_dict() for item in response.items]
        return []

    def retrieve(self, job_id):
        return self.submit[job_id]

    def remove(self, job_id):
        removed = False
        body = V1DeleteOptions()
        success, response = request(
            self.batch_client.delete_namespaced_job,
            job_id,
            self.namespace,
            body=body,
            catch=True,
        )
        if success:
            removed = True
        return removed
