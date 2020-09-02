from corc.defaults import CLUSTER, OCI, JOB, META, S3, STORAGE, PROVIDER
from corc.cli.args import extract_arguments
from corc.cli.providers.helpers import select_provider
from corc.job import (
    run as api_run,
    get_results as api_get_results,
    delete_results as api_delete_results,
    list_results as api_list_results,
)


def run(args):
    provider_kwargs = vars(extract_arguments(args, [PROVIDER]))
    cluster_kwargs = vars(extract_arguments(args, [CLUSTER]))
    meta_kwargs = vars(extract_arguments(args, [META]))
    job_kwargs = vars(extract_arguments(args, [JOB]))
    storage_kwargs = vars(extract_arguments(args, [STORAGE]))
    s3_kwargs = vars(extract_arguments(args, [S3]))

    provider = select_provider(provider_kwargs, default_fallback=True, verbose=True)
    if not provider:
        return False
    provider_kwargs = vars(extract_arguments(args, [provider.upper()]))
    job_kwargs["meta"] = meta_kwargs

    action_kwargs = dict(
        cluster_kwargs=cluster_kwargs,
        job_kwargs=job_kwargs,
        storage_kwargs=storage_kwargs,
        staging_kwargs=s3_kwargs,
    )

    api_run(provider, provider_kwargs, action_kwargs)


def get_results(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    job_args = vars(extract_arguments(args, [JOB]))
    staging_args = vars(extract_arguments(args, [STORAGE]))
    s3_args = vars(extract_arguments(args, [S3]))

    if oci_args:
        return api_get_results(
            job_kwargs=job_args, staging_kwargs=staging_args, storage_kwargs=s3_args,
        )


def delete_results(args):
    job_args = vars(extract_arguments(args, [JOB]))
    staging_args = vars(extract_arguments(args, [STORAGE]))
    s3_args = vars(extract_arguments(args, [S3]))

    return api_delete_results(
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
        return api_list_results(
            job_kwargs=job_args,
            staging_kwargs=staging_args,
            storage_kwargs=s3_args,
            storage_extra_kwargs=storage_extra_kwargs,
        )
