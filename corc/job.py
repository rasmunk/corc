from corc.defaults import AWS, OCI, JOB, RUN, STORAGE, CLUSTER, EXECUTE
from corc.cli.args import extract_arguments
from corc.oci.job import run as oci_run


def run(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    aws_args = vars(extract_arguments(args, [AWS]))
    cluster_args = vars(extract_arguments(args, [CLUSTER]))
    job_args = vars(extract_arguments(args, [JOB]))
    execute_args = vars(extract_arguments(args, [EXECUTE]))
    storage_args = vars(extract_arguments(args, [STORAGE]))

    if oci_args:
        return oci_run(
            cluster_kwargs=cluster_args,
            execute_kwargs=execute_args,
            job_kwargs=job_args,
            oci_kwargs=oci_args,
            storage_kwargs=storage_args,
        )

    if aws_args:
        pass
        # return aws_run
