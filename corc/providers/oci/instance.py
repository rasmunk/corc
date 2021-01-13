import copy
import oci
from oci.core import (
    ComputeClient,
    ComputeClientCompositeOperations,
    VirtualNetworkClient,
    VirtualNetworkClientCompositeOperations,
)
from oci.identity import IdentityClient, IdentityClientCompositeOperations
from oci.core.models import (
    InstanceSourceViaImageDetails,
    LaunchInstanceDetails,
    InstanceShapeConfig,
    LaunchInstanceShapeConfigDetails,
    CreateVnicDetails,
    Instance,
    CreateSubnetDetails,
    CreateVcnDetails,
    CreateInternetGatewayDetails,
    CreateRouteTableDetails,
)
from oci.util import to_dict
from corc.authenticator import SSHCredentials
from corc.orchestrator import Orchestrator
from corc.util import open_port
from corc.config import (
    default_config_path,
    load_from_config,
    load_from_env_or_config,
    gen_config_provider_prefix,
)
from corc.providers.oci.helpers import (
    create,
    delete,
    get,
    list_entities,
    new_client,
    stack_was_deleted,
    prepare_details,
    new_compute_client,
)
from corc.providers.oci.network import (
    ensure_vcn_stack,
    new_vcn_stack,
    valid_vcn_stack,
    delete_vcn_stack,
    create_subnet,
    refresh_vcn_stack,
    get_subnet_in_vcn_stack,
)


def valid_instance(instance):
    if not isinstance(instance, Instance):
        return False
    return True


def create_instance(
    compute_client, launch_instance_details, wait_for_states=None, **kwargs
):
    if not wait_for_states:
        wait_for_states = [oci.core.models.Instance.LIFECYCLE_STATE_RUNNING]

    instance = create(
        compute_client,
        "launch_instance",
        launch_instance_details,
        wait_for_states=wait_for_states,
        **kwargs,
    )
    if not instance:
        return None
    return instance


def client_list_instances(provider, provider_kwargs, format_return=False, **kwargs):
    client = new_compute_client(name=provider_kwargs["profile"]["name"])
    instances = list_instances(client, provider_kwargs["profile"]["compartment_id"])
    if format_return:
        return to_dict(instances)
    return instances


def list_instances(compute_client, compartment_id, kwargs=None):
    if not kwargs:
        kwargs = {}

    if "lifecycle_state" not in kwargs:
        kwargs.update(dict(lifecycle_state=Instance.LIFECYCLE_STATE_RUNNING))

    return list_entities(
        compute_client, "list_instances", compartment_id=compartment_id, **kwargs
    )


def client_delete_instance(provider, provider_kwargs, instance=None):
    if not instance["id"] and not instance["display_name"]:
        return False, "Either the id or display-name of the instance must be provided"

    compute_client = new_compute_client(name=provider_kwargs["profile"]["name"])
    if instance["id"]:
        instance_id = instance["id"]
    else:
        instance_object = get_instance_by_name(
            compute_client,
            provider_kwargs["profile"]["compartment_id"],
            instance["display_name"],
        )
        if not instance_object:
            return (
                False,
                "Failed to find an instance with display-name: {}".format(
                    instance["display_name"]
                ),
            )

        instance_id = instance_object.id

    deleted = delete_instance(compute_client, instance_id)
    return deleted, instance_id


def delete_instance(compute_client, instance_id, **kwargs):
    return delete(compute_client, "terminate_instance", instance_id, **kwargs)


def client_get_instance(provider, provider_kwargs, format_return=False, instance=None):
    if not instance["id"] and not instance["display_name"]:
        msg = "Either the id or name of the instance must be provided"
        return False, msg

    client = new_compute_client(name=provider_kwargs["profile"]["name"])
    found_instance = None
    if instance["id"]:
        instance_id = instance["id"]
        found_instance = get_instance(
            client, provider_kwargs["profile"]["compartment_id"], instance_id
        )
    else:
        found_instance = get_instance_by_name(
            client,
            provider_kwargs["profile"]["compartment_id"],
            instance["display_name"],
        )
    if found_instance:
        if format_return:
            return to_dict(instance), ""
        return instance, ""
    return None, "Failed to find an instance"


def get_instance(compute_client, compartment_id, instance_id, kwargs=None):
    if not kwargs:
        kwargs = {}
    return get(compute_client, "get_instance", instance_id, **kwargs)


def get_instance_by_name(compute_client, compartment_id, display_name, kwargs=None):
    if not kwargs:
        kwargs = {}

    kwargs.update(dict(display_name=display_name))
    instances = list_instances(compute_client, compartment_id, kwargs=kwargs)
    if instances:
        return instances[0]
    return None


def _prepare_source_details(available_images, **kwargs):
    selected_image = None
    for image in available_images:
        if (
            image.operating_system == kwargs["operating_system"]
            and image.operating_system_version == kwargs["operating_system_version"]
        ):
            selected_image = image
            break

    if not selected_image:
        raise RuntimeError("Failed to find the specified image")

    source_image_kwargs = {
        k: v for k, v in kwargs.items() if hasattr(InstanceSourceViaImageDetails, k)
    }
    source_image_details = InstanceSourceViaImageDetails(
        image_id=selected_image.id, **source_image_kwargs
    )
    return source_image_details


def _prepare_shape(available_shapes, **kwargs):
    selected_shape = None
    for shape in available_shapes:
        if shape.shape == kwargs["shape"]:
            selected_shape = shape.shape
            break

    if not selected_shape:
        raise RuntimeError("Failed to find the specified shape")

    return selected_shape


def _prepare_shape_config(**kwargs):
    shape_kwargs = {
        k: v for k, v in kwargs.items() if hasattr(LaunchInstanceShapeConfigDetails, k)
    }
    shape_config_details = LaunchInstanceShapeConfigDetails(**shape_kwargs)
    return shape_config_details


def _prepare_vnic_details(**kwargs):
    create_nvic_kwargs = {
        k: v for k, v in kwargs.items() if hasattr(CreateVnicDetails, k)
    }
    create_vnic_details = CreateVnicDetails(**create_nvic_kwargs)
    return create_vnic_details


def _prepare_metadata(**kwargs):
    prepared_metadata = {}
    if "ssh_authorized_keys" in kwargs:
        prepared_metadata.update(
            {"ssh_authorized_keys": "\n".join(kwargs["ssh_authorized_keys"])}
        )
        kwargs.pop("ssh_authorized_keys")

    prepared_metadata.update(**kwargs)
    return prepared_metadata


def _prepare_launch_instance_details(**kwargs):
    instance_kwargs = {
        k: v for k, v in kwargs.items() if hasattr(LaunchInstanceDetails, k)
    }
    launch_instance_details = LaunchInstanceDetails(**instance_kwargs)
    return launch_instance_details


def _gen_instance_stack_details(vcn_id, subnet_id, images, shapes, **options):
    instance_stack_details = {}
    source_details = _prepare_source_details(images, **options["instance"])

    # Either static or dynamic shape
    shape_config = None
    if "shape_config" in options["instance"]:
        shape_config = _prepare_shape_config(**options["instance"]["shape_config"])
        options["instance"].pop("shape_config")

    shape = _prepare_shape(shapes, **options["instance"])
    if "shape" in options["instance"]:
        options["instance"].pop("shape")

    create_vnic_details = _prepare_vnic_details(subnet_id=subnet_id)

    # Extract metadata
    metadata = {}
    if "instance_metadata" in options:
        metadata = _prepare_metadata(**options["instance_metadata"])

    launch_instance_dict = dict(
        compartment_id=options["profile"]["compartment_id"],
        shape=shape,
        create_vnic_details=create_vnic_details,
        source_details=source_details,
        metadata=metadata,
        **options["instance"],
    )

    if shape_config:
        launch_instance_dict.update({"shape_config": shape_config})

    launch_instance_details = _prepare_launch_instance_details(**launch_instance_dict)

    instance_stack_details["launch_instance"] = launch_instance_details
    return instance_stack_details


class OCIInstanceOrchestrator(Orchestrator):
    def __init__(self, options):
        super().__init__(options)

        self.compute_client = new_client(
            ComputeClient,
            composite_class=ComputeClientCompositeOperations,
            name=options["profile"]["name"],
        )

        self.identity_client = new_client(
            IdentityClient,
            composite_class=IdentityClientCompositeOperations,
            name=options["profile"]["name"],
        )

        self.network_client = new_client(
            VirtualNetworkClient,
            composite_class=VirtualNetworkClientCompositeOperations,
            name=options["profile"]["name"],
        )

        self.port = 22
        self.instance = None
        self.vcn_stack = None

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
            vcn_kwargs=self.options["vcn"],
            internet_gateway_kwargs=self.options["internetgateway"],
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

    def endpoint(self, select=None):
        # Return the endpoint that is being orchestrated
        public_endpoint = None
        if self.instance:
            vnic_attachments = list_entities(
                self.compute_client,
                "list_vnic_attachments",
                self.options["profile"]["compartment_id"],
                instance_id=self.instance.id,
            )
            # For now just pick the first attachment
            for vnic_attach in vnic_attachments:
                vnic = get(self.network_client, "get_vnic", vnic_attach.vnic_id)
                if hasattr(vnic, "public_ip") and vnic.public_ip:
                    public_endpoint = vnic.public_ip
                    break
        return public_endpoint

    def get_resource(self):
        return self.resource_id, self.instance

    def poll(self):
        target_endpoint = self.endpoint()
        if target_endpoint:
            if open_port(target_endpoint, self.port):
                self._is_reachable = True
                return
        self._is_reachable = False

    def setup(self, resource_config=None, credentials=None):
        # If shape in resource_config, override general options
        options = copy.deepcopy(self.options)
        if not resource_config:
            resource_config = {}

        if not credentials:
            credentials = []

        # TODO, check isinstance dict resource_config
        if "shape" in resource_config:
            options["instance"]["shape"] = resource_config["shape"]

        if "shape_config" in resource_config:
            options["instance"]["shape_config"] = resource_config["shape_config"]

        if "instance_metadata" not in options:
            options["instance_metadata"] = {}

        for credential in credentials:
            if hasattr(credential, "public_key") and getattr(credential, "public_key"):
                if "ssh_authorized_keys" not in options["instance_metadata"]:
                    options["instance_metadata"]["ssh_authorized_keys"] = []

                options["instance_metadata"]["ssh_authorized_keys"].append(
                    getattr(credential, "public_key")
                )

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
            subnet_kwargs=options["subnet"],
            optional_value_kwargs=["id", "display_name"],
        )

        if not subnet:
            # Create new subnet and attach to the vcn_stack
            create_subnet_details = prepare_details(
                CreateSubnetDetails,
                compartment_id=options["profile"]["compartment_id"],
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
                    options["subnet"]["display_name"], self.vcn_stack["vcn"].id
                )
            )

        # Available images
        available_images = list_entities(
            self.compute_client, "list_images", options["profile"]["compartment_id"]
        )

        available_shapes = list_entities(
            self.compute_client,
            "list_shapes",
            options["profile"]["compartment_id"],
            availability_domain=options["instance"]["availability_domain"],
        )

        instance_details = _gen_instance_stack_details(
            self.vcn_stack["vcn"].id,
            subnet.id,
            available_images,
            available_shapes,
            **options,
        )

        instance = None
        if "display_name" in options["instance"]:
            instance = get_instance_by_name(
                self.compute_client,
                options["profile"]["compartment_id"],
                options["instance"]["display_name"],
                kwargs={
                    "availability_domain": options["instance"]["availability_domain"]
                },
            )

        if not instance:
            self._is_ready = False
            instance = create_instance(
                self.compute_client, instance_details["launch_instance"]
            )
            if valid_instance(instance):
                self.resource_id, self.instance = instance.id, instance
            else:
                raise ValueError("The new instance: {} is not valid".format(instance))
        else:
            if valid_instance(instance):
                self.resource_id, self.instance = instance.id, instance

        if self.instance and self.resource_id:
            # Assign unique id to instance
            self._is_ready = True

    def tear_down(self):
        if not self.instance:
            self.instance = get_instance_by_name(
                self.compute_client,
                self.options["profile"]["compartment_id"],
                self.options["instance"]["display_name"],
                kwargs={
                    "availability_domain": self.options["instance"][
                        "availability_domain"
                    ]
                },
            )

        if self.instance:
            # Await that it is terminated
            # Must be done before we can remove the vcn
            deleted = delete_instance(
                self.compute_client,
                self.instance.id,
                wait_for_states=[Instance.LIFECYCLE_STATE_TERMINATED],
            )
            if deleted:
                self.resource_id, self.instance = None, None
        else:
            self.resource_id, self.instance = None, None

        if not self.vcn_stack:
            # refresh
            self.vcn_stack = self._get_vcn_stack()

        # TODO, optional delete
        if self.vcn_stack:
            vcn_deleted = delete_vcn_stack(
                self.network_client,
                self.options["profile"]["compartment_id"],
                vcn_id=self.vcn_stack["id"],
            )
            if stack_was_deleted(vcn_deleted):
                self.vcn_stack = None

        if self.instance and self.vcn_stack:
            self._is_ready = True
        else:
            self._is_ready = False

    @classmethod
    def adapt_options(cls, **kwargs):
        adapted_options = {}
        options = {}
        if "provider_kwargs" in kwargs:
            options.update(kwargs["provider_kwargs"])

        if "kwargs" in kwargs:
            options.update(kwargs["kwargs"])

        for k, v in options.items():
            if k == "vcn":
                adapted_options["internetgateway"] = v.pop("internetgateway", {})
                adapted_options["routetable"] = v.pop("routetable", {})
                adapted_options["subnet"] = v.pop("subnet", {})
                adapted_options[k] = v
            else:
                adapted_options[k] = v
        return adapted_options

    @classmethod
    def load_config_options(cls, provider="oci", path=default_config_path):
        options = {}
        provider_prefix = (provider,)
        oci_profile = load_from_config(
            {"profile": {}},
            prefix=gen_config_provider_prefix(provider_prefix),
            path=path,
            allow_sub_keys=True,
        )

        oci_instance = load_from_config(
            {"instance": {}},
            prefix=gen_config_provider_prefix(provider_prefix),
            path=path,
            allow_sub_keys=True,
        )

        oci_vcn = load_from_config(
            {"vcn": {}},
            prefix=gen_config_provider_prefix(provider_prefix),
            path=path,
            allow_sub_keys=True,
        )

        if "profile" in oci_profile:
            options["profile"] = oci_profile["profile"]

        if "instance" in oci_instance:
            options["instance"] = oci_instance["instance"]

        if "vcn" in oci_vcn:
            vcn = oci_vcn["vcn"]
            if "subnet" in vcn:
                options["subnet"] = vcn.pop("subnet")

            if "routetable" in vcn:
                options["routetable"] = vcn.pop("routetable")

            if "internetgateway" in vcn:
                options["internetgateway"] = vcn.pop("internetgateway")

            options["vcn"] = vcn
        return options

    @classmethod
    def make_resource_config(
        cls,
        provider,
        provider_profile=None,
        provider_kwargs=None,
        cpu=None,
        memory=None,
        gpus=None,
    ):
        if not provider_profile:
            provider_profile = {}

        if not provider_kwargs:
            provider_kwargs = {}

        availability_domain = ""
        if "availability_domain" in provider_kwargs:
            availability_domain = provider_kwargs["availability_domain"]
        else:
            # Try load from config
            availability_domain = load_from_env_or_config(
                {"instance": {"availability_domain": {}}},
                prefix=gen_config_provider_prefix((provider,)),
            )

        # TODO, load OCI environment variables
        compute_client = new_client(
            ComputeClient,
            composite_class=ComputeClientCompositeOperations,
            name=provider_profile["name"],
        )

        resource_config = {}
        available_shapes = list_entities(
            compute_client,
            "list_shapes",
            provider_profile["compartment_id"],
            availability_domain=availability_domain,
        )

        # Subset selection
        if cpu:
            cpu_shapes = []
            for shape in available_shapes:
                # Either dynamic or fixed ocpu count
                if (
                    hasattr(shape, "ocpu_options")
                    and shape.ocpu_options
                    and shape.ocpu_options.max >= cpu
                    and shape.ocpu_options.min <= cpu
                ):
                    # Requires shape config
                    shape.ocpus = cpu
                    cpu_shapes.append(shape)
                else:
                    if shape.ocpus >= cpu:
                        cpu_shapes.append(shape)
            available_shapes = cpu_shapes

        if memory:
            memory_shapes = []
            for shape in available_shapes:
                if (
                    hasattr(shape, "memory_options")
                    and shape.memory_options
                    and shape.memory_options.max_in_g_bs >= memory
                    and shape.memory_options.min_in_g_bs <= memory
                ):
                    # Dynamic memory range
                    # HACK, since you can't atm set the dynamic memory amount
                    # Ensure that we rank the flexible shapes by how
                    # much the total allocated memory is assigned to the instance
                    shape.memory_in_gbs = (
                        shape.memory_options.default_per_ocpu_in_g_bs * shape.ocpus
                    )
                    memory_shapes.append(shape)
                else:
                    if shape.memory_in_gbs >= memory:
                        memory_shapes.append(shape)
            available_shapes = memory_shapes

        if gpus:
            gpu_shapes = []
            for shape in available_shapes:
                if hasattr(shape, "gpus") and shape.gpus >= gpus:
                    gpu_shapes.append(shape)
            available_shapes = gpu_shapes

        # TODO, Minimum shape available
        if available_shapes:
            # sort on cpu and memory
            minimum_shape = sorted(
                available_shapes, key=lambda shape: (shape.ocpus, shape.memory_in_gbs)
            )[0]
            # If a dynamic resource instance -> needs to be a shape_config
            if (
                hasattr(minimum_shape, "ocpu_options")
                and minimum_shape.ocpu_options
                and hasattr(minimum_shape, "memory_options")
                and minimum_shape.memory_options
            ):
                # pass shape values to shapeconfig
                instance_shape_details = {}
                attributes = minimum_shape.attribute_map
                for k, v in attributes.items():
                    if hasattr(InstanceShapeConfig, k):
                        instance_shape_details[k] = getattr(minimum_shape, k)
                # shape_config = InstanceShapeConfig(**instance_shape_details)
                resource_config["shape_config"] = instance_shape_details
            resource_config["shape"] = minimum_shape.shape
        return resource_config

    @classmethod
    def make_credentials(cls, **kwargs):
        credentials = []
        if "instance" in kwargs and "ssh_authorized_keys" in kwargs["instance"]:
            public_keys = kwargs["instance"]["ssh_authorized_keys"]
            for public_key in public_keys:
                credentials.append(SSHCredentials(public_key=public_key))
        return credentials

    @classmethod
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise ValueError("options is not a dictionary")
        expected_profile_keys = [
            "compartment_id",
            "name",
        ]

        expected_instance_keys = [
            "availability_domain",
            "shape",
            "operating_system",
            "operating_system_version",
        ]
        optional_instance_metadata_keys = ["ssh_authorized_keys"]
        optional_instance_keys = ["display_name"]

        expected_vcn_keys = ["dns_label", "display_name"]
        optional_vcn_keys = [
            k
            for k, v in CreateVcnDetails().attribute_map.items()
            if k not in expected_vcn_keys
        ]
        optional_vcn_keys.append("id")

        expected_subnet_keys = ["dns_label", "display_name"]
        optional_subnet_keys = [
            k
            for k, v in CreateSubnetDetails().attribute_map.items()
            if k not in expected_subnet_keys
        ]
        optional_subnet_keys.append("id")

        expected_route_table_keys = ["routerules"]
        optional_route_table_keys = [
            k
            for k, v in CreateRouteTableDetails().attribute_map.items()
            if k not in expected_route_table_keys
        ]
        optional_route_table_keys.append("id")
        # optional_route_rule_keys = [k for k, v in RouteRule().attribute_map.items()]

        expected_gateway_keys = ["is_enabled"]
        optional_gateway_keys = [
            k
            for k, v in CreateInternetGatewayDetails().attribute_map.items()
            if k not in expected_gateway_keys
        ]
        optional_gateway_keys.append("id")

        expected_groups = {
            "profile": expected_profile_keys,
            "instance": expected_instance_keys
            + optional_instance_metadata_keys
            + optional_instance_keys,
            "vcn": expected_vcn_keys + optional_vcn_keys,
            "routetable": expected_route_table_keys + optional_route_table_keys,
            # "route_rule": optional_route_rule_keys,
            "internetgateway": expected_gateway_keys + optional_gateway_keys,
            "subnet": expected_subnet_keys + optional_subnet_keys,
        }

        # TODO, flatten the dict before the validation
        # -> avoid recursion for nested structures
        for group, keys in expected_groups.items():
            if group not in options:
                raise KeyError("Missing group: {}".format(group))

            if not isinstance(options[group], dict):
                raise TypeError("Group: {} must be a dictionary".format(group))

            for key, _ in options[group].items():
                if key not in keys:
                    raise KeyError("Incorrect key: {} is not in: {}".format(key, keys))
