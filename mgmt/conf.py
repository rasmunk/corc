import argparse


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-name", default="DEFAULT")
    parser.add_argument("--compartment-id", default=False)
    parser.add_argument("--ssh-authorized-keys", nargs='+', default=[])
    parser.add_argument("--vm-ip", default=False)
    parser.add_argument("--operating-system", default="CentOS")
    parser.add_argument("--operating-system-version", default="7")
    parser.add_argument("--target-shape", default="VM.Standard2.1")
    return parser.parse_args()
