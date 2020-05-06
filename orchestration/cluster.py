from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from oci.container_engine.models import Cluster, CreateClusterDetails, WorkRequest
from oci.container_engine.models import (
    NodePool,
    CreateNodePoolDetails,
    NodePoolPlacementConfigDetails,
    CreateNodePoolNodeConfigDetails,
)
from kubernetes import client, config
from .oci_helpers import new_client, create, delete, get, list_entities
from .orchestrator import OCIOrchestrator, OCITask
from .args import get_arguments, OCI, CLUSTER


CLUSTER = "CLUSTER"


def new_cluster_stack(
    container_engine_client, create_cluster_details, create_node_pool_details
):
    stack = {"cluster": None, "node_pool": None}

    cluster = create_cluster(container_engine_client, create_cluster_details)

    if not cluster:
        # Cluster is required to setup the node pool
        return stack

    stack["cluster"] = cluster
    create_node_pool_details.cluster_id = cluster.id

    node_pool = create_node_pool(container_engine_client, create_node_pool_details)

    if node_pool:
        stack["node_pool"] = node_pool

    return stack


def delete_cluster_stack(container_engine_client, cluster_id, delete_vcn=False):
    # TODO, delete associate Node Pool
    cluster = get(container_engine_client, "get_cluster", cluster_id)
    if not cluster:
        return False

    return delete_cluster(container_engine_client, cluster_id)


def delete_cluster(container_engine_client, cluster_id, **kwargs):
    return delete(
        container_engine_client, "delete_cluster", Cluster, cluster_id, **kwargs
    )


def create_cluster(container_engine_client, create_cluster_details):
    cluster = create(
        container_engine_client,
        "create_cluster",
        wait_for_states=[WorkRequest.STATUS_SUCCEEDED, WorkRequest.STATUS_FAILED],
        create_cluster_details=create_cluster_details,
    )

    if not cluster:
        return None
    return cluster


def get_cluster_by_name(container_engine_client, name, life_cycle_state=None):
    if not life_cycle_state:
        life_cycle_state = [Cluster.LIFECYCLE_STATE_ACTIVE]

    clusters = list_entities(
        container_engine_client,
        "list_clusters",
        life_cycle_state=life_cycle_state,
        name=name,
    )


def delete_node_pool(container_engine_client, cluster_id, **kwargs):
    return delete(container_engine_client, "delete_node_pool", cluster_id, **kwargs)


def create_node_pool(container_engine_client, create_node_pool_details):
    node_pool = create(
        container_engine_client,
        "create_node_pool",
        wait_for_states=[WorkRequest.STATUS_SUCCEEDED, WorkRequest.STATUS_FAILED],
        create_node_pool_details=create_node_pool_details,
    )
    if not node_pool:
        return None

    return node_pool


def _prepare_create_cluster_details(**kwargs):
    create_cluster_details = CreateClusterDetails(**kwargs)
    return create_cluster_details


def _prepare_node_pool_details(**kwargs):
    node_pool_placement = NodePoolPlacementConfigDetails(**kwargs)
    return node_pool_placement


class OCIClusterOrchestrator(OCIOrchestrator):
    def __init__(self, config):
        super().__init__(config)
        OCIClusterOrchestrator.validate_config(self.config)
        # Set client
        self.client = new_client(
            ContainerEngineClient,
            composite_class=ContainerEngineClientCompositeOperations,
            profile_name=config["profile_name"],
        )
        self.cluster = None

    def prepare(self):
        cluster = get_cluster_by_name(self.client, self.config["name"])
        if not cluster:
            self.is_ready = False
            create_cluster_details = _prepare_create_cluster_details(**self.config)
            create_node_pool_details = _prepare_create_node_pool_details(**self.config)
            cluster = new_cluster_stack(
                self.client, create_cluster_details, create_node_pool_details
            )
            if not cluster:
                return self.is_ready
            self.is_ready = True
        return self.id_ready

    def tear_down(self):
        deleted = delete_cluster_stack(self.client, self.cluster.id)
        if deleted:
            self.is_ready = False

    # Use kubernetes to schedule the task in the cluster
    # def schedule(self, job):
    #     v1 = client.CoreV1Api()
    #     ret = v1.list_pod_for_all_namespaces(watch=False)

    #     # Create kubernetes job

    #     v1.deployment

    @classmethod
    def validate_config(cls, config):
        if not isinstance(config, dict):
            raise ValueError("config is not a dictionary")

        expected_fields = [
            "compartment_id",
            "profile_name",
            "name",
            "availability_domain",
            "size",
        ]

        for field in expected_fields:
            if field not in config:
                raise ValueError(
                    "Missing field: {} in config: {}".format(field, config)
                )


# def create_job_object():
#     # Configureate Pod template container
#     container = client.V1Container(
#         name="pi",
#         image="perl",
#         command=["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"])
#     # Create and configurate a spec section
#     template = client.V1PodTemplateSpec(
#         metadata=client.V1ObjectMeta(labels={"app": "pi"}),
#         spec=client.V1PodSpec(restart_policy="Never", containers=[container]))
#     # Create the specification of deployment
#     spec = client.V1JobSpec(
#         template=template,
#         backoff_limit=4)
#     # Instantiate the job object
#     job = client.V1Job(
#         api_version="batch/v1",
#         kind="Job",
#         metadata=client.V1ObjectMeta(name=JOB_NAME),
#         spec=spec)

#     return job


# def create_job(api_instance, job):
#     api_response = api_instance.create_namespaced_job(
#         body=job,
#         namespace="default")
#     print("Job created. status='%s'" % str(api_response.status))


# def update_job(api_instance, job):
#     # Update container image
#     job.spec.template.spec.containers[0].image = "perl"
#     api_response = api_instance.patch_namespaced_job(
#         name=JOB_NAME,
#         namespace="default",
#         body=job)
#     print("Job updated. status='%s'" % str(api_response.status))


# def delete_job(api_instance):
#     api_response = api_instance.delete_namespaced_job(
#         name=JOB_NAME,
#         namespace="default",
#         body=client.V1DeleteOptions(
#             propagation_policy='Foreground',
#             grace_period_seconds=5))
#     print("Job deleted. status='%s'" % str(api_response.status))
