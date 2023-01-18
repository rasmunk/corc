def instance_identity_group(parser):
    instance_group = parser.add_argument_group(title="Instance identity arguments")
    instance_group.add_argument("--instance-uuid", default="")
    instance_group.add_argument("--instance-name", default="")


def start_instance_group(parser):
    instance_group = parser.add_argument_group(title="Libvirt instance arguments")
    instance_group.add_argument("--instance-name", default="")
    instance_group.add_argument("--instance-ssh-authorized-key", default="")
