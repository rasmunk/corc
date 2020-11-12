import boto3
import os
import time
from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from kubernetes import client
from kubernetes.client import (
    V1Volume,
    V1SecretVolumeSource,
    V1VolumeMount,
    V1ObjectMeta,
)
from kubernetes.client.rest import ApiException

from jobio.storage.s3 import expand_s3_bucket, stage_s3_resource
from corc.config import (
    valid_job_config,
    valid_storage_config,
    valid_s3_config,
)
from corc.defaults import (
    STORAGE_CREDENTIALS_NAME,
    KUBERNETES_NAMESPACE,
    JOB_DEFAULT_NAME,
)
from corc.util import validate_dict_fields, validate_dict_values, validate_either_values
from corc.helpers import load_aws_config
from corc.storage.s3 import (
    bucket_exists,
    delete_bucket,
    delete_objects,
    list_objects,
    required_s3_fields,
    upload_to_s3,
    upload_directory_to_s3,
)
from corc.schedulers.kubernetes.nodes import NodeManager
from corc.schedulers.kubernetes.scheduler import KubenetesScheduler
from corc.providers.oci.cluster import get_cluster_by_name, refresh_kube_config
from corc.providers.oci.helpers import new_client
from corc.providers.oci.config import valid_profile_config, valid_cluster_config


required_run_cluster_fields = {"name": str, "image": str}

required_run_job_fields = {
    "meta": {"num_jobs": int, "num_parallel": int},
    "commands": list,
}

required_storage_fields = {
    "enable": True,
    "endpoint": True,
    "credentials_path": True,
    "input_path": True,
    "output_path": True,
}

required_staging_values = {
    "config_file": True,
    "credentials_file": True,
    "name": True,
    "bucket_name": True,
    "bucket_input_prefix": True,
    "bucket_output_prefix": True,
}


def _validate_fields(provider=None, cluster=None, job=None, storage=None, s3=None):
    if provider:
        validate_dict_fields(
            provider["profile"], valid_profile_config, verbose=True, throw=True
        )

    if cluster:
        validate_dict_fields(cluster, valid_cluster_config, verbose=True, throw=True)

    if job:
        validate_dict_fields(job, valid_job_config, verbose=True, throw=True)

    if storage:
        validate_dict_fields(storage, valid_storage_config, verbose=True, throw=True)

    if s3:
        validate_dict_fields(s3, valid_s3_config, verbose=True, throw=True)


def _required_run_arguments(provider_kwargs, cluster, job, storage, s3):
    validate_dict_values(
        provider_kwargs["profile"], valid_profile_config, verbose=True, throw=True
    )
    validate_dict_values(cluster, required_run_cluster_fields, verbose=True, throw=True)
    validate_dict_values(job, required_run_job_fields, verbose=True, throw=True)
    # Storage and Staging are not required to execute a job, only if enabled


def run(provider_kwargs, cluster={}, job={}, storage={}):
    # TODO, temp fix
    s3 = storage["s3"]
    _validate_fields(
        provider=provider_kwargs, cluster=cluster, job=job, storage=storage, s3=s3
    )
    _required_run_arguments(provider_kwargs, cluster, job, storage, s3)

    response = {"job": {}}
    if "name" not in job["meta"] or not job["meta"]["name"]:
        since_epoch = int(time.time())
        job["meta"]["name"] = "{}-{}".format(JOB_DEFAULT_NAME, since_epoch)

    if "bucket_name" not in s3 or not s3["bucket_name"]:
        s3["bucket_name"] = job["meta"]["name"]

    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        name=provider_kwargs["profile"]["name"],
    )

    compute_cluster = get_cluster_by_name(
        container_engine_client,
        provider_kwargs["profile"]["compartment_id"],
        name=cluster["name"],
    )

    if not compute_cluster:
        response["msg"] = "Failed to find a cluster with name: {}".format(
            cluster["name"]
        )
        return False, response

    refreshed = refresh_kube_config(
        compute_cluster.id, name=provider_kwargs["profile"]["name"]
    )
    if not refreshed:
        response["msg"] = "Failed to refresh the kubernetes config"
        return False, response

    node_manager = NodeManager()
    if not node_manager.discover():
        response["msg"] = "Failed to discover any nodes to schedule jobs on"
        return False, response

    node = node_manager.select()
    if not node:
        response["msg"] = "Failed to select a node to schedule on"
        return False, response

    # Ensure we have the newest config
    scheduler = KubenetesScheduler()

    jobio_args = [
        "jobio",
        "run",
    ]
    jobio_args.extend(job["commands"])
    jobio_args.extend(["--job-meta-name", job["meta"]["name"]])

    if "output_path" in job:
        jobio_args.extend(
            ["--job-output-path", job["output_path"],]
        )

    if "capture" in job and job["capture"]:
        jobio_args.append("--job-capture")

    if "debug" in job["meta"]:
        jobio_args.append("--job-meta-debug")

    if "env_override" in job["meta"]:
        jobio_args.append("--job-meta-env-override")

    # Maintained by the pod
    volumes = []
    # Maintained by the container
    volume_mounts = []
    # Environment to pass to the container
    envs = []

    # Prepare config for the scheduler
    scheduler_config = {}

    if storage and storage["enable"]:
        validate_dict_values(storage, required_storage_fields, throw=True)
        jobio_args.append("--storage-enable")

        # Means that results should be exported to the specified storage
        # Create kubernetes secrets
        core_api = client.CoreV1Api()
        # storage_api = client.StorageV1Api()

        # Storage endpoint credentials secret (Tied to a profile and job)
        secret_profile_name = "{}-{}-{}".format(
            STORAGE_CREDENTIALS_NAME, s3["name"], job["meta"]["name"]
        )
        try:
            storage_credentials_secret = core_api.read_namespaced_secret(
                secret_profile_name, KUBERNETES_NAMESPACE
            )
        except ApiException:
            storage_credentials_secret = None

        # volumes
        secret_volume_source = V1SecretVolumeSource(secret_name=secret_profile_name)
        secret_volume = V1Volume(name=secret_profile_name, secret=secret_volume_source)
        volumes.append(secret_volume)

        # Where the storage credentials should be mounted
        # in the compute unit
        secret_mount = V1VolumeMount(
            name=secret_profile_name,
            mount_path=storage["credentials_path"],
            read_only=True,
        )
        volume_mounts.append(secret_mount)

        if s3:
            validate_dict_values(s3, required_staging_values, verbose=True, throw=True)
            jobio_args.append("--storage-s3")
            # S3 storage
            # Look for s3 credentials and config files
            s3_config = load_aws_config(
                s3["config_file"],
                credentials_file=s3["credentials_file"],
                name=s3["name"],
            )
            s3_config["endpoint_url"] = storage["endpoint"]

            if not storage_credentials_secret:
                secret_data = dict(
                    aws_access_key_id=s3_config["aws_access_key_id"],
                    aws_secret_access_key=s3_config["aws_secret_access_key"],
                )
                secret_metadata = V1ObjectMeta(name=secret_profile_name)
                secrets_config = dict(metadata=secret_metadata, string_data=secret_data)
                scheduler_config.update(dict(secret_kwargs=secrets_config))

            # If `access_key`
            # TODO, unify argument endpoint, with s3 config endpoint'
            s3_resource = boto3.resource("s3", **s3_config)

            bucket = bucket_exists(s3_resource.meta.client, s3["bucket_name"])
            if not bucket:
                bucket = s3_resource.create_bucket(
                    Bucket=s3["bucket_name"],
                    CreateBucketConfiguration={
                        "LocationConstraint": s3_config["region_name"]
                    },
                )

            if "upload_path" in storage and storage["upload_path"]:
                # Upload local path to the bucket as designated input for the job
                uploaded = None
                if os.path.exists(storage["upload_path"]):
                    if os.path.isdir(storage["upload_path"]):
                        uploaded = upload_directory_to_s3(
                            s3_resource.meta.client,
                            storage["upload_path"],
                            s3["bucket_name"],
                            s3_prefix=s3["bucket_input_prefix"],
                        )
                    elif os.path.isfile(storage["upload_path"]):
                        s3_path = os.path.basename(storage["upload_path"])
                        if s3["bucket_input_prefix"]:
                            s3_path = os.path.join(s3["bucket_input_prefix"], s3_path)
                        # Upload
                        uploaded = upload_to_s3(
                            s3_resource.meta.client,
                            storage["upload_path"],
                            s3_path,
                            s3["bucket_name"],
                        )

                if not uploaded:
                    response[
                        "msg"
                    ] = "Failed to local path: {} in the upload folder to s3".format(
                        storage["upload_path"]
                    )
                    return False, response

            jobio_args.extend(
                [
                    "--s3-region-name",
                    s3_config["region_name"],
                    "--storage-secrets-dir",
                    storage["credentials_path"],
                    "--storage-endpoint",
                    storage["endpoint"],
                    "--storage-input-path",
                    storage["input_path"],
                    "--storage-output-path",
                    storage["output_path"],
                    "--bucket-name",
                    s3["bucket_name"],
                    "--bucket-input-prefix",
                    s3["bucket_input_prefix"],
                    "--bucket-output-prefix",
                    s3["bucket_output_prefix"],
                ]
            )

            # Provide a way to allow pod specific output prefixes
            field_ref = client.V1ObjectFieldSelector(field_path="metadata.name")
            env_var_source = client.V1EnvVarSource(field_ref=field_ref)
            # HACK, Set the output prefix in the bucket to the name of the pod
            env_output_prefix = client.V1EnvVar(
                name="JOBIO_BUCKET_OUTPUT_PREFIX", value_from=env_var_source
            )
            envs.append(env_output_prefix)

    if scheduler_config:
        prepared = scheduler.prepare(**scheduler_config)
        if not prepared:
            response["msg"] = "Failed to prepare the scheduler"
            return False, response

    container_spec = dict(
        name=job["meta"]["name"],
        image=cluster["image"],
        env=envs,
        args=jobio_args,
        volume_mounts=volume_mounts,
    )

    # If the working directory does not exist inside the container
    # It will set permissions where it will be unable to expand the
    # s3 bucket if the user doesn't have root permissions
    if "working_dir" in job:
        container_spec.update({"working_dir": job["working_dir"]})

    # args=jobio_args,
    pod_spec = dict(node_name=node.metadata.name, volumes=volumes, dns_policy="Default")

    job_spec = dict(
        backoff_limit=2,
        parallelism=job["meta"]["num_parallel"],
        completions=job["meta"]["num_jobs"],
    )

    task = dict(
        container_kwargs=container_spec,
        pod_spec_kwargs=pod_spec,
        job_spec_kwargs=job_spec,
    )

    job = scheduler.submit(**task)
    if not job:
        response["msg"] = "Failed to submit the job"
        return False, response

    response["job"] = job
    response["msg"] = "Job submitted"
    return True, response


def _required_delete_job_arguments(cluster, job):

    required_cluster_fields = {"name": str}
    validate_dict_values(cluster, required_cluster_fields, verbose=True, throw=True)

    required_job_fields = {"meta": dict}
    validate_dict_values(job, required_job_fields, verbose=True, throw=True)

    either_meta_fields = {"name": str, "all": str}
    validate_either_values(job["meta"], either_meta_fields, verbose=True, throw=True)


def delete_job(provider_kwargs, cluster={}, job={}):
    _validate_fields(provider=provider_kwargs, job=job, cluster=cluster)
    _required_delete_job_arguments(cluster, job)

    response = {}
    # Ensure we have the newest config
    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        name=provider_kwargs["profile"]["name"],
    )

    compute_cluster = get_cluster_by_name(
        container_engine_client,
        provider_kwargs["profile"]["compartment_id"],
        name=cluster["name"],
    )

    if not compute_cluster:
        response["msg"] = "Failed to find a cluster with name: {}".format(
            cluster["name"]
        )
        return False, response

    refreshed = refresh_kube_config(
        compute_cluster.id, name=provider_kwargs["profile"]["name"]
    )
    if not refreshed:
        response["msg"] = "Failed to refresh the kubernetes config"
        return False, response

    scheduler = KubenetesScheduler()

    if "name" in job["meta"] and job["meta"]["name"]:
        removed = scheduler.remove(job["meta"]["name"])
        if removed:
            response["msg"] = "Removed: {}".format(job["meta"]["name"])
            return True, response

        response["msg"] = "Failed to remove: {}".format(job["meta"]["name"])
        return False, response

    if "all" in job["meta"] and job["meta"]["all"]:
        jobs = scheduler.list_scheduled()

        if not jobs:
            response["msg"] = "Failed to retrieve scheduled jobs"
            return False, response

        failed = []
        # Kubernetes jobs
        for job in jobs:
            removed = scheduler.remove(job["metadata"]["name"])
            if not removed:
                failed.append(job)

        if failed:
            response["msg"] = "Failed to remove: {}".format(
                [job["metadata"]["name"] for job in jobs]
            )
            return False, response

        response["msg"] = "Removed all jobs"
        return True, response

    response["msg"] = "Neither a single name or all jobs were specified to be removed"
    return False, response


def list_job():
    response = {}
    # Ensure we have the newest config
    scheduler = KubenetesScheduler()
    jobs = scheduler.list_scheduled()
    if not isinstance(jobs, list):
        response["msg"] = "Failed to retrieve scheduled jobs"
        return False, response

    response["jobs"] = jobs
    return True, response


def _required_get_result_arguments(job, storage, s3):

    required_job_fields = {"meta": dict}
    validate_dict_values(job, required_job_fields, verbose=True, throw=True)

    required_meta_fields = {"name": str}
    validate_dict_values(job["meta"], required_meta_fields, verbose=True, throw=True)

    required_storage_fields = {"endpoint": str}
    validate_dict_values(storage, required_storage_fields, verbose=True, throw=True)
    validate_dict_values(s3, required_s3_fields, verbose=True, throw=True)


def get_results(job={}, storage={}):
    # TODO, temp fix
    s3 = storage["s3"]
    _validate_fields(job=job, storage=storage, s3=s3)
    _required_get_result_arguments(job, storage, s3)

    response = {"id": job["meta"]["name"]}

    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_aws_config(
        s3["config_file"], s3["credentials_file"], name=s3["name"],
    )
    s3_config["endpoint_url"] = storage["endpoint"]

    # Download results from s3
    s3_resource = stage_s3_resource(**s3_config)

    # Whether to expand all or a single result
    if "result_prefix" in job and job["result_prefix"]:
        result_prefix = job["result_prefix"]
    else:
        # Use all
        result_prefix = ""

    bucket = bucket_exists(s3_resource.meta.client, job["meta"]["name"])
    if not bucket:
        response["msg"] = "Could not find a bucket with the name: {}".format(
            job["meta"]["name"]
        )
        return (False, response)

    expanded = expand_s3_bucket(
        s3_resource,
        job["meta"]["name"],
        storage["download_path"],
        s3_prefix=result_prefix,
    )

    if not expanded:
        response["msg"] = "Failed to expand the target bucket: {}".format(
            job["meta"]["name"]
        )

    response["path"] = storage["download_path"]
    response["msg"] = "Downloaded results"
    return (True, response)


def _required_delete_result_arguments(job, storage, s3):

    required_job_fields = {"meta": dict}
    validate_dict_values(job, required_job_fields, verbose=True, throw=True)

    required_meta_fields = {"name": str}
    validate_dict_values(job["meta"], required_meta_fields, verbose=True, throw=True)

    required_storage_fields = {
        "endpoint": str,
    }
    validate_dict_values(storage, required_storage_fields, verbose=True, throw=True)
    validate_dict_values(s3, required_s3_fields, verbose=True, throw=True)


def delete_results(job={}, storage={}):
    s3 = storage["s3"]
    _validate_fields(job=job, storage=storage, s3=s3)
    _required_delete_result_arguments(job, storage, s3)

    response = {"id": job["meta"]["name"]}
    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_aws_config(
        s3["config_file"], s3["credentials_file"], name=s3["name"],
    )
    s3_config["endpoint_url"] = storage["endpoint"]

    # Download results from s3
    s3_resource = stage_s3_resource(**s3_config)
    # Whether to expand all or a single result
    if "result_prefix" in job and job["result_prefix"]:
        result_prefix = job["result_prefix"]
    else:
        # Use all
        result_prefix = ""

    bucket = bucket_exists(s3_resource.meta.client, job["meta"]["name"])
    if not bucket:
        response["msg"] = "Could not find a bucket with the name: {}".format(
            job["meta"]["name"]
        )

    deleted = delete_objects(s3_resource, job["meta"]["name"], s3_prefix=result_prefix)

    if "Errors" in deleted:
        for error in deleted["Errors"]:
            print("Failed to delete: {}".format(error))

    # If the bucket is empty, remove it as well
    results = list_objects(s3_resource, job["meta"]["name"])

    if not results:
        if not delete_bucket(s3_resource.meta.client, job["meta"]["name"]):
            response["msg"] = "Failed to delete: {}".format(job["meta"]["name"])
            return False, response

    response["msg"] = "Deleted {}".format(job["meta"]["name"])
    return True, response


def _required_list_results_arguments(job, storage, s3):
    required_job_fields = {"meta": dict}
    validate_dict_values(job, required_job_fields, verbose=True, throw=True)

    required_meta_fields = {"name": str}
    validate_dict_values(job["meta"], required_meta_fields, verbose=True, throw=True)

    required_storage_fields = {
        "endpoint": str,
    }
    validate_dict_values(storage, required_storage_fields, verbose=True, throw=True)
    validate_dict_values(s3, required_s3_fields, verbose=True, throw=True)


def list_results(job={}, storage={}):
    s3 = storage["s3"]
    _validate_fields(job=job, storage=storage, s3=s3)
    _required_list_results_arguments(job, storage, s3)

    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_aws_config(
        s3["config_file"], s3["credentials_file"], name=s3["name"],
    )
    s3_config["endpoint_url"] = storage["endpoint"]

    s3_resource = stage_s3_resource(**s3_config)
    response = {"id": job["meta"]["name"]}
    results = []
    if "name" in job["meta"] and job["meta"]["name"]:
        bucket = bucket_exists(s3_resource.meta.client, job["meta"]["name"])
        if not bucket:
            response["msg"] = "Could not find a bucket with the name: {}".format(
                job["meta"]["name"]
            )
            return False, response
        results = list_objects(s3_resource, job["meta"]["name"])
    else:
        response = s3_resource.meta.client.list_buckets()
        if "Buckets" in response:
            results = response["Buckets"]

    response["results"] = results
    return True, response
