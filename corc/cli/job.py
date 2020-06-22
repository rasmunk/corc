from corc.cli.args import extract_arguments
from corc.job import run


def run(args):
    oci_kwargs = vars(extract_arguments(args, [OCI]))
    cluster_kwargs = vars(extract_arguments(args, [CLUSTER]))
    job_kwargs = vars(extract_arguments(args, [JOB]))
    staging_kwargs = vars(extract_arguments(args, [STORAGE]))
    s3_kwargs = vars(extract_arguments(args, [S3]))

    run(
        oci_kwargs=oci_kwargs,
        cluster_kwargs=cluster_kwargs,
        job_kwargs=job_kwargs,
        staging_kwargs=staging_kwargs,
        s3_kwargs=s3_kwargs,
    )
