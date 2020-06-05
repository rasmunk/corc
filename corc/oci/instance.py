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
    CreateVnicDetails,
    Instance,
)
from corc.orchestrator import Orchestrator
from corc.util import open_port
from corc.oci.helpers import (
    create,
    delete,
    get,
    list_entities,
    new_client,
    stack_was_deleted,
)
from corc.oci.network import (
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
    # compute_client = new_client(
    #     ComputeClient,
    #     composite_class=ComputeClientCompositeOperations,
    #     profile_name=oci_kwargs["profile_name"],
    # )

    # identity_client = new_client(
    #     IdentityClient,
    #     composite_class=IdentityClientCompositeOperations,
    #     profile_name=oci_kwargs["profile_name"],
    # )

    # network_client = new_client(
    #     VirtualNetworkClient,
    #     composite_class=VirtualNetworkClientCompositeOperations,
    #     profile_name=oci_kwargs["profile_name"],
    # )

    # # AD
    # selected_availability_domain = None
    # available_domains = list_entities(
    #     identity_client,
    #     "list_availability_domains",
    #     compartment_id=oci_kwargs["compartment_id"],
    # )

    # for domain in available_domains:
    #     if domain.name == compute_kwargs["ad"]:
    #         selected_availability_domain = domain

    # if not selected_availability_domain:
    #     print("Failed to find the selected AD: {}".format(compute_kwargs["ad"]))
    #     print("Available are: {}".format(available_domains))
    #     return False

    # # Available images
    # available_images = list_entities(
    #     compute_client, "list_images", oci_kwargs["compartment_id"]
    # )

    # available_shapes = list_entities(
    #     compute_client, "list_shapes", oci_kwargs["compartment_id"]
    # )

    # instance_details = _gen_instance_stack_details(
    #     self.vcn_stack["vcn"].id,
    #     subnet.id,
    #     available_images,
    #     available_shapes,
    #     self.options,
    # )

    # # Network (VCN)
    # selected_vcn = None
    # get_vcn_by_name(
    #     network_client, oci_kwargs["compartment_id"],
    # )

    # # VCN Subnet
    # selected_subnet = None
    # if not selected_subnet:
    #     print("Failed to find the selected subnet: {}".format(subnet_kwargs["id"]))
    #     return False

    # # Existing or create new vnic
    # create_vnic_details = CreateVnicDetails(subnet_id=selected_subnet.id)

    # launch_instance_details = LaunchInstanceDetails(
    #     compartment_id=oci_kwargs["compartment_id"],
    #     availability_domain=selected_availability_domain.name,
    #     shape=selected_shape.shape,
    # )

    # instance = create_instance(
    #     compute_client,
    #     launch_instance_details,
    #     wait_for_states=[oci.core.models.Instance.LIFECYCLE_STATE_PROVISIONING],
    # )

    # print("Instance: {}".format(instance))


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

    shape = _prepare_shape(shapes, **options["compute"])

    create_vnic_details = _prepare_vnic_details(subnet_id=subnet_id)

    # Extract metadata
    metadata = {}
    if "compute_metadata" in options:
        metadata = _prepare_metadata(**options["compute_metadata"])

    if "shape" in options["compute"]:
        options["compute"].pop("shape")

    launch_instance_details = _prepare_launch_instance_details(
        compartment_id=options["oci"]["compartment_id"],
        shape=shape,
        create_vnic_details=create_vnic_details,
        source_details=source_details,
        metadata=metadata,
        **options["compute"],
    )

    instance_stack_details["launch_instance"] = launch_instance_details
    return instance_stack_details


class OCIInstanceOrchestrator(Orchestrator):
    def __init__(self, options):
        super().__init__(options)

        self.compute_client = new_client(
            ComputeClient,
            composite_class=ComputeClientCompositeOperations,
            profile_name=options["oci"]["profile_name"],
        )

        self.identity_client = new_client(
            IdentityClient,
            composite_class=IdentityClientCompositeOperations,
            profile_name=options["oci"]["profile_name"],
        )

        self.network_client = new_client(
            VirtualNetworkClient,
            composite_class=VirtualNetworkClientCompositeOperations,
            profile_name=options["oci"]["profile_name"],
        )

        self.port = 22
        self.instance = None
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

    def setup(self):
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
            self.options["oci"]["compartment_id"],
            self.vcn_stack["id"],
            self.options["subnet"]["display_name"],
        )

        if not subnet:
            raise RuntimeError(
                "Failed to find a subnet with the name: {} in vcn: {}".format(
                    self.options["subnet"]["display_name"], self.vcn_stack["vcn"].id
                )
            )

        # Available images
        available_images = list_entities(
            self.compute_client, "list_images", self.options["oci"]["compartment_id"]
        )

        available_shapes = list_entities(
            self.compute_client, "list_shapes", self.options["oci"]["compartment_id"]
        )

        instance_details = _gen_instance_stack_details(
            self.vcn_stack["vcn"].id,
            subnet.id,
            available_images,
            available_shapes,
            **self.options,
        )

        instance = None
        if "display_name" in self.options["compute"]:
            instance = get_instance_by_name(
                self.compute_client,
                self.options["oci"]["compartment_id"],
                self.options["compute"]["display_name"],
            )

        if not instance:
            self._is_ready = False
            instance = create_instance(
                self.compute_client, instance_details["launch_instance"]
            )
            if valid_instance(instance):
                self.instance = instance
            else:
                raise ValueError("The new instance: {} is not valid".format(instance))
        else:
            if valid_instance(instance):
                self.instance = instance

        if self.instance:
            self._is_ready = True

    def tear_down(self):
        if not self.instance:
            self.instance = get_instance_by_name(
                self.compute_client,
                self.options["oci"]["compartment_id"],
                self.options["compute"]["display_name"],
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
                self.instance = None
        else:
            self.instance = None

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
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise ValueError("options is not a dictionary")

        expected_oci_keys = [
            "compartment_id",
            "profile_name",
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
