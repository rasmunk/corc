import argparse
from corc.defaults import PACKAGE_NAME
from corc.cli.helpers import (
    add_job_cli,
    add_cluster_cli,
    add_instance_cli,
    add_platform_group,
)


def run():
    parser = argparse.ArgumentParser(prog=PACKAGE_NAME)
    # Platform
    add_platform_group(parser)

    commands = parser.add_subparsers(title="COMMAND")
    instance_parser = commands.add_parser("instance")
    add_instance_cli(instance_parser)

    cluster_parser = commands.add_parser("cluster")
    add_cluster_cli(cluster_parser)

    job_parser = commands.add_parser("job")
    add_job_cli(job_parser)

    args = parser.parse_args()
    # Execute default function
    if hasattr(args, "func"):
        result = args.func(args)
        if result:
            print(result)
    return None


if __name__ == "__main__":
    arguments = run()
