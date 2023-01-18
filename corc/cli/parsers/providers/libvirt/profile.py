def valid_libvirt_group(parser):
    add_libvirt_group(parser)


def add_libvirt_group(parser):
    libvirt_group = parser.add_argument_group(title="Libvirt arguments")
    libvirt_group.add_argument("--libvirt-profile-name", default="")

    # HACK to extract the set provider from the cli
    libvirt_group.add_argument("--libvirt", action="store_true", default=True)
