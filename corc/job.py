import corc.providers as providers
from corc.defaults import CLUSTER, OCI, JOB, S3, STORAGE
from corc.cli.args import extract_arguments
from corc.providers.oci.job import (
    run as oci_run,
    get_results as oci_get_results,
    delete_results as oci_delete_results,
    list_results as oci_list_results,
)


def run(args):
    provider_kwargs = extract_arguments(args, [PROVIDER])
    # Interpolate kwargs with config
    _provider = __import__("{}.{}.{}".format("corc.providers", "job"), fromlist=['object'])
    run_func = getattr(_provider, "run")
    return run_func(**kwargs)


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
