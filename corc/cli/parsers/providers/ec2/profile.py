def valid_aws_group(parser):
    add_ec2_group(parser)


def add_ec2_group(parser):
    aws_group = parser.add_argument_group(title="EC2 arguments")
    aws_group.add_argument("--ec2-profile-name", default="")
    aws_group.add_argument("--ec2-profile-region-name", default="")

    # HACK to extract the set provider from the cli
    aws_group.add_argument("--ec2", action="store_true", default=True)
