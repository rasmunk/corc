from corc.defaults import CLUSTER, OCI, JOB, S3, STORAGE
from corc.cli.args import extract_arguments
from corc.providers.oci.job import (
    run as oci_run,
    get_results as oci_get_results,
    delete_results as oci_delete_results,
    list_results as oci_list_results,
)


def run(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    cluster_args = vars(extract_arguments(args, [CLUSTER]))
    job_args = vars(extract_arguments(args, [JOB]))
    staging_args = vars(extract_arguments(args, [STORAGE]))
    s3_args = vars(extract_arguments(args, [S3]))

    if not s3_args["bucket_name"]:
        s3_args["bucket_name"] = job_args["name"]

    if oci_args:
        oci_run(
            cluster_kwargs=cluster_args,
            job_kwargs=job_args,
            oci_kwargs=oci_args,
            staging_kwargs=staging_args,
            storage_kwargs=s3_args,
        )


def get_results(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    job_args = vars(extract_arguments(args, [JOB]))
    staging_args = vars(extract_arguments(args, [STORAGE]))
    s3_args = vars(extract_arguments(args, [S3]))

    if oci_args:
        return oci_get_results(
            job_kwargs=job_args, staging_kwargs=staging_args, storage_kwargs=s3_args,
        )


def delete_results(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    job_args = vars(extract_arguments(args, [JOB]))
    staging_args = vars(extract_arguments(args, [STORAGE]))
    s3_args = vars(extract_arguments(args, [S3]))

    if oci_args:
        return oci_delete_results(
            job_kwargs=job_args, staging_kwargs=staging_args, storage_kwargs=s3_args
        )


def list_results(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    job_args = vars(extract_arguments(args, [JOB]))
    staging_args = vars(extract_arguments(args, [STORAGE]))
    s3_args = vars(extract_arguments(args, [S3]))

    if oci_args:
        if "extra_kwargs" in s3_args:
            storage_extra_kwargs = s3_args.pop("extra_kwargs")
        return oci_list_results(
            job_kwargs=job_args,
            staging_kwargs=staging_args,
            storage_kwargs=s3_args,
            storage_extra_kwargs=storage_extra_kwargs,
        )
