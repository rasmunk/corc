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


def create_job_object():
    # Configureate Pod template container
    container = client.V1Container(
        name="pi",
        image="perl",
        command=["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"],
    )
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "pi"}),
        spec=client.V1PodSpec(restart_policy="Never", containers=[container]),
    )
    # Create the specification of deployment
    spec = client.V1JobSpec(template=template, backoff_limit=4)
    # Instantiate the job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=JOB_NAME),
        spec=spec,
    )
    return job


def create_job(api_instance, job):
    api_response = api_instance.create_namespaced_job(body=job, namespace="default")
    print("Job created. status='%s'" % str(api_response.status))


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


def load_kube_config():
    try:
        config.load_kube_config()
        return True
    except (ConfigException, TypeError) as err:
        print("Failed to load kube config: {}".format(err))
    return False


def parse_yaml(data):
    try:
        parsed = yaml.safe_load(data)
        return parsed
    except yaml.reader.ReaderError as err:
        print("Failed to parse yaml: {}".format(err))
    return False


def save_kube_config(config_dict, config_file=None, user_exec_args=None):
    if not isinstance(config_dict, dict):
        return False

    if config_file is None:
        # Get the absolute path
        config_file = os.path.expanduser(KUBE_CONFIG_DEFAULT_LOCATION)
    with open(config_file, "w") as fh:
        yaml.dump(config_dict, fh)
    return True


def main():
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.

    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        profile_name="XNOVOTECH",
    )

    comp_id = "ocid1.tenancy.oc1..aaaaaaaakfmksyrf7hl2gfexmjpb6pbyrirm6k3ro7wd464y2pr7atpxpv4q"
    cluster_name = "XNOVOTECH Cluster"
    profile_name = "XNOVOTECH"

    loaded = load_kube_config()
    if not loaded:
        # Try to generate a new config
        cluster = get_cluster_by_name(
            container_engine_client, comp_id, name=cluster_name
        )
        kube_config = create(container_engine_client, "create_kubeconfig", cluster.id)
        if kube_config and hasattr(kube_config, "text"):
            config_dict = parse_yaml(kube_config.text)
            # HACK, add profile to user args
            if profile_name:
                profile_args = ["--profile", profile_name]
                config_dict["users"][0]["user"]["exec"]["args"].extend(profile_args)
            if save_kube_config(config_dict):
                loaded = load_kube_config()

    if not loaded:
        print("Could not find a valid config")
        exit(1)

    batch_v1 = client.BatchV1Api()
    # Create a job object with client-python API. The job we
    # created is same as the `pi-job.yaml` in the /examples folder.
    job = create_job_object()
    create_job(batch_v1, job)
    # update_job(batch_v1, job)
    # delete_job(batch_v1)


if __name__ == "__main__":
    main()
