from corc.core.storage.defaults import SUPPORTED_STORAGE_PROVIDERS


def valid_storage_group(parser):
    add_storage_group(parser)
    delete_storage(parser)
    download_storage(parser)
    select_storage(parser)


def add_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add orchestration provider arguments"
    )
    providers = provider_group.add_argument_group(title="test")

    for storage_provider in SUPPORTED_STORAGE_PROVIDERS:
        providers.add_argument(storage_provider)


def remove_provider_group(parser):
    provider_group = parser.add_argument_group(
        title="Add orchestration provider arguments"
    )
    providers = provider_group.add_argument_group(title="test")

    # TODO, only list the providers that are actually installed
    for storage_provider in SUPPORTED_STORAGE_PROVIDERS:
        providers.add_argument(storage_provider)


def add_storage_group(parser):
    storage_group = parser.add_argument_group(title="Storage arguments")
    storage_group.add_argument("--storage-enable", action="store_true")
    storage_group.add_argument("--storage-credentials-path", default="")
    storage_group.add_argument("--storage-upload-path", default="")
    storage_group.add_argument("--storage-input-path", default="")
    storage_group.add_argument("--storage-output-path", default="")


def delete_storage(parser):
    delete_storage_group = parser.add_argument_group(title="Storage Delete arguments")
    delete_method = delete_storage_group.add_mutually_exclusive_group()
    delete_method.add_argument(
        "--storage-delete-all", action="store_true", default=False
    )
    delete_method.add_argument("--storage-delete-id", default="")
    delete_method.add_argument("--storage-delete-prefix", default="")


def download_storage(parser):
    get_storage_group = parser.add_argument_group(title="Storage Download arguments")
    get_storage_group.add_argument("--storage-download-path", default="")


def select_storage(parser):
    storage_group = parser.add_argument_group(title="Storage Selection arguments")
    storage_group.add_argument("--storage-endpoint", default="")
