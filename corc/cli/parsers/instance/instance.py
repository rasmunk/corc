from corc.cli.parsers.providers.oci.instance import (
    start_instance_group as oci_start_instance,
)
from corc.cli.parsers.providers.ec2.instance import (
    start_instance_group as ec2_start_instance,
)


def valid_instance_group(parser):
    instance_identity_group(parser)
    oci_start_instance(parser)
    ec2_start_instance(parser)


def instance_identity_group(parser):
    instance_group = parser.add_argument_group(title="Instance Identity arguments")
    instance_group.add_argument("--instance-id", default="")
