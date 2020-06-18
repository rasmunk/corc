def valid_oci_group(parser):
    add_oci_group(parser)


def add_oci_group(parser):
    oci_group = parser.add_argument_group(title="OCI arguments")
    oci_group.add_argument("--oci-profile-name", default="DEFAULT")
    oci_group.add_argument("--oci-compartment-id", default="")
