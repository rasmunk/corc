# from corc.cli.parser import ParseKwargs


def valid_s3_group(parser):
    add_s3_group(parser)
    select_s3_group(parser)
    s3_config_group(parser)
    list_s3_group(parser)
    s3_extra(parser)


def s3_config_group(parser):
    s3_config = parser.add_argument_group(title="S3 Config arguments")
    s3_config.add_argument("--storage-s3-config-file", default="")
    s3_config.add_argument("--storage-s3-credentials-file", default="")
    s3_config.add_argument("--storage-s3-name", default="")


def select_s3_group(parser):
    s3_group = parser.add_argument_group(title="S3 Selection arguments")
    s3_group.add_argument("--storage-s3-bucket-id", default="")
    s3_group.add_argument("--storage-s3-bucket-name", default="")


def add_s3_group(parser):
    s3 = parser.add_argument_group(title="S3 arguments")
    s3.add_argument("--storage-s3-bucket-input-prefix", default="")
    s3.add_argument("--storage-s3-bucket-output-prefix", default="")


def list_s3_group(parser):
    s3_list = parser.add_argument_group(title="S3 List arguments")
    s3_list.add_argument("--storage-s3-all", default=False, type=bool)


def s3_extra(parser):
    pass


#    s3_extra = parser.add_argument_group(title="S3 Extra arguments")
#    s3_extra.add_argument("--storage-s3-extra-kwargs", nargs="*", action=ParseKwargs)
