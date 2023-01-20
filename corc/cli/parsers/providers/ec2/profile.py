def valid_ec2_group(parser):
    profile_group(parser)


def profile_group(parser):
    ec2_group = parser.add_argument_group(title="EC2 arguments")
    ec2_group.add_argument("--ec2-profile-name", default="")
    ec2_group.add_argument("--ec2-profile-region-name", default="")

    # HACK to extract the set provider from the cli
    ec2_group.add_argument("--ec2", action="store_true", default=True)
