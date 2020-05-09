import os
import yaml
from kubernetes import client, config
from kubernetes.config import ConfigException
from kubernetes.config.kube_config import KUBE_CONFIG_DEFAULT_LOCATION

from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from oci.container_engine.models import CreateClusterKubeconfigContentDetails


from oci_helpers import create
from cluster import get_cluster_by_name, new_client


JOB_NAME = "pi"


def update_job(api_instance, job):
    # Update container image
    job.spec.template.spec.containers[0].image = "perl"
    api_response = api_instance.patch_namespaced_job(
        name=JOB_NAME, namespace="default", body=job
    )
    print("Job updated. status='%s'" % str(api_response.status))


def delete_job(api_instance):
    api_response = api_instance.delete_namespaced_job(
        name=JOB_NAME,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=5
        ),
    )
    print("Job deleted. status='%s'" % str(api_response.status))
