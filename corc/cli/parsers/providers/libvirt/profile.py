def valid_libvirt_group(parser):
    profile_group(parser)


def profile_group(parser):
    libvirt_group = parser.add_argument_group(title="Libvirt arguments")
    libvirt_group.add_argument("--libvirt-profile-name", default="")
    libvirt_group.add_argument("--libvirt-profile-driver-uri", default="")
    libvirt_group.add_argument("--libvirt-profile-driver-key", default=None)
    libvirt_group.add_argument("--libvirt-profile-driver-secret", default=None)

    # HACK to extract the set provider from the cli
    libvirt_group.add_argument("--libvirt", action="store_true", default=True)
