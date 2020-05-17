import argparse
from corc.args import add_instance_cli, add_cluster_cli, add_job_cli, add_platform_group


NAME = "corc"


def cli():
    # usage_msg = "%(prog)s [OPTIONS] COMMAND [ARGS]"
    parser = argparse.ArgumentParser(prog=NAME)
    # Platform
    add_platform_group(parser)

    commands = parser.add_subparsers(title='COMMAND')
    instance_parser = commands.add_parser('instance')
    add_instance_cli(instance_parser)

    cluster_parser = commands.add_parser('cluster')
    add_cluster_cli(cluster_parser)

    job_parser = commands.add_parser('job')
    add_job_cli(job_parser)
    return parser.parse_args()


if __name__ == "__main__":
    args = cli()
    if args:
        run(args)
