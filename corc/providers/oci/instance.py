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
)
from corc.orchestrator import Orchestrator
from corc.util import open_port
from corc.config import load_from_env_or_config, gen_config_provider_prefix
from corc.providers.config import get_provider_profile
from corc.providers.oci.helpers import (
    create,
    delete,
    get,
    list_entities,
    new_client,
    stack_was_deleted,
)
from corc.providers.oci.network import (
    get_vcn_by_name,
    new_vcn_stack,
    valid_vcn_stack,
    get_vcn_stack,
    get_subnet_by_name,
    delete_vcn_stack,
    refresh_vcn_stack,
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


def terminate_instance(compute_client, instance_id, **kwargs):
    return delete(compute_client, "terminate_instance", instance_id, **kwargs)


def get_instance_by_name(compute_client, compartment_id, display_name, kwargs=None):
    if not kwargs:
        kwargs = {}

    if "lifecycle_state" not in kwargs:
        kwargs.update(dict(lifecycle_state=Instance.LIFECYCLE_STATE_RUNNING))

    instances = list_entities(
        compute_client,
        "list_instances",
        compartment_id,
        display_name=display_name,
        **kwargs,
    )
    if instances:
        return instances[0]
    return None


def launch_instance(compute_kwargs={}, oci_kwargs={}, subnet_kwargs={}, vcn_kwargs={}):
    raise NotImplementedError


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
    source_details = _prepare_source_details(images, **options["compute"])

    # Either static or dynamic shape
    shape_config = None
    if "shape_config" in options["compute"]:
        shape_config = _prepare_shape_config(**options["compute"]["shape_config"])
        options["compute"].pop("shape_config")

    shape = _prepare_shape(shapes, **options["compute"])
    if "shape" in options["compute"]:
        options["compute"].pop("shape")

    create_vnic_details = _prepare_vnic_details(subnet_id=subnet_id)

    # Extract metadata
    metadata = {}
    if "compute_metadata" in options:
        metadata = _prepare_metadata(**options["compute_metadata"])

    launch_instance_dict = dict(
        compartment_id=options["oci"]["compartment_id"],
        shape=shape,
        create_vnic_details=create_vnic_details,
        source_details=source_details,
        metadata=metadata,
        **options["compute"],
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
            name=options["oci"]["name"],
        )

        self.identity_client = new_client(
            IdentityClient,
            composite_class=IdentityClientCompositeOperations,
            name=options["oci"]["name"],
        )

        self.network_client = new_client(
            VirtualNetworkClient,
            composite_class=VirtualNetworkClientCompositeOperations,
            name=options["oci"]["name"],
        )

        self.port = 22
        self.instance = None
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
            subnet_kwargs=self.options["subnet"],
        )
        return stack

    def _refresh_vcn_stack(self, vcn_stack):
        stack = refresh_vcn_stack(
            self.network_client,
            self.options["oci"]["compartment_id"],
            vcn_kwargs=self.options["vcn"],
            subnet_kwargs=self.options["subnet"],
        )
        return stack

    def endpoint(self, select=None):
        # Return the endpoint that is being orchestrated
        public_endpoint = None
        if self.instance:
            vnic_attachments = list_entities(
                self.compute_client,
                "list_vnic_attachments",
                self.options["oci"]["compartment_id"],
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

    def setup(self, resource_config=None):
        # If shape in resource_config, override general options
        options = copy.deepcopy(self.options)
        if not resource_config:
            resource_config = {}

        # TODO, check isinstance dict resource_config
        if "shape" in resource_config:
            options["compute"]["shape"] = resource_config["shape"]

        if "shape_config" in resource_config:
            options["compute"]["shape_config"] = resource_config["shape_config"]

        # Ensure we have a VCN stack ready
        vcn_stack = self._get_vcn_stack()
        if not vcn_stack:
            vcn_stack = self._new_vcn_stack()

        if valid_vcn_stack(vcn_stack):
            self.vcn_stack = vcn_stack
        else:
            # FIXME, creates a duplicate VCN
            self.vcn_stack = self._refresh_vcn_stack(vcn_stack)

        if not valid_vcn_stack(self.vcn_stack):
            raise RuntimeError(
                "Failed to fix the broken VCN stack: {}".format(vcn_stack)
            )

        # Find the selected subnet in the VCN
        subnet = get_subnet_by_name(
            self.network_client,
            options["oci"]["compartment_id"],
            self.vcn_stack["id"],
            options["subnet"]["display_name"],
        )

        if not subnet:
            raise RuntimeError(
                "Failed to find a subnet with the name: {} in vcn: {}".format(
                    options["subnet"]["display_name"], self.vcn_stack["vcn"].id
                )
            )

        # Available images
        available_images = list_entities(
            self.compute_client, "list_images", options["oci"]["compartment_id"]
        )

        available_shapes = list_entities(
            self.compute_client,
            "list_shapes",
            options["oci"]["compartment_id"],
            availability_domain=options["compute"]["availability_domain"],
        )

        instance_details = _gen_instance_stack_details(
            self.vcn_stack["vcn"].id,
            subnet.id,
            available_images,
            available_shapes,
            **options,
        )

        instance = None
        if "display_name" in options["compute"]:
            instance = get_instance_by_name(
                self.compute_client,
                options["oci"]["compartment_id"],
                options["compute"]["display_name"],
                kwargs={
                    "availability_domain": options["compute"]["availability_domain"]
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
                self.options["oci"]["compartment_id"],
                self.options["compute"]["display_name"],
                kwargs={
                    "availability_domain": self.options["compute"][
                        "availability_domain"
                    ]
                },
            )

        if self.instance:
            # Await that it is terminated
            # Must be done before we can remove the vcn
            deleted = terminate_instance(
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
                self.options["oci"]["compartment_id"],
                vcn_id=self.vcn_stack["id"],
            )
            if stack_was_deleted(vcn_deleted):
                self.vcn_stack = None

        if self.instance and self.vcn_stack:
            self._is_ready = True
        else:
            self._is_ready = False

    def poll(self):
        target_endpoint = self.endpoint()
        if target_endpoint:
            if open_port(target_endpoint, self.port):
                self._is_reachable = True

    @classmethod
    def make_resource_config(
        cls,
        provider_profile=None,
        provider_kwargs=None,
        cpu=None,
        memory=None,
        gpus=None,
    ):
        if not provider_profile:
            provider_profile = get_provider_profile("oci")

        if not provider_kwargs:
            provider_kwargs = {}

        availability_domain = ""
        if "availability_domain" not in provider_kwargs:
            # Try load from config
            availability_domain = load_from_env_or_config(
                {"instance": {"availability_domain": {}}},
                prefix=gen_config_provider_prefix(("oci",)),
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
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise ValueError("options is not a dictionary")

        expected_oci_keys = [
            "compartment_id",
            "name",
        ]

        expected_compute_keys = [
            "availability_domain",
            "shape",
            "operating_system",
            "operating_system_version",
        ]

        optional_compute_metadata_keys = ["ssh_authorized_keys"]
        optional_compute_keys = ["display_name"]

        expected_vcn_keys = ["cidr_block", "dns_label", "display_name"]

        optional_vcn_keys = ["id"]

        expected_subnet_keys = ["dns_label"]

        optional_subnet_keys = ["id", "cidr_block", "display_name"]

        expected_groups = {
            "oci": expected_oci_keys,
            "compute": expected_compute_keys
            + optional_compute_metadata_keys
            + optional_compute_keys,
            "vcn": expected_vcn_keys + optional_vcn_keys,
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
