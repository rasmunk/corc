import copy
from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
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
from oci_helpers import (
    new_client,
    create,
    delete,
    get,
    list_entities,
    get_kubernetes_version,
)
from orchestrator import OCIOrchestrator, OCITask
from network import (
    new_vcn_stack,
    get_vcn_stack,
    valid_vcn_stack,
    get_vcn_by_name,
    delete_vcn_stack,
)
from args import get_arguments, OCI, CLUSTER


CLUSTER = "CLUSTER"

# FIXME, no node_pools should be allowed
def valid_cluster_stack(stack):

    if not isinstance(stack, dict):
        raise TypeError("The Cluster stack must be a dictionary to be valid")

    expected_fields = ["cluster", "node_pools"]
    for field in expected_fields:
        if field not in stack:
            return False
        # Value can't be None/False
        if not stack[field]:
            return False
    return True


def new_cluster_stack(
    container_engine_client,
    create_cluster_details,
    create_node_pool_details,
    discover_vcn=False,
):
    stack = dict(cluster=None, node_pools=[])
    cluster = create_cluster(container_engine_client, create_cluster_details)

    if not cluster:
        # Cluster is required to setup the node pool
        return stack

    stack["cluster"] = cluster
    create_node_pool_details.cluster_id = cluster.id

    print(create_node_pool_details)

    node_pool = create_node_pool(container_engine_client, create_node_pool_details)

    if node_pool:
        stack["node_pools"].append(node_pool)

    return stack


# def update_cluster_stack(
#     container_engine_client,
#     create_cluster_details,
#     create_node_pool_details
#     ):

#     stack = dict(cluster=None, node_pools=[])

#     cluster = update_cluster


def get_cluster_stack(container_engine_client, compartment_id, cluster_id):

    stack = dict(cluster=None, node_pools=[])

    cluster = get(container_engine_client, "get_cluster", cluster_id)
    if not cluster:
        return stack

    stack["cluster"] = cluster

    # Get node pools
    node_pools = list_entities(
        container_engine_client,
        "list_node_pools",
        compartment_id,
        cluster_id=cluster.id,
    )

    if node_pools:
        stack["node_pools"].extend(node_pools)

    return stack


def delete_cluster_stack(container_engine_client, cluster_id, delete_vcn=False):
    # TODO, delete associate Node Pool
    cluster = get(container_engine_client, "get_cluster", cluster_id)
    if not cluster:
        return False

    return delete_cluster(container_engine_client, cluster_id)


def delete_cluster(container_engine_client, cluster_id, **kwargs):
    return delete(
        container_engine_client,
        "delete_cluster",
        cluster_id,
        wait_for_states=[WorkRequest.STATUS_SUCCEEDED, WorkRequest.STATUS_FAILED],
        **kwargs,
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


def get_cluster_by_name(
    container_engine_client, compartment_id, name, lifecycle_state=None
):
    if not lifecycle_state:
        lifecycle_state = [Cluster.LIFECYCLE_STATE_ACTIVE]
    clusters = list_entities(
        container_engine_client,
        "list_clusters",
        compartment_id=compartment_id,
        name=name,
        lifecycle_state=lifecycle_state,
    )
    if clusters:
        return clusters[0]
    return None


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
    cluster_kwargs = {
        k: v for k, v in kwargs.items() if hasattr(CreateClusterDetails, k)
    }
    create_cluster_details = CreateClusterDetails(**cluster_kwargs)
    return create_cluster_details


def _prepare_node_pool_placement_config(**kwargs):
    node_pool_kwargs = {
        k: v for k, v in kwargs.items() if hasattr(NodePoolPlacementConfigDetails, k)
    }

    return NodePoolPlacementConfigDetails(**node_pool_kwargs)


def _prepare_create_node_pool_config(**kwargs):
    create_node_pool_config_kwargs = {
        k: v for k, v in kwargs.items() if hasattr(CreateNodePoolNodeConfigDetails, k)
    }
    return CreateNodePoolNodeConfigDetails(**create_node_pool_config_kwargs)


def _prepare_create_node_pool_details(**kwargs):
    create_node_pool_details = {
        k: v for k, v in kwargs.items() if hasattr(CreateNodePoolDetails, k)
    }
    return CreateNodePoolDetails(**create_node_pool_details)


def _gen_cluster_stack_details(vnc_id, subnets, kubernetes_version, **options):
    cluster_details = {}

    create_cluster_details = _prepare_create_cluster_details(
        vcn_id=vnc_id,
        kubernetes_version=kubernetes_version,
        **options["oci"],
        **options["cluster"],
    )
    cluster_details["create_cluster"] = create_cluster_details

    node_pool_place_configs = []
    if subnets:
        for subnet in subnets:
            node_pool_place_configs.append(
                _prepare_node_pool_placement_config(
                    subnet_id=subnet.id, **options["node"]
                )
            )

    node_config_details = _prepare_create_node_pool_config(
        size=options["node"]["size"], placement_configs=node_pool_place_configs,
    )

    create_node_pool_details = _prepare_create_node_pool_details(
        node_config_details=node_config_details,
        kubernetes_version=kubernetes_version,
        **options["oci"],
        **options["node"],
    )
    cluster_details["create_node_pool"] = create_node_pool_details

    return cluster_details


class OCIClusterOrchestrator(OCIOrchestrator):
    def __init__(self, options):
        super().__init__(options)
        # Set client
        self.container_engine_client = new_client(
            ContainerEngineClient,
            composite_class=ContainerEngineClientCompositeOperations,
            profile_name=options["oci"]["profile_name"],
        )
        self.network_client = new_client(
            VirtualNetworkClient,
            composite_class=VirtualNetworkClientCompositeOperations,
            profile_name=options["oci"]["profile_name"],
        )

        self.cluster_stack = None
        self.vcn_stack = None

    def _get_vcn_stack(self):
        stack = {}
        vcn = get_vcn_by_name(
            self.network_client,
            self.options["oci"]["compartment_id"],
            self.options["vcn"]["display_name"],
        )
        if vcn:
            stack = get_vcn_stack(
                self.network_client, self.options["oci"]["compartment_id"], vcn.id
            )
        return stack

    def _new_vcn_stack(self):
        stack = new_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
        )
        return stack

    def prepare(self):

        # Ensure we have a VCN stack ready
        vcn_stack = self._get_vcn_stack()
        if not vcn_stack:
            vcn_stack = self._new_vcn_stack()

        if valid_vcn_stack(vcn_stack):
            self.vcn_stack = vcn_stack
        else:
            raise ValueError("Did not receive a proper VCN stack: {}".format(vcn_stack))

        kubernetes_version = get_kubernetes_version(self.container_engine_client)
        cluster_details = _gen_cluster_stack_details(
            self.vcn_stack["vcn"].id,
            self.vcn_stack["subnets"],
            kubernetes_version,
            **self.options,
        )

        cluster = get_cluster_by_name(
            self.container_engine_client,
            self.options["oci"]["compartment_id"],
            self.options["cluster"]["name"],
        )
        if not cluster:
            self._is_ready = False
            # Ensure that we don't change the state options
            options = copy.deepcopy(self.options)

            cluster_stack = new_cluster_stack(
                self.container_engine_client,
                cluster_details["create_cluster"],
                cluster_details["create_node_pool"],
            )
            if valid_cluster_stack(cluster_stack):
                self.cluster_stack = cluster_stack
            else:
                raise ValueError(
                    "The new cluster stack: {} is not valid".format(cluster_stack)
                )
        else:
            cluster_stack = get_cluster_stack(
                self.container_engine_client,
                self.options["oci"]["compartment_id"],
                cluster.id,
            )
            if valid_cluster_stack(cluster_stack):
                self.cluster_stack = cluster_stack

        if self.cluster_stack:
            self._is_ready = True

    def tear_down(self):
        if self.vcn_stack:
            vcn_stack_deleted = delete_vcn_stack(
                self.network_client,
                self.options["oci"]["compartment_id"],
                vcn_id=self.vcn_stack["vcn"].id,
            )
            # TODO, handle better
            if not vcn_stack_deleted:
                return False

        if self.cluster_stack:
            cluster = self.cluster_stack["cluster"]
            deleted = delete_cluster_stack(self.container_engine_client, cluster.id)
            if deleted:
                self._is_ready = False
                self.cluster_stack = None
        else:
            self._is_ready = False
            self.cluster_stack = None

    # Use kubernetes to schedule the task in the cluster
    # def schedule(self, job):
    #     v1 = client.CoreV1Api()
    #     ret = v1.list_pod_for_all_namespaces(watch=False)

    #     # Create kubernetes job

    #     v1.deployment

    @classmethod
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise ValueError("options is not a dictionary")

        expected_oci_keys = [
            "compartment_id",
            "profile_name",
        ]

        expected_cluster_keys = [
            "name",
        ]

        expected_node_keys = [
            "availability_domain",
            "name",
            "size",
            "node_shape",
            "node_image_name",
        ]

        expected_vcn_keys = ["cidr_block", "display_name"]

        # TODO, this and vcn cidr_block should be optional
        optional_subnet_keys = ["cidr_block"]

        expected_groups = {
            "oci": expected_oci_keys,
            "cluster": expected_cluster_keys,
            "node": expected_node_keys,
            "vcn": expected_vcn_keys,
        }

        for group, keys in expected_groups.items():
            if group not in options:
                raise KeyError("Missing group: {}".format(group))

            if not isinstance(options[group], dict):
                raise TypeError("Group: {} must be a dictionary".format(group))

            for key, _ in options[group].items():
                if key not in keys:
                    raise KeyError("Incorrect key: {} is not in: {}".format(key, keys))


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
