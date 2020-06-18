def valid_vcn_group(parser):
    add_vcn_group(parser)


def add_vcn_group(parser):
    vcn_group = parser.add_argument_group(title="VCN arguments")
    vcn_group.add_argument("--vcn-id", default="")
    vcn_group.add_argument("--vcn-dns-label", default=None)
    vcn_group.add_argument("--vcn-display-name", default="VCN Network")
    vcn_group.add_argument("--vcn-cidr-block", default="10.0.0.0/16")
