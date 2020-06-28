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
    load_from_config,
    gen_config_provider_prefix,
    gen_config_prefix,
    valid_job_config,
    valid_job_meta_config,
    valid_storage_config,
    valid_s3_config,
)
from corc.defaults import (
    STORAGE_CREDENTIALS_NAME,
    KUBERNETES_NAMESPACE,
    JOB_DEFAULT_NAME,
)
from corc.util import (
    validate_dict_fields,
    validate_dict_types,
    validate_dict_values,
    missing_fields,
)
from corc.storage.s3 import (
    bucket_exists,
    delete_bucket,
    delete_objects,
    list_objects,
    load_s3_config,
    required_s3_fields,
    required_s3_values,
    upload_to_s3,
    upload_directory_to_s3,
)
from corc.kubernetes.nodes import NodeManager
from corc.kubernetes.scheduler import KubenetesScheduler
from corc.providers.oci.cluster import get_cluster_by_name, refresh_kube_config
from corc.providers.oci.helpers import new_client
from corc.providers.oci.config import valid_profile_config, valid_cluster_config


required_run_cluster_fields = {"name": str, "image": str}

required_run_job_fields = {
    "meta": {"num_jobs": int, "num_parallel": int},
    "command": str,
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
    "profile_name": True,
    "bucket_name": True,
    "bucket_input_prefix": True,
    "bucket_output_prefix": True,
}


def validate_arguments(provider_kwargs, cluster, job, storage, s3):
    validate_dict_fields(
        provider_kwargs, valid_profile_config, verbose=True, throw=True
    )
    validate_dict_values(
        provider_kwargs, valid_profile_config, verbose=True, throw=True
    )

    validate_dict_fields(cluster, valid_cluster_config, verbose=True, throw=True)
    validate_dict_values(cluster, required_run_cluster_fields, verbose=True, throw=True)

    validate_dict_fields(job, valid_job_config, verbose=True, throw=True)
    validate_dict_values(job, required_run_job_fields, verbose=True, throw=True)

    # Storage and Staging are not required to execute a job, only if enabled
    validate_dict_fields(storage, valid_storage_config, verbose=True, throw=True)
    validate_dict_fields(s3, valid_s3_config, verbose=True, throw=True)


def run(
    provider_kwargs, cluster={}, job={}, storage={}, s3={},
):
    # Try to load the missing values from the config
    # missing_oci_dict = missing_fields(oci_kwargs, valid_profile_config)
    # config_profile_prefix = gen_config_provider_prefix({"oci": {"profile": {}}})
    # oci_kwargs.update(load_from_config(missing_oci_dict, prefix=config_profile_prefix))

    # missing_cluster = missing_fields(cluster, valid_cluster_config)
    # config_cluster_prefix = gen_config_provider_prefix({"oci": {"cluster": {}}})
    # cluster.update(
    #     load_from_config(missing_cluster, prefix=config_cluster_prefix)
    # )

    # missing_job_dict = missing_fields(job, valid_job_config)
    # config_job_prefix = gen_config_prefix({"job": {}})
    # job.update(load_from_config(missing_job_dict, prefix=config_job_prefix))

    # missing_meta_dict = missing_fields(job["meta"], valid_job_meta_config)
    # config_meta_prefix = gen_config_prefix({"job": {"meta": {}}})
    # job["meta"].update(
    #     load_from_config(missing_meta_dict, prefix=config_meta_prefix)
    # )

    # missing_storage_dict = missing_fields(storage, valid_storage_config)
    # config_storage_prefix = gen_config_prefix({"storage": {}})
    # storage.update(
    #     load_from_config(missing_storage_dict, prefix=config_storage_prefix)
    # )

    # missing_staging_dict = missing_fields(s3, valid_s3_config)
    # config_staging_prefix = gen_config_prefix({"storage": {"s3": {}}})
    # s3.update(
    #     load_from_config(missing_staging_dict, prefix=config_staging_prefix)
    # )

    validate_arguments(provider_kwargs, cluster, job, storage, s3)

    if "name" not in job["meta"] or not job["meta"]["name"]:
        since_epoch = int(time.time())
        job["meta"]["name"] = "{}-{}".format(JOB_DEFAULT_NAME, since_epoch)

    if "bucket_name" not in s3 or not s3["bucket_name"]:
        s3["bucket_name"] = job["meta"]["name"]

    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        profile_name=oci_kwargs["profile_name"],
    )

    cluster = get_cluster_by_name(
        container_engine_client, oci_kwargs["compartment_id"], name=cluster["name"],
    )

    if not cluster:
        print("Failed to find a cluster with name: {}".format(cluster["name"]))
        return False

    refreshed = refresh_kube_config(cluster.id, profile_name=oci_kwargs["profile_name"])
    if not refreshed:
        exit(1)

    node_manager = NodeManager()
    node_manager.discover()
    node = node_manager.select()

    # Ensure we have the newest config
    scheduler = KubenetesScheduler()

    jobio_args = [
        "jobio",
        "run",
        job["command"],
        "--job-name",
        job["meta"]["name"],
    ]

    if "args" in job:
        jobio_args.extend(["--execute-args", " ".join(job["args"])])

    if "output_path" in job:
        jobio_args.extend(
            ["--execute-output-path", job["output_path"],]
        )

    if "capture" in job and job["capture"]:
        jobio_args.append("--execute-capture")

    if "debug" in job["meta"]:
        jobio_args.append("--job-debug")

    if "env_override" in job["meta"]:
        jobio_args.append("--job-env-override")

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

        # Storage endpoint credentials secret
        try:
            storage_credentials_secret = core_api.read_namespaced_secret(
                STORAGE_CREDENTIALS_NAME, KUBERNETES_NAMESPACE
            )
        except ApiException:
            storage_credentials_secret = None

        # volumes
        secret_volume_source = V1SecretVolumeSource(
            secret_name=STORAGE_CREDENTIALS_NAME
        )
        secret_volume = V1Volume(
            name=STORAGE_CREDENTIALS_NAME, secret=secret_volume_source
        )
        volumes.append(secret_volume)

        # Where the storage credentials should be mounted
        # in the compute unit
        secret_mount = V1VolumeMount(
            name=STORAGE_CREDENTIALS_NAME,
            mount_path=storage["credentials_path"],
            read_only=True,
        )
        volume_mounts.append(secret_mount)

        if s3:
            validate_dict_values(s3, required_staging_values, throw=True)
            jobio_args.append("--storage-s3")
            # S3 storage
            # Look for s3 credentials and config files
            s3_config = load_s3_config(
                s3["config_file"],
                s3["credentials_file"],
                storage["endpoint"],
                profile_name=s3["profile_name"],
            )

            if not storage_credentials_secret:
                secret_data = dict(
                    aws_access_key_id=s3_config["aws_access_key_id"],
                    aws_secret_access_key=s3_config["aws_secret_access_key"],
                )
                secret_metadata = V1ObjectMeta(name=STORAGE_CREDENTIALS_NAME)
                secrets_config = dict(metadata=secret_metadata, string_data=secret_data)
                scheduler_config.update(dict(secret_kwargs=secrets_config))

            # If `access_key`
            # TODO, unify argument endpoint, with s3 config endpoint'
            s3 = boto3.resource("s3", **s3_config)

            bucket = bucket_exists(s3.meta.client, s3["bucket_name"])
            if not bucket:
                bucket = s3.create_bucket(
                    Bucket=s3["bucket_name"],
                    CreateBucketConfiguration={
                        "LocationConstraint": s3_config["region_name"]
                    },
                )

            if "upload_path" in storage and storage["upload_path"]:
                # Upload local path to the bucket as designated input for the job
                if os.path.exists(storage["upload_path"]):
                    if os.path.isdir(storage["upload_path"]):
                        uploaded = upload_directory_to_s3(
                            s3.meta.client,
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
                            s3.meta.client,
                            storage["upload_path"],
                            s3_path,
                            s3["bucket_name"],
                        )

                if not uploaded:
                    raise RuntimeError(
                        "Failed to local path: {} in the upload folder to s3".format(
                            storage["upload_path"]
                        )
                    )

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
            raise RuntimeError("Failed to prepare the scheduler")

    container_spec = dict(
        name=job["meta"]["name"],
        image=cluster["image"],
        env=envs,
        args=jobio_args,
        volume_mounts=volume_mounts,
    )
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

    job_id = scheduler.submit(**task)
    if not job_id:
        exit(1)


def get_results(job={}, s3={}, storage={}):
    validate_dict_types(s3, required_get_storage_fields, throw=True)
    validate_dict_values(s3, required_get_storage_values, throw=True)

    validate_dict_types(storage, required_s3_fields, throw=True)
    validate_dict_values(storage, required_s3_values, throw=True)

    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_s3_config(
        storage["config_file"],
        storage["credentials_file"],
        s3["endpoint"],
        profile_name=storage["profile_name"],
    )

    # Download results from s3
    s3_resource = stage_s3_resource(**s3_config)

    # Whether to expand all or a single result
    if "result_prefix" in job and job["result_prefix"]:
        result_prefix = job["result_prefix"]
    else:
        # Use all
        result_prefix = ""

    bucket = bucket_exists(s3_resource.meta.client, job["name"])
    if not bucket:
        raise RuntimeError(
            "Could not find a bucket with the name: {}".format(job["name"])
        )

    expanded = expand_s3_bucket(
        s3_resource, job["name"], s3["download_path"], s3_prefix=result_prefix,
    )

    if not expanded:
        raise RuntimeError("Failed to expand the target bucket: {}".format(job["name"]))


def delete_results(job={}, s3={}, storage={}):

    validate_dict_types(s3, required_delete_storage_fields, throw=True)
    validate_dict_values(s3, required_delete_storage_values, throw=True)

    validate_dict_types(storage, required_s3_fields, throw=True)
    validate_dict_values(storage, required_s3_values, throw=True)

    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_s3_config(
        storage["config_file"],
        storage["credentials_file"],
        s3["endpoint"],
        profile_name=storage["profile_name"],
    )

    # Download results from s3
    s3_resource = stage_s3_resource(**s3_config)

    # Whether to expand all or a single result
    if "result_prefix" in job and job["result_prefix"]:
        result_prefix = job["result_prefix"]
    else:
        # Use all
        result_prefix = ""

    bucket = bucket_exists(s3_resource.meta.client, job["name"])
    if not bucket:
        raise RuntimeError(
            "Could not find a bucket with the name: {}".format(job["name"])
        )

    deleted = delete_objects(s3_resource, job["name"], s3_prefix=result_prefix)

    if "Errors" in deleted:
        for error in deleted["Errors"]:
            print("Failed to delete: {}".format(error))

    # If the bucket is empty, remove it as well
    results = list_objects(s3_resource, job["name"])

    if not results:
        if not delete_bucket(s3_resource.meta.client, job["name"]):
            return False
    return True


def list_results(
    job={}, s3={}, storage={}, storage_extra_kwargs={},
):
    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_s3_config(
        storage["config_file"],
        storage["credentials_file"],
        s3["endpoint"],
        profile_name=storage["profile_name"],
    )

    s3_resource = stage_s3_resource(**s3_config)
    response = {}
    results = []
    if "name" in job and job["name"]:
        bucket = bucket_exists(s3_resource.meta.client, job["name"])
        if not bucket:
            raise RuntimeError(
                "Could not find a bucket with the name: {}".format(job["name"])
            )
        results = list_objects(s3_resource, job["name"], **storage_extra_kwargs)
    else:
        response = s3_resource.meta.client.list_buckets()
        if "Buckets" in response:
            results = response["Buckets"]
    return results
