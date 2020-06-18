def valid_config_group(parser):
    add_config_group(parser)


def add_config_group(parser):
    storage_group = parser.add_argument_group(title="Config argument")
    storage_group.add_argument("--generate-config", action="store_true", default=True)
