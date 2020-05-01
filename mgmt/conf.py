import argparse


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-name", default="DEFAULT")
    parser.add_argument("--compartment-id", default=False)
    parser.add_argument("--ssh-authorized-keys", nargs='+', default=[])
    return parser.parse_args()
