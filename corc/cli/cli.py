import argparse
import sys
from corc.cli.helpers import (
    add_job_cli,
    add_cluster_cli,
    add_instance_cli,
    add_platform_group,
)


NAME = "corc"


def run():
    parser = argparse.ArgumentParser(prog=NAME)
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
    # Execute default funciton
    if hasattr(args, "func"):
        args.func(args)
    return None


if __name__ == "__main__":
    arguments = run()
