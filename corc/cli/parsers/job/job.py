from corc.cli.parsers.job.result import results_group


def valid_job_group(parser):
    results_group(parser)
    job_meta_group(parser)
    job_group(parser)


def select_job_group(parser, required=True):
    job_group = parser.add_argument_group(title="Job Identity arguments")
    job_group.add_argument("--job-name", default="", required=required)


def job_meta_group(parser):
    job_group = parser.add_argument_group(title="Job Meta arguments")
    job_group.add_argument("--job-debug", action="store_true", default=False)
    job_group.add_argument("--job-env-override", action="store_true", default=True)
    job_group.add_argument("--job-num-jobs", default=1, type=int)
    job_group.add_argument("--job-num-parallel", default=1, type=int)


def job_group(parser):
    job_group = parser.add_argument_group(title="Job Execute arguments")
    job_group.add_argument("job_command", default="")
    job_group.add_argument("--job-name", default="")
    job_group.add_argument("--job-args", nargs="*", default="")
    job_group.add_argument("--job-capture", action="store_true", default=True)
    job_group.add_argument("--job-output-path", default="/tmp/output")
