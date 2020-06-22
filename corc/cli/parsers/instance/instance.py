def valid_compute_group(parser):
    add_compute_group(parser)


def add_compute_group(parser):
    compute_group = parser.add_argument_group(title="Compute arguments")
    compute_group.add_argument("--compute-ssh-authorized-keys", nargs="+", default=[])
    compute_group.add_argument("--compute-ad", default="")
    compute_group.add_argument("--compute-os", default="CentOS")
    compute_group.add_argument("--compute-os-version", default="7")
    compute_group.add_argument("--compute-target-shape", default="VM.Standard2.1")
