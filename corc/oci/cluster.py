from oci.core import VirtualNetworkClient, VirtualNetworkClientCompositeOperations
from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from oci.container_engine.models import Cluster, CreateClusterDetails, WorkRequest
from oci.container_engine.models import (
    CreateNodePoolDetails,
    NodePoolPlacementConfigDetails,
    CreateNodePoolNodeConfigDetails,
)

from corc.oci.helpers import (
    new_client,
    create,
    delete,
    get,
    list_entities,
    get_kubernetes_version,
)
from corc.util import parse_yaml
from corc.kubernetes.config import save_kube_config, load_kube_config
from corc.orchestrator import Orchestrator
from corc.oci.network import (
    new_vcn_stack,
    get_vcn_stack,
    valid_vcn_stack,
    get_vcn_by_name,
    delete_vcn_stack,
)


def refresh_kube_config(cluster_id, profile_name="DEFAULT"):
    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        profile_name=profile_name,
    )

    # Try to load the existing
    # Create or refresh the kubernetes config
    kube_config = create(container_engine_client, "create_kubeconfig", cluster_id)
    if kube_config and hasattr(kube_config, "text"):
        config_dict = parse_yaml(kube_config.text)
        # HACK, add profile to user args
        if profile_name:
            profile_args = ["--profile", profile_name]
            config_dict["users"][0]["user"]["exec"]["args"].extend(profile_args)
        if save_kube_config(config_dict):
            loaded = load_kube_config()

    loaded = load_kube_config()
    if not loaded:
        # The new/refreshed config failed to load
        return False
    return True


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
        return stack

    # cluster
    stack["cluster"] = cluster
    create_node_pool_details.cluster_id = cluster.id

    node_pool = create_node_pool(container_engine_client, create_node_pool_details)

    if node_pool:
        stack["node_pools"].append(node_pool)

    return stack


def update_cluster_stack(
    container_engine_client, update_cluster_details, update_node_pool_details
):
    raise NotImplementedError


def get_cluster_stack(
    container_engine_client, compartment_id, cluster_id, node_kwargs=None
):

    if not node_kwargs:
        node_kwargs = dict()

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
        **node_kwargs,
    )

    if node_pools:
        stack["node_pools"].extend(node_pools)

    return stack


def delete_cluster_stack(container_engine_client, cluster_id, delete_vcn=False):
    # Will implicitly delete the node pool as well
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


def create_cluster(container_engine_client, create_cluster_details, create_kwargs=None):
    if not create_kwargs:
        create_kwargs = dict(
            wait_for_states=[
                WorkRequest.STATUS_SUCCEEDED,
                WorkRequest.OPERATION_TYPE_CLUSTER_CREATE,
                WorkRequest.STATUS_FAILED,
            ]
        )

    created_response = create(
        container_engine_client,
        "create_cluster",
        create_cluster_details=create_cluster_details,
        **create_kwargs,
    )

    if not created_response:
        return None

    cluster = None
    # NOTE, only supports a single cluster creation for now
    if created_response.resources:
        cluster_id = created_response.resources[0].identifier
        # Get the actual created cluster
        cluster = get(container_engine_client, "get_cluster", cluster_id)

    return cluster


def get_cluster_by_name(
    container_engine_client, compartment_id, name, cluster_kwargs=None
):
    if not cluster_kwargs:
        cluster_kwargs = dict(lifecycle_state=[Cluster.LIFECYCLE_STATE_ACTIVE])
    clusters = list_entities(
        container_engine_client,
        "list_clusters",
        compartment_id=compartment_id,
        name=name,
        **cluster_kwargs,
    )
    if clusters:
        return clusters[0]
    return None


def delete_node_pool(container_engine_client, cluster_id, **kwargs):
    return delete(container_engine_client, "delete_node_pool", cluster_id, **kwargs)


def create_node_pool(container_engine_client, create_node_pool_details):
    created_response = create(
        container_engine_client,
        "create_node_pool",
        wait_for_states=[
            WorkRequest.STATUS_SUCCEEDED,
            WorkRequest.OPERATION_TYPE_NODEPOOL_CREATE,
            WorkRequest.STATUS_FAILED,
        ],
        create_node_pool_details=create_node_pool_details,
    )
    if not created_response:
        return None

    node_pool = None
    # NOTE, only supports a single cluster creation for now
    if created_response.resources:
        node_pool_id = created_response.resources[0].identifier
        # Get the actual created cluster
        node_pool = get(container_engine_client, "get_node_pool", node_pool_id)

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


class OCIClusterOrchestrator(Orchestrator):
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
        self._is_ready = False

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
            subnet_kwargs=self.options["subnet"],
        )
        return stack

    def poll(self):
        pass

    def setup(self):
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

            if cluster_stack["cluster"] and not cluster_stack["node_pools"]:
                cluster_details["create_node_pool"].cluster_id = cluster_stack[
                    "cluster"
                ].id
                node_pool = create_node_pool(
                    self.container_engine_client, cluster_details["create_node_pool"]
                )
                if node_pool:
                    cluster_stack["node_pool"].extend(node_pool)

            if valid_cluster_stack(cluster_stack):
                self.cluster_stack = cluster_stack

        if self.cluster_stack:
            self._is_ready = True

    def tear_down(self):
        if self.cluster_stack:
            cluster = self.cluster_stack["cluster"]
            deleted = delete_cluster_stack(self.container_engine_client, cluster.id)
            if deleted:
                self.cluster_stack = None
        else:
            self.cluster_stack = None

        if self.vcn_stack:
            vcn_deleted = delete_vcn_stack(
                self.network_client,
                self.options["oci"]["compartment_id"],
                vcn_id=self.vcn_stack["vcn"].id,
            )
            if vcn_deleted:
                self.vcn_stack = None

        if self.cluster_stack and self.vcn_stack:
            self._is_ready = True
        else:
            self._is_ready = False

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

        optional_node_keys = ["ssh_public_key"]

        expected_vcn_keys = ["cidr_block", "dns_label", "display_name"]

        expected_subnet_keys = ["dns_label"]

        # TODO, this and vcn cidr_block should be optional
        optional_subnet_keys = ["cidr_block", "display_name"]

        expected_groups = {
            "oci": expected_oci_keys,
            "cluster": expected_cluster_keys,
            "node": expected_node_keys + optional_node_keys,
            "vcn": expected_vcn_keys,
            "subnet": expected_subnet_keys + optional_subnet_keys,
        }

        for group, keys in expected_groups.items():
            if group not in options:
                raise KeyError("Missing group: {}".format(group))

            if not isinstance(options[group], dict):
                raise TypeError("Group: {} must be a dictionary".format(group))

            for key, _ in options[group].items():
                if key not in keys:
                    raise KeyError("Incorrect key: {} is not in: {}".format(key, keys))
