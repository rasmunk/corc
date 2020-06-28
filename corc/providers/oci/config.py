import flatten_dict
from corc.config import recursive_check_config
from corc.defaults import CLUSTER, COMPUTE, VCN, SUBNET, PROFILE


default_cluster_config = {
    "name": "cluster",
    "kubernetes_version": "",
    "domain": "",
    "image": "nielsbohr/mccode-job-runner:latest",
}


valid_cluster_config = {
    "id": str,
    "name": str,
    "kubernetes_version": str,
    "domain": str,
    "node": dict,
    "image": str,
}

default_instance_config = {
    "ssh_authorized_keys": [],
    "availability_domain": "",
    "operating_system": "CentOS",
    "operating_system_version": "7",
    "target_shape": "VM.Standard2.1",
}

valid_instance_config = {
    "ssh_authorized_keys": list,
    "availability_domain": str,
    "operating_system": str,
    "operating_system_version": str,
    "target_shape": str,
}

default_subnet_config = {"id": "", "dns_label": None, "cidr_block": "10.0.1.0/24"}


valid_subnet_config = {"id": str, "dns_label": str, "cidr_block": str}


default_vcn_config = {
    "id": "",
    "dns_label": None,
    "display_name": "VCN Network",
    "cidr_block": "10.0.0.0/16",
}

valid_vcn_config = {"id": str, "dns_label": str, "display_name": str, "cidr_block": str}


default_network_config = {
    "subnet": default_subnet_config,
    "vcn": default_vcn_config,
}

valid_network_config = {"subnet": valid_subnet_config, "vcn": valid_vcn_config}

default_profile_config = {"profile_name": "DEFAULT", "compartment_id": ""}

valid_profile_config = {"profile_name": str, "compartment_id": str}

default_config = {
    "cluster": default_cluster_config,
    "instance": default_instance_config,
    "network": default_network_config,
    "profile": default_profile_config,
}

default_oci_config = {"oci": default_config}

valid_node_config = {
    "id": str,
    "name": str,
    "availability_domain": str,
    "size": int,
    "shape": str,
    "image": str,
}

default_node_config = {
    "id": "",
    "name": "",
    "availability_domain": "",
    "size": 1,
    "shape": "VM.Standard2.1",
    "image": "Oracle-Linux-7.7-2020.03.23-0",
}

valid_full_oci_config = {
    "cluster": valid_cluster_config,
    "instance": valid_instance_config,
    "network": valid_network_config,
    "profile": valid_profile_config,
}

oci_config_groups = {
    CLUSTER: valid_cluster_config,
    COMPUTE: valid_instance_config,
    VCN: valid_vcn_config,
    SUBNET: valid_subnet_config,
    PROFILE: valid_profile_config,
}


def generate_oci_config(**kwargs):
    config = default_oci_config
    if kwargs:
        flat = flatten_dict.flatten(config)
        other_flat = flatten_dict.flatten(kwargs)
        flat.update(other_flat)
        config = flatten_dict.unflatten(flat)
    return config


def valid_oci_config(config, verbose=False):
    if not isinstance(config, dict):
        return False

    if "oci" not in config:
        return False

    return recursive_check_config(config["oci"], valid_full_oci_config, verbose=verbose)
