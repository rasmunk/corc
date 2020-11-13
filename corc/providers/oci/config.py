import flatten_dict
from corc.config import recursive_check_config
from corc.defaults import (
    CLUSTER,
    CLUSTER_NODE,
    INSTANCE,
    VCN,
    VCN_SUBNET,
    VCN_INTERNETGATEWAY,
    VCN_ROUTETABLE,
    VCN_ROUTETABLE_ROUTERULES,
    PROFILE,
)

valid_cluster_node_config = {
    "id": str,
    "name": str,
    "availability_domain": str,
    "size": int,
    "node_shape": str,
    "image": (str, dict),
}

default_cluster_node_config = {
    "id": "",
    "name": "NodePool",
    "availability_domain": "",
    "size": 1,
    "node_shape": "VM.Standard2.1",
    "image": "Oracle-Linux-7.8-2020.09.23-0",
}


default_cluster_config = {
    "name": "cluster",
    "kubernetes_version": "",
    "domain": "",
    "image": "nielsbohr/mccode-job-runner:latest",
    "node": default_cluster_node_config,
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
    "shape": "VM.Standard2.1",
}

valid_instance_config = {
    "ssh_authorized_keys": list,
    "availability_domain": str,
    "operating_system": str,
    "operating_system_version": str,
    "shape": str,
}

default_subnet_config = {
    "id": "",
    "display_name": "worker_subnet",
    "dns_label": "workers",
    "cidr_block": "10.0.1.0/24",
}

valid_subnet_config = {
    "id": str,
    "display_name": str,
    "dns_label": str,
    "cidr_block": str,
}

default_internet_gateway_config = {
    "id": "",
    "display_name": "default_gateway",
    "is_enabled": True,
}

valid_internet_gateway_config = {
    "id": str,
    "display_name": str,
    "is_enabled": bool,
}

default_route_rule_config = {
    "id": "",
    "cidr_block": None,
    "destination": "0.0.0.0/0",
    "destination_type": "CIDR_BLOCK",
}

valid_route_rule_config = {
    "id": str,
    "cidr_block": (str, None),
    "destination": str,
    "destination_type": str,
}

default_route_table_config = {
    "id": "",
    "display_name": "default_route_table",
    "routerules": [default_route_rule_config],
}

valid_route_table_config = {
    "id": str,
    "display_name": str,
    "routerules": list,
}

default_vcn_config = {
    "id": "",
    "dns_label": "vcn",
    "display_name": "VCN Network",
    "cidr_block": "10.0.0.0/16",
    "subnet": default_subnet_config,
    "internetgateway": default_internet_gateway_config,
    "routetable": default_route_table_config,
}

valid_vcn_config = {
    "id": str,
    "dns_label": str,
    "display_name": str,
    "cidr_block": str,
    "subnet": dict,
    "internetgateway": dict,
    "routetable": dict,
}

default_profile_config = {"name": "DEFAULT", "compartment_id": ""}

valid_profile_config = {"name": str, "compartment_id": str}

default_config = {
    "cluster": default_cluster_config,
    "instance": default_instance_config,
    "vcn": default_vcn_config,
    # "network": default_network_config,
    "profile": default_profile_config,
}

default_oci_config = {"oci": default_config}

valid_full_oci_config = {
    "cluster": valid_cluster_config,
    "instance": valid_instance_config,
    "vcn": valid_vcn_config,
    "profile": valid_profile_config,
}

oci_config_groups = {
    CLUSTER: valid_cluster_config,
    CLUSTER_NODE: valid_cluster_node_config,
    INSTANCE: valid_instance_config,
    VCN: valid_vcn_config,
    VCN_SUBNET: valid_subnet_config,
    VCN_INTERNETGATEWAY: valid_internet_gateway_config,
    VCN_ROUTETABLE: valid_route_table_config,
    VCN_ROUTETABLE_ROUTERULES: valid_route_rule_config,
    PROFILE: valid_profile_config,
}


def generate_oci_config(overwrite_with_empty=False, **kwargs):
    config = default_oci_config
    if kwargs:
        flat = flatten_dict.flatten(config)
        other_flat = flatten_dict.flatten(kwargs)
        for k, v in other_flat.items():
            if not v and overwrite_with_empty:
                flat[k] = v
            if v:
                flat[k] = v
        config = flatten_dict.unflatten(flat)
    return config


def valid_oci_config(config, verbose=False):
    if not isinstance(config, dict):
        return False

    if "oci" not in config:
        return False

    return recursive_check_config(config["oci"], valid_full_oci_config, verbose=verbose)


def load_config_groups(**kwargs):
    return oci_config_groups
