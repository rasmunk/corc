def instance_identity_group(parser):
    instance_group = parser.add_argument_group(title="Instance Identity arguments")
    instance_group.add_argument("--instance-uuid", default="")
    instance_group.add_argument("--instance-name", default="")


def start_instance_group(parser):
    instance_group = parser.add_argument_group(title="AWS Instance arguments")
    instance_group.add_argument("--instance-name", default="")
    instance_group.add_argument("--instance-image", default="")
    instance_group.add_argument("--instance-size", default="")
    instance_group.add_argument("--instance-ssh-authorized-key", default="")
