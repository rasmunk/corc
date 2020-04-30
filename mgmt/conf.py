import argparse


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-name", default="DEFAULT")
    parser.add_argument("--compartment-id", default=False)
    parser.add_argument("--image", default=False)

    return parser.parse_args()
