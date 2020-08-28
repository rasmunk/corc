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
    arguments = parser.add_argument_group(title="VCN Subnet Identity arguments")
    arguments.add_argument("--vcn-subnet-id", default="")


def vcn_subnet_config_group(parser):
    arguments = parser.add_argument_group(title="VCN Subnet arguments")
    arguments.add_argument("--vcn-subnet-dns-label", default="")
    arguments.add_argument("--vcn-subnet-cidr-block", default="")


def vcn_internetgateway_identity_group(parser):
    arguments = parser.add_argument_group(
        title="VCN Internet Gateway Identity arguments"
    )
    arguments.add_argument("--vcn-internetgateway-id", default="")


def vcn_internetgateway_config_group(parser):
    arguments = parser.add_argument_group(title="VCN Internet Gateway arguments")
    arguments.add_argument(
        "--vcn-internetgateway-is-enabled", action="store_true", default=True
    )


def vcn_routetable_identity_group(parser):
    arguments = parser.add_argument_group(title="VCN Route Table Identity arguments")
    arguments.add_argument("--vcn-routetable-id", default="")
