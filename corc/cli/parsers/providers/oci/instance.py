def instance_identity_group(parser):
    instance_group = parser.add_argument_group(title="Instance Identity arguments")
    instance_group.add_argument("--instance-id", default="")
    instance_group.add_argument("--instance-display-name", default="")


def instance_get_group(parser):
    instance_group = parser.add_argument_group(title="Instance Get arguments")
    instance_group.add_argument(
        "--details-endpoints", action="store_true", default=False
    )


def start_instance_group(parser):
    instance_group = parser.add_argument_group(title="OCI Instance arguments")
    instance_group.add_argument("--instance-display-name", default="")
    instance_group.add_argument("--instance-ssh-authorized-keys", nargs="+", default=[])
    instance_group.add_argument("--instance-availability-domain", default="")
    instance_group.add_argument("--instance-operating-system", default="")
    instance_group.add_argument("--instance-operating-system-version", default="")
    instance_group.add_argument("--instance-shape", default="")
