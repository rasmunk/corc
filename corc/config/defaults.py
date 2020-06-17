default_cluster_config = {"name": "cluster", "kubernetes_version": "", "domain": ""}

default_configurer_config = {}

default_instance_config = {
    "ssh_authorized_keys": [],
    "availability_domain": "",
    "operating_system": "CentOS",
    "operating_system_version": "7",
    "target_shape": "VM.Standard2.1",
}

default_job_config = {
    "meta": {
        "name": "",
        "debug": False,
        "env_override": True,
        "num_jobs": 1,
        "num_parallel": 1,
    },
    "capture": True,
    "output_path": "/tmp/output",
}

default_network_config = {
    "subnet": {"id": "", "dns_label": None, "cidr_block": "10.0.1.0/24"},
    "vcn": {
        "id": "",
        "dns_label": None,
        "display_name": "VCN Network",
        "cidr_block": "10.0.0.0/16",
    },
}

default_platform_config = {"oci": {"profile_name": "DEFAULT", "compartment_id": ""}}

default_storage_config = {
    "s3": {
        "config_file": "~/.aws/config",
        "credentials_file": "~/.aws/credentials",
        "profile_name": "default",
        "bucket_id": "",
        "bucket_name": "",
        "bucket_input_prefix": "input",
        "bucket_output_prefix": "output",
    },
    "endpoint": "",
    "credentials_path": "/mnt/creds",
    "upload_path": "",
    "input_path": "/tmp/input",
    "output_path": "/tmp/output",
    "download_path": "",
}


default_config = {
    "cluster": default_cluster_config,
    "configurer": default_configurer_config,
    "instance": default_instance_config,
    "job": default_job_config,
    "network": default_network_config,
    "platform": default_platform_config,
    "storage": default_storage_config,
}

valid_cluster_config = {
    "image": str,
    "id": str,
    "name": str,
    "kubernetes_version": str,
    "domain": str,
    "node": dict,
}

valid_node_config = {
    "id": str,
    "name": str,
    "availability_domain": str,
    "size": int,
    "shape": str,
    "image": str,
}

valid_configurer_config = {
    "root_path": str,
    "playbook_path": str,
    "inventory_path": str,
}

valid_instance_config = {
    "ssh_authorized_keys": list,
    "availability_domain": str,
    "operating_system": str,
    "operating_system_version": str,
    "target_shape": str,
}


valid_job_config = {
    "meta": {
        "name": str,
        "debug": bool,
        "env_override": bool,
        "num_jobs": int,
        "num_parallel": int,
    },
    "command": str,
    "args": list,
    "capture": bool,
    "output_path": str,
}


valid_network_config = {
    "subnet": {"id": str, "dns_label": str, "cidr_block": str},
    "vcn": {"id": str, "dns_label": str, "display_name": str, "cidr_block": str},
}

valid_platform_config = {"profile_name": str, "compartment_id": str}

valid_s3_config = {
    "config_file": str,
    "credentials_file": str,
    "profile_name": str,
    "bucket_id": str,
    "bucket_name": str,
    "bucket_input_prefix": str,
    "bucket_output_prefix": str,
}

valid_storage_config = {
    "s3": dict,
    "endpoint": str,
    "credentials_path": str,
    "upload_path": str,
    "input_path": str,
    "output_path": str,
    "download_path": str,
}


valid_corc_config = {
    "cluster": valid_cluster_config,
    "configurer": valid_configurer_config,
    "instance": valid_instance_config,
    "job": valid_job_config,
    "network": valid_network_config,
    "platform": valid_platform_config,
    "storage": valid_storage_config,
}
