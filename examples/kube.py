import sys
import os

# Import base
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_path, "orchestration"))
sys.path.append(base_path)

from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from kubernetes import client
from cluster import refresh_kube_config, new_client, get_cluster_by_name
from orchestration.kubernetes.scheduler import KubenetesScheduler
from orchestration.kubernetes.job import prepare_job, create_job
from orchestration.kubernetes.nodes import list_nodes

if __name__ == "__main__":
    profile_name = "XNOVOTECH"
    # Extract OCI cluster id
    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        profile_name=profile_name,
    )

    compartment_id = "ocid1.tenancy.oc1..aaaaaaaakfmksyrf7hl2gfexmjpb6pbyrirm6k3ro7wd464y2pr7atpxpv4q"
    cluster_name = "Test XNOVOTECH Cluster"
    cluster = get_cluster_by_name(
        container_engine_client, compartment_id, name=cluster_name
    )

    refreshed = refresh_kube_config(cluster.id, profile_name=profile_name)
    if not refreshed:
        exit(1)

    kub_client = client.CoreV1Api()

    # Save in shelve the last selected

    nodes = list_nodes(kub_client)

    print(n)
