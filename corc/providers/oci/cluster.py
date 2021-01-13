from oci.core import (
    ComputeClient,
    ComputeClientCompositeOperations,
    VirtualNetworkClient,
    VirtualNetworkClientCompositeOperations,
)
from oci.container_engine import (
    ContainerEngineClient,
    ContainerEngineClientCompositeOperations,
)
from oci.container_engine.models import Cluster, CreateClusterDetails, WorkRequest
from oci.container_engine.models import (
    CreateNodePoolDetails,
    NodePoolPlacementConfigDetails,
    CreateNodePoolNodeConfigDetails,
    NodeSourceViaImageDetails,
)
from oci.core.models import CreateSubnetDetails
from oci.util import to_dict
from corc.providers.oci.helpers import (
    new_client,
    new_compute_client,
    create,
    delete,
    get,
    list_entities,
    get_kubernetes_version,
    prepare_details,
)
from corc.providers.oci.config import (
    valid_profile_config,
    valid_cluster_config,
    valid_cluster_node_config,
    valid_vcn_config,
    valid_subnet_config,
    valid_internet_gateway_config,
    valid_route_rule_config,
    valid_route_table_config,
)
from corc.util import (
    parse_yaml,
    validate_dict_fields,
    validate_dict_values,
)
from corc.schedulers.kubernetes.config import save_kube_config, load_kube_config
from corc.orchestrator import Orchestrator
from corc.providers.oci.network import (
    create_subnet,
    delete_vcn_stack,
    ensure_vcn_stack,
    get_subnet_in_vcn_stack,
    new_vcn_stack,
    valid_vcn_stack,
    refresh_vcn_stack,
    update_vcn_stack,
)


def new_cluster_engine_client(**kwargs):
    return new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        **kwargs,
    )


def refresh_kube_config(cluster_id, name="DEFAULT"):
    container_engine_client = new_client(
        ContainerEngineClient,
        composite_class=ContainerEngineClientCompositeOperations,
        name=name,
    )
    # Try to load the existing
    # Create or refresh the kubernetes config

    kube_config = create(container_engine_client, "create_kubeconfig", cluster_id)
    if kube_config and hasattr(kube_config, "text"):
        config_dict = parse_yaml(kube_config.text)
        # HACK, add profile to user args
        if name:
            profile_args = ["--profile", name]
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

    expected_fields = ["id", "cluster", "node_pools"]
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
    stack = dict(id=None, cluster=None, node_pools=[])
    cluster = create_cluster(container_engine_client, create_cluster_details)

    if not cluster:
        return stack

    # cluster
    stack["cluster"] = cluster
    if hasattr(cluster, "id"):
        stack["id"] = cluster.id
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

    stack = dict(id=None, cluster=None, node_pools=[])

    cluster = get(container_engine_client, "get_cluster", cluster_id)
    if not cluster:
        return stack

    stack["cluster"] = cluster
    if hasattr(cluster, "id"):
        stack["id"] = cluster.id

    # Get node pools (NodePoolSummaries)
    node_pool_summaries = list_entities(
        container_engine_client,
        "list_node_pools",
        compartment_id,
        cluster_id=cluster.id,
        **node_kwargs,
    )

    for summary in node_pool_summaries:
        node_pool = get(container_engine_client, "get_node_pool", summary.id)
        if node_pool:
            stack["node_pools"].append(node_pool)
    return stack


def delete_cluster_stack(container_engine_client, cluster_id, delete_vcn=False):
    # Will implicitly delete the node pool as well
    cluster = get(container_engine_client, "get_cluster", cluster_id)
    if not cluster:
        return False
    return delete_cluster(container_engine_client, cluster_id)


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
        create_cluster_details,
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


def client_list_clusters(provider, provider_kwargs, format_return=False, **kwargs):
    client = new_compute_client(name=provider_kwargs["profile"]["name"])
    clusters = list_clusters(client, provider_kwargs["profile"]["compartment_id"])
    if format_return:
        return to_dict(clusters)
    return clusters


def list_clusters(container_engine_client, compartment_id, cluster_kwargs=None):
    if not cluster_kwargs:
        cluster_kwargs = {}

    if "lifecycle_state" not in cluster_kwargs:
        cluster_kwargs.update(dict(lifecycle_state=[Cluster.LIFECYCLE_STATE_ACTIVE]))

    # ClusterSummaries
    return list_entities(
        container_engine_client,
        "list_clusters",
        compartment_id=compartment_id,
        **cluster_kwargs,
    )


def client_delete_cluster(provider, provider_kwargs, cluster=None):
    if not cluster["id"] and not cluster["display_name"]:
        return False, "Either the id or display-name of the cluster must be provided"

    compute_client = new_compute_client(name=provider_kwargs["profile"]["name"])
    if cluster["id"]:
        cluster_id = cluster["id"]
    else:
        _object = get_cluster_by_name(
            compute_client,
            provider_kwargs["profile"]["compartment_id"],
            cluster["display_name"],
        )
        if not _object:
            return (
                False,
                "Failed to find a cluster with display-name: {}".format(
                    _object["display_name"]
                ),
            )

        cluster_id = _object.id

    deleted = delete_cluster(compute_client, cluster_id)
    return deleted, cluster_id


def delete_cluster(container_engine_client, cluster_id, **kwargs):
    return delete(
        container_engine_client,
        "delete_cluster",
        cluster_id,
        wait_for_states=[WorkRequest.STATUS_SUCCEEDED, WorkRequest.STATUS_FAILED],
        **kwargs,
    )


def client_get_cluster(provider, provider_kwargs, format_return=False, cluster=None):
    if not cluster["id"] and not cluster["display_name"]:
        msg = "Either the id or name of the cluster must be provided"
        return False, msg

    client = new_compute_client(name=provider_kwargs["profile"]["name"])
    found_cluster = None
    if cluster["id"]:
        cluster_id = cluster["id"]
        found_cluster = get_cluster(
            client, provider_kwargs["profile"]["compartment_id"], cluster_id
        )
    else:
        found_cluster = get_cluster_by_name(
            client,
            provider_kwargs["profile"]["compartment_id"],
            cluster["display_name"],
        )
    if found_cluster:
        if format_return:
            return to_dict(cluster), ""
        return cluster, ""
    return None, "Failed to find an cluster"


def get_cluster(compute_client, compartment_id, cluster_id, kwargs=None):
    if not kwargs:
        kwargs = {}
    return get(compute_client, "get_cluster", cluster_id, **kwargs)


def get_cluster_by_name(
    container_engine_client, compartment_id, name, cluster_kwargs=None
):
    if not cluster_kwargs:
        cluster_kwargs = {}

    cluster_kwargs.update(dict(name=name))

    clusters = list_clusters(container_engine_client, compartment_id, cluster_kwargs)
    if clusters:
        # Convert to cluster type
        cluster = get(container_engine_client, "get_cluster", clusters[0].id)
        return cluster
    return None


def delete_node_pool(container_engine_client, cluster_id, **kwargs):
    return delete(container_engine_client, "delete_node_pool", cluster_id, **kwargs)


def create_node_pool(container_engine_client, create_node_pool_details):
    created_response = create(
        container_engine_client,
        "create_node_pool",
        create_node_pool_details,
        wait_for_states=[
            WorkRequest.STATUS_SUCCEEDED,
            WorkRequest.OPERATION_TYPE_NODEPOOL_CREATE,
            WorkRequest.STATUS_FAILED,
        ],
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


def prepare_node_source_details(image, **kwargs):
    if not image:
        raise RuntimeError("No image was provided")

    node_source_details = {
        k: v for k, v in kwargs.items() if hasattr(NodeSourceViaImageDetails, k)
    }

    node_source_details = NodeSourceViaImageDetails(
        image_id=image.id, **node_source_details
    )

    return node_source_details


def prepare_create_cluster_details(**kwargs):
    cluster_kwargs = {
        k: v for k, v in kwargs.items() if hasattr(CreateClusterDetails, k)
    }
    create_cluster_details = CreateClusterDetails(**cluster_kwargs)
    return create_cluster_details


def prepare_node_pool_placement_config(**kwargs):
    node_pool_kwargs = {
        k: v for k, v in kwargs.items() if hasattr(NodePoolPlacementConfigDetails, k)
    }

    return NodePoolPlacementConfigDetails(**node_pool_kwargs)


def prepare_create_node_pool_config(**kwargs):
    create_node_pool_config_kwargs = {
        k: v for k, v in kwargs.items() if hasattr(CreateNodePoolNodeConfigDetails, k)
    }
    return CreateNodePoolNodeConfigDetails(**create_node_pool_config_kwargs)


def prepare_create_node_pool_details(**kwargs):
    # Discover the image_id if the name is provided
    create_node_pool_details = {
        k: v for k, v in kwargs.items() if hasattr(CreateNodePoolDetails, k)
    }
    return CreateNodePoolDetails(**create_node_pool_details)


def gen_cluster_stack_details(vnc_id, subnets, image, **options):
    cluster_details = {}

    create_cluster_details = prepare_create_cluster_details(
        vcn_id=vnc_id,
        compartment_id=options["profile"]["compartment_id"],
        **options["cluster"],
    )
    cluster_details["create_cluster"] = create_cluster_details

    node_pool_place_configs = []
    if subnets:
        for subnet_id, subnet in subnets.items():
            node_pool_place_configs.append(
                prepare_node_pool_placement_config(
                    subnet_id=subnet.id, **options["cluster"]["node"]
                )
            )

    node_config_details = prepare_create_node_pool_config(
        size=options["cluster"]["node"]["size"],
        placement_configs=node_pool_place_configs,
    )

    # Convert the deprecrated image name, to the proper source details
    node_source_details = prepare_node_source_details(image)
    if node_source_details:
        options["cluster"]["node"]["node_source_details"] = node_source_details

    create_node_pool_details = prepare_create_node_pool_details(
        node_config_details=node_config_details,
        kubernetes_version=options["cluster"]["kubernetes_version"],
        compartment_id=options["profile"]["compartment_id"],
        **options["cluster"]["node"],
    )
    cluster_details["create_node_pool"] = create_node_pool_details

    return cluster_details


class OCIClusterOrchestrator(Orchestrator):
    def __init__(self, options):
        super().__init__(options)

        image_options = {}
        # Adapt the node image to the OCI API
        # If the image name is just defined, else expect a dict structure
        if isinstance(options["cluster"]["node"]["image"], str):
            image_name = options["cluster"]["node"]["image"]
            image_options = dict(display_name=image_name)
            self.options["cluster"]["node"].pop("image")
        else:
            image_options = options["cluster"]["node"]["image"]

        self.options["cluster"]["node"]["image"] = image_options

        # Set clients
        self.compute_client = new_client(
            ComputeClient,
            composite_class=ComputeClientCompositeOperations,
            name=options["profile"]["name"],
        )
        self.container_engine_client = new_client(
            ContainerEngineClient,
            composite_class=ContainerEngineClientCompositeOperations,
            name=options["profile"]["name"],
        )
        self.network_client = new_client(
            VirtualNetworkClient,
            composite_class=VirtualNetworkClientCompositeOperations,
            name=options["profile"]["name"],
        )

        if (
            "kubernetes_version" not in self.options["cluster"]
            or not self.options["cluster"]["kubernetes_version"]
        ):
            self.options["cluster"]["kubernetes_version"] = get_kubernetes_version(
                self.container_engine_client
            )

        self.cluster_stack = None
        self.vcn_stack = None
        self._is_ready = False

    def _get_vcn_stack(self):
        return refresh_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
        )

    def _new_vcn_stack(self):
        stack = new_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            internet_gateway_kwargs=self.options["internetgateway"],
            vcn_kwargs=self.options["vcn"],
            route_table_kwargs=self.options["routetable"],
            subnet_kwargs=self.options["subnet"],
        )
        return stack

    def _ensure_vcn_stack(self):
        ensured = ensure_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            internet_gateway_kwargs=self.options["internetgateway"],
            route_table_kwargs=self.options["routetable"],
            subnet_kwargs=self.options["subnet"],
        )
        if not ensured:
            print("Failed to ensure the VCN stack")
        return self._get_vcn_stack()

    def _update_vcn_stack(self):
        return update_vcn_stack(
            self.network_client,
            self.options["profile"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            subnet_kwargs=self.options["subnet"],
        )

    def _valid_vcn_stack(self, vcn_stack):
        # If id or display_name is not set, don't require them
        required_vcn = {
            k: v
            for k, v in self.options["vcn"].items()
            if (k != "id" and k != "display_name")
            or (v and k == "id" or k == "display_name")
        }

        required_igs = [
            {
                k: v
                for k, v in self.options["internetgateway"].items()
                if (k != "id" and k != "display_name")
                or (v and k == "id" or k == "display_name")
            }
        ]
        required_subnets = [
            {
                k: v
                for k, v in self.options["subnet"].items()
                if (k != "id" and k != "display_name")
                or (v and k == "id" or k == "display_name")
            }
        ]
        return valid_vcn_stack(
            vcn_stack,
            required_vcn=required_vcn,
            required_igs=required_igs,
            required_subnets=required_subnets,
        )

    def poll(self):
        self._is_reachable = True

    def setup(self):
        # Ensure we have a VCN stack ready
        vcn_stack = self._get_vcn_stack()
        if not vcn_stack:
            vcn_stack = self._new_vcn_stack()

        if not self._valid_vcn_stack(vcn_stack):
            vcn_stack = self._ensure_vcn_stack()

        if not self._valid_vcn_stack(vcn_stack):
            raise RuntimeError(
                "A valid VCN stack could not be found: {}".format(vcn_stack)
            )
        self.vcn_stack = vcn_stack

        # Find the selected subnet in the VCN
        subnet = get_subnet_in_vcn_stack(
            self.vcn_stack,
            subnet_kwargs=self.options["subnet"],
            optional_value_kwargs=["id", "display_name"],
        )

        if not subnet:
            # Create new subnet and attach to the vcn_stack
            create_subnet_details = prepare_details(
                CreateSubnetDetails,
                compartment_id=self.options["profile"]["compartment_id"],
                vcn_id=self.vcn_stack["id"],
                route_table_id=self.vcn_stack["vcn"].default_route_table_id,
                **self.options["subnet"],
            )
            subnet = create_subnet(
                self.network_client, create_subnet_details, self.vcn_stack["id"]
            )
            self.vcn_stack = self._ensure_vcn_stack()

        if not subnet:
            raise RuntimeError(
                "Failed to find a subnet with the name: {} in vcn: {}".format(
                    self.options["subnet"]["display_name"], self.vcn_stack["vcn"].id
                )
            )

        # Available images
        available_images = list_entities(
            self.compute_client,
            "list_images",
            self.options["profile"]["compartment_id"],
            **self.options["cluster"]["node"]["image"],
        )

        if not available_images:
            raise ValueError(
                "No valid image could be found with options: {}".format(
                    self.options["cluster"]["node"]["image"]
                )
            )

        if len(available_images) > 1:
            raise ValueError(
                "More than 1 image was found with options: {}".format(
                    self.options["cluster"]["node"]["image"]
                )
            )

        image = available_images[0]
        cluster_details = gen_cluster_stack_details(
            self.vcn_stack["id"], self.vcn_stack["subnets"], image, **self.options,
        )

        cluster = get_cluster_by_name(
            self.container_engine_client,
            self.options["profile"]["compartment_id"],
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
                self.options["profile"]["compartment_id"],
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
                    cluster_stack["node_pools"].append(node_pool)

            if valid_cluster_stack(cluster_stack):
                self.cluster_stack = cluster_stack

        if self.cluster_stack:
            self._is_ready = True

    def tear_down(self):
        if not self.cluster_stack:
            # refresh
            cluster = get_cluster_by_name(
                self.container_engine_client,
                self.options["profile"]["compartment_id"],
                self.options["cluster"]["name"],
            )

            if cluster:
                self.cluster_stack = get_cluster_stack(
                    self.container_engine_client,
                    self.options["profile"]["compartment_id"],
                    cluster.id,
                )

        if self.cluster_stack:
            cluster = self.cluster_stack["cluster"]
            deleted = delete_cluster_stack(self.container_engine_client, cluster.id)
            if deleted:
                self.cluster_stack = None
        else:
            self.cluster_stack = None

        if not self.vcn_stack:
            # refresh
            self.vcn_stack = self._get_vcn_stack()

        if self.vcn_stack:
            vcn_deleted = delete_vcn_stack(
                self.network_client,
                self.options["profile"]["compartment_id"],
                vcn_id=self.vcn_stack["id"],
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
            raise TypeError("options is not a dictionary")

        validate_dict_fields(
            options["profile"], valid_profile_config, verbose=True, throw=True
        )
        validate_dict_values(
            options["profile"], valid_profile_config, verbose=True, throw=True
        )

        validate_dict_fields(
            options["cluster"], valid_cluster_config, verbose=True, throw=True
        )
        required_cluster_fields = {"name": str}
        validate_dict_values(
            options["cluster"], required_cluster_fields, verbose=True, throw=True
        )

        required_node_fields = {
            "availability_domain": str,
            "name": str,
            "size": int,
            "node_shape": str,
            "image": (str, dict),
        }

        validate_dict_fields(
            options["cluster"]["node"],
            valid_cluster_node_config,
            verbose=True,
            throw=True,
        )
        validate_dict_values(
            options["cluster"]["node"], required_node_fields, verbose=True, throw=True
        )

        required_vcn_fields = {"dns_label": str, "cidr_block": str}
        validate_dict_fields(options["vcn"], valid_vcn_config, verbose=True, throw=True)
        validate_dict_values(
            options["vcn"], required_vcn_fields, verbose=True, throw=True
        )

        required_subnet_fields = {"dns_label": str, "cidr_block": str}
        validate_dict_fields(
            options["subnet"], valid_subnet_config, verbose=True, throw=True
        )
        validate_dict_values(
            options["subnet"], required_subnet_fields, verbose=True, throw=True
        )

        required_internetgateway_fields = {"is_enabled": bool}
        validate_dict_fields(
            options["internetgateway"],
            valid_internet_gateway_config,
            verbose=True,
            throw=True,
        )
        validate_dict_values(
            options["internetgateway"],
            required_internetgateway_fields,
            verbose=True,
            throw=True,
        )

        required_route_table_fields = {"routerules": list}
        validate_dict_fields(
            options["routetable"], valid_route_table_config, verbose=True, throw=True
        )
        validate_dict_values(
            options["routetable"], required_route_table_fields, verbose=True, throw=True
        )

        required_routerules_fields = {
            "destination": str,
            "destination_type": str,
        }

        # Check each routerule
        if isinstance(options["routetable"]["routerules"], list):
            for route_rule in options["routetable"]["routerules"]:
                validate_dict_fields(
                    route_rule, valid_route_rule_config, verbose=True, throw=True,
                )
                validate_dict_values(
                    route_rule, required_routerules_fields, verbose=True, throw=True,
                )
        else:
            validate_dict_fields(
                options["routetable"]["routerules"],
                valid_route_rule_config,
                verbose=True,
                throw=True,
            )
            validate_dict_values(
                options["routetable"]["routerules"],
                required_routerules_fields,
                verbose=True,
                throw=True,
            )
