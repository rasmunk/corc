# TODO, rename to `stage_endpoint` and `staging_path`
required_staging_fields = {
    "enable": bool,
    "endpoint": str,
    "credentials_path": str,
    "upload_path": str,
    "input_path": str,
    "output_path": str,
}

required_staging_values = {
    "enable": True,
    "endpoint": True,
    "credentials_path": True,
    "upload_path": False,
    "input_path": False,
    "output_path": True,
}


required_get_storage_fields = {
    "endpoint": str,
    "download_path": str,
}

required_get_storage_values = {"endpoint": True, "download_path": False}

required_delete_storage_fields = {
    "endpoint": str,
}

required_delete_storage_values = {"endpoint": True}
