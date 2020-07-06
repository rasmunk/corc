def valid_vcn_group(parser):
    vcn_identity_group(parser)
    vcn_config_group(parser)
    vcn_subnet_identity_group(parser)
    vcn_subnet_config_group(parser)


def vcn_identity_group(parser):
    vcn_group = parser.add_argument_group(title="VCN Identity arguments")
    vcn_group.add_argument("--vcn-id", default="")


def vcn_config_group(parser):
    vcn_group = parser.add_argument_group(title="VCN arguments")
    vcn_group.add_argument("--vcn-dns-label", default="")
    vcn_group.add_argument("--vcn-display-name", default="")
    vcn_group.add_argument("--vcn-cidr-block", default="")


def vcn_subnet_identity_group(parser):
    subnet_group = parser.add_argument_group(title="VCN Subnet Identity arguments")
    subnet_group.add_argument("--vcn-subnet-id", default="")


def vcn_subnet_config_group(parser):
    subnet_group = parser.add_argument_group(title="VCN Subnet arguments")
    subnet_group.add_argument("--vcn-subnet-dns-label", default="")
    subnet_group.add_argument("--vcn-subnet-cidr-block", default="")
