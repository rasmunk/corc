def valid_subnet_group(parser):
    add_subnet_group(parser)


def add_subnet_group(parser):
    subnet_group = parser.add_argument_group(title="Subnet arguments")
    subnet_group.add_argument("--subnet-id", default="")
    subnet_group.add_argument("--subnet-dns-label", default=None)
    subnet_group.add_argument("--subnet-cidr-block", default="")
