import yaml


def parse_yaml(data):
    try:
        parsed = yaml.safe_load(data)
        return parsed
    except yaml.reader.ReaderError as err:
        print("Failed to parse yaml: {}".format(err))
    return False


def dump_yaml(path, data):
    try:
        with open(path, "w") as fh:
            yaml.dump(data, fh)
        return True
    except IOError as err:
        print("Failed to dump yaml: {} - {}".format(path, err))
    return False


def validate_config(config, required_fields=None):
    if not required_fields:
        required_fields = {}
    for var, _type in required_fields.items():
        if var not in config:
            raise KeyError("{} variable is missing from config: {}".format(var, config))
        if not isinstance(config[var], _type):
            raise ValueError(
                "variable: {} value: {} is of incorrect type: {}".format(
                    var, config[var], type(config[var])
                )
            )
    return True
