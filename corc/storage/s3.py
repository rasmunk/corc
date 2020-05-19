import botocore
import os

required_s3_fields = {
    "bucket_name": str,
    "bucket_input_prefix": str,
    "bucket_output_prefix": str,
    "config_file": str,
    "credentials_file": str,
    "profile_name": str,
}

required_s3_values = {
    "bucket_name": False,
    "bucket_input_prefix": False,
    "bucket_output_prefix": False,
    "config_file": True,
    "credentials_file": True,
    "profile_name": True,
}


def upload_to_s3(s3_client, local_path, s3_path, bucket_name):
    if not os.path.exists(local_path):
        return False
    s3_client.upload_file(local_path, bucket_name, s3_path)
    return True


def upload_directory_to_s3(client, path, bucket_name, s3_prefix="input"):
    if not os.path.exists(path):
        return False
    for root, dirs, files in os.walk(path):
        for filename in files:
            local_path = os.path.join(root, filename)
            # generate s3 dir path
            # Skip the first /
            # HACK
            s3_path = local_path.split(path)[1][1:]
            # Upload
            if s3_prefix:
                s3_path = os.path.join(s3_prefix, s3_path)
            if not client.upload_file(local_path, bucket_name, s3_path):
                return False
    return True


def bucket_exists(s3_client, bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except botocore.exceptions.ClientError:
        pass
    return False
