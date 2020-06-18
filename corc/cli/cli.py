import argparse
import json
from corc.defaults import PACKAGE_NAME
from corc.cli.helpers import (
    config_cli,
    job_cli,
    orchestration_cli,
)


def run():
    parser = argparse.ArgumentParser(prog=PACKAGE_NAME)
    commands = parser.add_subparsers(title="COMMAND")
    config_parser = commands.add_parser("config")
    config_cli(config_parser)

    orchestration_parser = commands.add_parser("orchestration")
    orchestration_cli(orchestration_parser)

    job_parser = commands.add_parser("job")
    job_cli(job_parser)

    args = parser.parse_args()
    # Execute default function
    if hasattr(args, "func"):
        result = args.func(args)
        if result:
            try:
                json_object = json.loads(result)
                print(json.dumps(json_object, indent=2))
            except Exception:
                print(result)
    return None


if __name__ == "__main__":
    arguments = run()
