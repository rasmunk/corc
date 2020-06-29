def valid_oci_group(parser):
    add_oci_group(parser)


def add_oci_group(parser):
    oci_group = parser.add_argument_group(title="OCI arguments")
    oci_group.add_argument("--oci-profile-name", default="")
    oci_group.add_argument("--oci-profile-compartment-id", default="")

    # HACK to extract the set provider from the cli
    oci_group.add_argument("--oci", action="store_true", default=True)
