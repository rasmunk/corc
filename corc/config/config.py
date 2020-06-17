import os
import strictyaml import load


valid_config = {
    'cluster': {
        'image': str,
        "id": str,
        "name": str,
        "kubernetes-version": str,
        "domain": str
        "node": {
            "id": str,
            "name": str,
            "availability-domain": str,
            "size": int,
            "shape": str,
            "image": str
        }
    },
    'configurer': {
        "root_path": str,
        "playbook_path": str,
        "inventory_path": str
    },
    'instance': {
        "ssh-authorized_keys": list,
        "availability-domain": str,
        "operating_system": str,
        "operating_system_version": str,
        "target_shape": str
    },
    'job': {
        "meta": {
            "name": str,
            "debug": str,
            "env_override": str,
            "num_jobs": int
            "num_parallel": int
        },
        "command": str,
        "args": list,
        "capture": bool,
        "output_path": str
    },
    'network': {
        "subnet": {
            "id": str,
            "dns_label": str,
            "cidr_block": str
        },
        "vcn": {
            "id": str,
            "dns_label": str,
            "display_name": str,
            "cidr_block": str
        }
    },
    "platform": {
        "profile_name": str,
        "compartment_id": str
    },
    "storage": {
        "s3": {
            "config_file": str,
            "credentials_file": str,
            "profile_name": str,
            "bucket_id": str,
            "bucket_name": str,
            "bucket_input_prefix": str,
            "bucket_output_prefix": str,
        },
        "endpoint": str,
        "download_path": str
    }
}


def load_config(path):
    config = {}
    if not os.path.exists(path):
        return config

    config = load(path)
    return config

