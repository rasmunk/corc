def valid_aws_group(parser):
    add_aws_group(parser)


def add_aws_group(parser):
    aws_group = parser.add_argument_group(title="AWS arguments")
    aws_group.add_argument("--aws", action="store_true", default=False)
