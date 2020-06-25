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


def validate_arguments(
    oci_kwargs, cluster_kwargs, job_kwargs, storage_kwargs, staging_kwargs
):
    validate_dict_fields(oci_kwargs, valid_profile_config, verbose=True, throw=True)
    validate_dict_values(oci_kwargs, valid_profile_config, verbose=True, throw=True)

    validate_dict_fields(cluster_kwargs, valid_cluster_config, verbose=True, throw=True)
    validate_dict_values(
        cluster_kwargs, required_run_cluster_fields, verbose=True, throw=True
    )

    validate_dict_fields(job_kwargs, valid_job_config, verbose=True, throw=True)
    validate_dict_values(job_kwargs, required_run_job_fields, verbose=True, throw=True)

    # Storage and Staging are not required to execute a job, only if enabled
    validate_dict_fields(storage_kwargs, valid_storage_config, verbose=True, throw=True)
    validate_dict_fields(staging_kwargs, valid_s3_config, verbose=True, throw=True)


def run(
    oci_kwargs, cluster_kwargs={}, job_kwargs={}, storage_kwargs={}, staging_kwargs={},
):
    # Try to load the missing values from the config
    missing_oci_dict = missing_fields(oci_kwargs, valid_profile_config)
    config_profile_prefix = gen_config_provider_prefix({"oci": {"profile": {}}})
    oci_kwargs.update(load_from_config(missing_oci_dict, prefix=config_profile_prefix))

    missing_cluster = missing_fields(cluster_kwargs, valid_cluster_config)
    config_cluster_prefix = gen_config_provider_prefix({"oci": {"cluster": {}}})
    cluster_kwargs.update(
        load_from_config(missing_cluster, prefix=config_cluster_prefix)
    )

    missing_job_dict = missing_fields(job_kwargs, valid_job_config)
    config_job_prefix = gen_config_prefix({"job": {}})
    job_kwargs.update(load_from_config(missing_job_dict, prefix=config_job_prefix))

    missing_meta_dict = missing_fields(job_kwargs["meta"], valid_job_meta_config)
    config_meta_prefix = gen_config_prefix({"job": {"meta": {}}})
    job_kwargs["meta"].update(
        load_from_config(missing_meta_dict, prefix=config_meta_prefix)
    )

    missing_storage_dict = missing_fields(storage_kwargs, valid_storage_config)
    config_storage_prefix = gen_config_prefix({"storage": {}})
    storage_kwargs.update(
        load_from_config(missing_storage_dict, prefix=config_storage_prefix)
    )

    missing_staging_dict = missing_fields(staging_kwargs, valid_s3_config)
    config_staging_prefix = gen_config_prefix({"storage": {"s3": {}}})
    staging_kwargs.update(
        load_from_config(missing_staging_dict, prefix=config_staging_prefix)
    )

    validate_arguments(
        oci_kwargs, cluster_kwargs, job_kwargs, storage_kwargs, staging_kwargs
    )

    if "name" not in job_kwargs["meta"] or not job_kwargs["meta"]["name"]:
        since_epoch = int(time.time())
        job_kwargs["meta"]["name"] = "{}-{}".format(JOB_DEFAULT_NAME, since_epoch)

    if "bucket_name" not in staging_kwargs or not staging_kwargs["bucket_name"]:
        staging_kwargs["bucket_name"] = job_kwargs["meta"]["name"]

    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        profile_name=oci_kwargs["profile_name"],
    )

    cluster = get_cluster_by_name(
        container_engine_client,
        oci_kwargs["compartment_id"],
        name=cluster_kwargs["name"],
    )

    if not cluster:
        print("Failed to find a cluster with name: {}".format(cluster_kwargs["name"]))
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
        job_kwargs["command"],
        "--job-name",
        job_kwargs["meta"]["name"],
    ]

    if "args" in job_kwargs:
        jobio_args.extend(["--execute-args", " ".join(job_kwargs["args"])])

    if "output_path" in job_kwargs:
        jobio_args.extend(
            ["--execute-output-path", job_kwargs["output_path"],]
        )

    if "capture" in job_kwargs and job_kwargs["capture"]:
        jobio_args.append("--execute-capture")

    if "debug" in job_kwargs["meta"]:
        jobio_args.append("--job-debug")

    if "env_override" in job_kwargs["meta"]:
        jobio_args.append("--job-env-override")

    # Maintained by the pod
    volumes = []
    # Maintained by the container
    volume_mounts = []
    # Environment to pass to the container
    envs = []

    # Prepare config for the scheduler
    scheduler_config = {}

    if storage_kwargs and storage_kwargs["enable"]:
        validate_dict_values(storage_kwargs, required_storage_fields, throw=True)
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
            mount_path=storage_kwargs["credentials_path"],
            read_only=True,
        )
        volume_mounts.append(secret_mount)

        if staging_kwargs:
            validate_dict_values(staging_kwargs, required_staging_values, throw=True)
            jobio_args.append("--storage-s3")
            # S3 storage
            # Look for s3 credentials and config files
            s3_config = load_s3_config(
                staging_kwargs["config_file"],
                staging_kwargs["credentials_file"],
                storage_kwargs["endpoint"],
                profile_name=staging_kwargs["profile_name"],
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

            bucket = bucket_exists(s3.meta.client, staging_kwargs["bucket_name"])
            if not bucket:
                bucket = s3.create_bucket(
                    Bucket=staging_kwargs["bucket_name"],
                    CreateBucketConfiguration={
                        "LocationConstraint": s3_config["region_name"]
                    },
                )

            if "upload_path" in storage_kwargs and storage_kwargs["upload_path"]:
                # Upload local path to the bucket as designated input for the job
                if os.path.exists(storage_kwargs["upload_path"]):
                    if os.path.isdir(storage_kwargs["upload_path"]):
                        uploaded = upload_directory_to_s3(
                            s3.meta.client,
                            storage_kwargs["upload_path"],
                            staging_kwargs["bucket_name"],
                            s3_prefix=staging_kwargs["bucket_input_prefix"],
                        )
                    elif os.path.isfile(storage_kwargs["upload_path"]):
                        s3_path = os.path.basename(storage_kwargs["upload_path"])
                        if staging_kwargs["bucket_input_prefix"]:
                            s3_path = os.path.join(
                                staging_kwargs["bucket_input_prefix"], s3_path
                            )
                        # Upload
                        uploaded = upload_to_s3(
                            s3.meta.client,
                            storage_kwargs["upload_path"],
                            s3_path,
                            staging_kwargs["bucket_name"],
                        )

                if not uploaded:
                    raise RuntimeError(
                        "Failed to local path: {} in the upload folder to s3".format(
                            storage_kwargs["upload_path"]
                        )
                    )

            jobio_args.extend(
                [
                    "--s3-region-name",
                    s3_config["region_name"],
                    "--storage-secrets-dir",
                    storage_kwargs["credentials_path"],
                    "--storage-endpoint",
                    storage_kwargs["endpoint"],
                    "--storage-input-path",
                    storage_kwargs["input_path"],
                    "--storage-output-path",
                    storage_kwargs["output_path"],
                    "--bucket-name",
                    staging_kwargs["bucket_name"],
                    "--bucket-input-prefix",
                    staging_kwargs["bucket_input_prefix"],
                    "--bucket-output-prefix",
                    staging_kwargs["bucket_output_prefix"],
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
        name=job_kwargs["meta"]["name"],
        image=cluster_kwargs["image"],
        env=envs,
        args=jobio_args,
        volume_mounts=volume_mounts,
    )
    # args=jobio_args,
    pod_spec = dict(node_name=node.metadata.name, volumes=volumes, dns_policy="Default")

    job_spec = dict(
        backoff_limit=2,
        parallelism=job_kwargs["meta"]["num_parallel"],
        completions=job_kwargs["meta"]["num_jobs"],
    )

    task = dict(
        container_kwargs=container_spec,
        pod_spec_kwargs=pod_spec,
        job_spec_kwargs=job_spec,
    )

    job_id = scheduler.submit(**task)
    if not job_id:
        exit(1)


def get_results(job_kwargs={}, staging_kwargs={}, storage_kwargs={}):
    validate_dict_types(staging_kwargs, required_get_storage_fields, throw=True)
    validate_dict_values(staging_kwargs, required_get_storage_values, throw=True)

    validate_dict_types(storage_kwargs, required_s3_fields, throw=True)
    validate_dict_values(storage_kwargs, required_s3_values, throw=True)

    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_s3_config(
        storage_kwargs["config_file"],
        storage_kwargs["credentials_file"],
        staging_kwargs["endpoint"],
        profile_name=storage_kwargs["profile_name"],
    )

    # Download results from s3
    s3_resource = stage_s3_resource(**s3_config)

    # Whether to expand all or a single result
    if "result_prefix" in job_kwargs and job_kwargs["result_prefix"]:
        result_prefix = job_kwargs["result_prefix"]
    else:
        # Use all
        result_prefix = ""

    bucket = bucket_exists(s3_resource.meta.client, job_kwargs["name"])
    if not bucket:
        raise RuntimeError(
            "Could not find a bucket with the name: {}".format(job_kwargs["name"])
        )

    expanded = expand_s3_bucket(
        s3_resource,
        job_kwargs["name"],
        staging_kwargs["download_path"],
        s3_prefix=result_prefix,
    )

    if not expanded:
        raise RuntimeError(
            "Failed to expand the target bucket: {}".format(job_kwargs["name"])
        )


def delete_results(job_kwargs={}, staging_kwargs={}, storage_kwargs={}):

    validate_dict_types(staging_kwargs, required_delete_storage_fields, throw=True)
    validate_dict_values(staging_kwargs, required_delete_storage_values, throw=True)

    validate_dict_types(storage_kwargs, required_s3_fields, throw=True)
    validate_dict_values(storage_kwargs, required_s3_values, throw=True)

    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_s3_config(
        storage_kwargs["config_file"],
        storage_kwargs["credentials_file"],
        staging_kwargs["endpoint"],
        profile_name=storage_kwargs["profile_name"],
    )

    # Download results from s3
    s3_resource = stage_s3_resource(**s3_config)

    # Whether to expand all or a single result
    if "result_prefix" in job_kwargs and job_kwargs["result_prefix"]:
        result_prefix = job_kwargs["result_prefix"]
    else:
        # Use all
        result_prefix = ""

    bucket = bucket_exists(s3_resource.meta.client, job_kwargs["name"])
    if not bucket:
        raise RuntimeError(
            "Could not find a bucket with the name: {}".format(job_kwargs["name"])
        )

    deleted = delete_objects(s3_resource, job_kwargs["name"], s3_prefix=result_prefix)

    if "Errors" in deleted:
        for error in deleted["Errors"]:
            print("Failed to delete: {}".format(error))

    # If the bucket is empty, remove it as well
    results = list_objects(s3_resource, job_kwargs["name"])

    if not results:
        if not delete_bucket(s3_resource.meta.client, job_kwargs["name"]):
            return False
    return True


def list_results(
    job_kwargs={}, staging_kwargs={}, storage_kwargs={}, storage_extra_kwargs={},
):
    # S3 storage
    # Look for s3 credentials and config files
    s3_config = load_s3_config(
        storage_kwargs["config_file"],
        storage_kwargs["credentials_file"],
        staging_kwargs["endpoint"],
        profile_name=storage_kwargs["profile_name"],
    )

    s3_resource = stage_s3_resource(**s3_config)
    response = {}
    results = []
    if "name" in job_kwargs and job_kwargs["name"]:
        bucket = bucket_exists(s3_resource.meta.client, job_kwargs["name"])
        if not bucket:
            raise RuntimeError(
                "Could not find a bucket with the name: {}".format(job_kwargs["name"])
            )
        results = list_objects(s3_resource, job_kwargs["name"], **storage_extra_kwargs)
    else:
        response = s3_resource.meta.client.list_buckets()
        if "Buckets" in response:
            results = response["Buckets"]
    return results
