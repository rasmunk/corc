def valid_instance_group(parser):
    start_instance_group(parser)
    instance_identity_group(parser)


def instance_identity_group(parser):
    instance_group = parser.add_argument_group(title="Instance Identity arguments")
    instance_group.add_argument("--instance-id", default="")
    instance_group.add_argument("--instance-display-name", default="")


def start_instance_group(parser):
    instance_group = parser.add_argument_group(title="Instance arguments")
    instance_group.add_argument("--instance-ssh-authorized-keys", nargs="+", default=[])
    instance_group.add_argument("--instance-availability-domain", default="")
    instance_group.add_argument("--instance-operating-system", default="")
    instance_group.add_argument("--instance-operating-system-version", default="")
    instance_group.add_argument("--instance-shape", default="")
