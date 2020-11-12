import boto3
import botocore
import copy
import os


required_s3_fields = {
    "config_file": str,
    "credentials_file": str,
    "name": str,
}

required_s3_values = {
    "config_file": True,
    "credentials_file": True,
    "name": True,
}

required_s3_bucket_fields = {
    "bucket_name": str,
    "bucket_input_prefix": str,
    "bucket_output_prefix": str,
}

required_s3_bucket_values = {
    "bucket_name": True,
    "bucket_input_prefix": False,
    "bucket_output_prefix": False,
}


def upload_to_s3(s3_client, local_path, s3_path, bucket_name):
    if not os.path.exists(local_path):
        return False
    s3_client.upload_file(local_path, bucket_name, s3_path)
    return True


def upload_directory_to_s3(client, path, bucket_name, s3_prefix="output"):
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
            try:
                client.upload_file(local_path, bucket_name, s3_path)
            except Exception:
                return False
    return True


def bucket_exists(s3_client, bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except botocore.exceptions.ClientError:
        pass
    return False


def create_bucket(s3_client, bucket_name, **kwargs):
    bucket = s3_client.create_bucket(Bucket=bucket_name, **kwargs)
    if not bucket:
        return False
    return bucket


def delete_bucket(s3_client, bucket_name, **kwargs):
    return s3_client.delete_bucket(Bucket=bucket_name, **kwargs)


def delete_objects(s3_resource, bucket_name, s3_prefix="", max_chunk_size=1000):
    bucket = s3_resource.Bucket(bucket_name)
    objects_keys = [
        {"Key": str(obj.key)} for obj in bucket.objects.filter(Prefix=s3_prefix)
    ]

    if not objects_keys:
        return {}

    print(len(objects_keys))
    num_delete = len(objects_keys)

    if num_delete > max_chunk_size:
        delete_chunks = [
            objects_keys[i : i + max_chunk_size]
            for i in range(0, num_delete, max_chunk_size)
        ]
        for idx, chunk_keys in enumerate(delete_chunks):
            s3_resource.meta.client.delete_objects(
                Bucket=bucket_name, Delete={"Objects": chunk_keys}
            )

    return s3_resource.meta.client.delete_objects(
        Bucket=bucket_name, Delete={"Objects": objects_keys}
    )


# Accept parameters to
def expand_s3_bucket(s3_resource, bucket_name, target_dir=None, s3_prefix="input"):
    """ Expands the content of the specified bucket into the target_dir """
    bucket = s3_resource.Bucket(bucket_name)
    for obj in bucket.objects.filter(Prefix=s3_prefix):
        obj_path = copy.deepcopy(obj.key)
        if s3_prefix:
            obj_path = os.path.relpath(obj_path, s3_prefix)

        if target_dir:
            full_path = os.path.join(target_dir, obj_path)
        else:
            full_path = obj_path
        dir_path = os.path.dirname(full_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        bucket.download_file(obj.key, full_path)
    return True


def list_objects(s3_resource, bucket_name, all_objects=True, **kwargs):
    finished = False
    results = []
    last_object = None
    while not finished:
        response = None
        if last_object:
            response = s3_resource.meta.client.list_objects_v2(
                Bucket=bucket_name, StartAfter=last_object["Key"], **kwargs
            )
        else:
            response = s3_resource.meta.client.list_objects_v2(
                Bucket=bucket_name, **kwargs
            )

        if response and "Contents" in response:
            results.extend(response["Contents"])

        if not all_objects:
            finished = True
        else:
            if response and "Contents" in response and response["IsTruncated"]:
                last_object = response["Contents"][-1]
            else:
                finished = True
    return results


def stage_s3_resource(**kwargs):
    return boto3.resource("s3", **kwargs)
