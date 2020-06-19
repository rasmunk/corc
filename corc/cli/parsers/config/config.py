def valid_config_group(parser):
    add_config_group(parser)


def add_config_group(parser):
    config_group = parser.add_argument_group(title="Config argument")
    config_group.add_argument("--config-full", action="store_true", default=True)
