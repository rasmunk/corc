import argparse
import json
from corc.defaults import PACKAGE_NAME, AWS_LOWER, OCI_LOWER
from corc.cli.helpers import (
    config_cli,
    job_cli,
    orchestration_cli,
    add_aws_group,
    add_oci_group,
)


def run():
    parser = argparse.ArgumentParser(prog=PACKAGE_NAME)
    commands = parser.add_subparsers(title="COMMAND")
    config_parser = commands.add_parser("config")
    config_cli(config_parser)

    # AWS
    aws_parser = commands.add_parser(AWS_LOWER)
    add_aws_group(aws_parser)

    # OCI
    oci_parser = commands.add_parser(OCI_LOWER)
    add_oci_group(oci_parser)
    oci_commands = oci_parser.add_subparsers(title="COMMAND")

    orchestration_parser = oci_commands.add_parser("orchestration")
    orchestration_cli(orchestration_parser)

    job_parser = oci_commands.add_parser("job")
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
