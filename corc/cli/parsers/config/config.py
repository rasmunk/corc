def valid_config_group(parser):
    add_config_group(parser)


def add_config_group(parser):
    config_group = parser.add_argument_group(title="Config argument")
    generate_config = config_group.add_mutually_exclusive_group(required=True)
    generate_config.add_argument(
        "--config-generate-full", action="store_true", default=False
    )
    generate_config.add_argument(
        "--config-generate-job", action="store_true", default=False
    )
