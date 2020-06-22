from corc.cli.parsers.job.result import results_group


def valid_job_group(parser):
    results_group(parser)
    job_meta_group(parser)
    job_group(parser)


def select_job_group(parser):
    job_group = parser.add_argument_group(title="Job Identity arguments")
    job_group.add_argument("--meta-name", type=str, default="")


def job_meta_group(parser):
    job_group = parser.add_argument_group(title="Job Meta arguments")
    job_group.add_argument("--meta-debug", action="store_true")
    job_group.add_argument("--meta-env-override", action="store_true")
    job_group.add_argument("--meta-num-jobs", type=int)
    job_group.add_argument("--meta-num-parallel", type=int)


def job_group(parser):
    job_group = parser.add_argument_group(title="Job Execute arguments")
    job_group.add_argument("job_command", type=str, default="")
    job_group.add_argument("--job-args", nargs="*", default=[])
    job_group.add_argument("--job-capture", action="store_true")
    job_group.add_argument("--job-output-path", type=str, default="")
