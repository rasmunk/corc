from corc.defaults import (
    OCI,
    SUBNET,
    COMPUTE,
    VCN,
)
from corc.cli.args import extract_arguments
from corc.providers.oci.instance import launch_instance as oci_launch_instance


def launch_instance(args):
    oci_args = vars(extract_arguments(args, [OCI]))
    compute_args = vars(extract_arguments(args, [COMPUTE]))
    subnet_args = vars(extract_arguments(args, [SUBNET]))
    vcn_args = vars(extract_arguments(args, [VCN]))

    if oci_args:
        return oci_launch_instance(
            compute_kwargs=compute_args,
            oci_kwargs=oci_args,
            subnet_kwargs=subnet_args,
            vcn_kwargs=vcn_args,
        )
