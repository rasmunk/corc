# TODO, rename to `stage_endpoint` and `staging_path`
required_staging_fields = {
    "endpoint": str,
    "credentials_path": str,
    "upload_path": str,
    "input_path": str,
    "output_path": str,
}

required_staging_values = {
    "endpoint": True,
    "credentials_path": True,
    "upload_path": False,
    "input_path": False,
    "output_path": True,
}