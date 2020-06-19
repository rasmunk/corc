default_cluster_config = {"name": "cluster", "kubernetes_version": "", "domain": ""}

default_instance_config = {
    "ssh_authorized_keys": [],
    "availability_domain": "",
    "operating_system": "CentOS",
    "operating_system_version": "7",
    "target_shape": "VM.Standard2.1",
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

default_profile_config = {"profile_name": "DEFAULT", "compartment_id": ""}

default_config = {
    "cluster": default_cluster_config,
    "instance": default_instance_config,
    "network": default_network_config,
    "profile": default_profile_config,
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

valid_instance_config = {
    "ssh_authorized_keys": list,
    "availability_domain": str,
    "operating_system": str,
    "operating_system_version": str,
    "target_shape": str,
}

valid_network_config = {
    "subnet": {"id": str, "dns_label": str, "cidr_block": str},
    "vcn": {"id": str, "dns_label": str, "display_name": str, "cidr_block": str},
}

valid_profile_config = {"profile_name": str, "compartment_id": str}

valid_oci_config = {
    "cluster": valid_cluster_config,
    "instance": valid_instance_config,
    "network": valid_network_config,
    "profile": valid_profile_config,
}


def generate_oci_config(**kwargs):
    # TODO, validate kwargs
    # TODO, update default config with kwargs
    return default_config
