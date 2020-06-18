def results_group(parser):
    results_group = parser.add_argument_group(title="Job Result arguments")
    results_group.add_argument("--job-result-all", action="store_true", default=True)
    results_group.add_argument("--job-result-prefix", default="")
