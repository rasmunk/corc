# TODO, make this work without the required import of the
# external library
from libcloud.compute.types import Provider as ComputeProvider
from libcloud.container.types import Provider as ContainerProvider

from corc.orchestration.defaults import EC2, OCI, LIBVIRT, VIRTUAL_MACHINE
from corc.orchestration.providers.oci.instance import OCIInstanceOrchestrator
from corc.orchestration.providers.oci.cluster import OCIClusterOrchestrator
from corc.orchestration.providers.apache.cluster import ApacheClusterOrchestrator
from corc.orchestration.providers.apache.container import ApacheContainerOrchestrator
from corc.orchestration.providers.apache.instance import ApacheInstanceOrchestrator
from corc.orchestration.providers.orchestration.dummy import LocalOrchestrator


ORCHESTRATORS = {
    # TODO, switch EC2 to ECS
    CONTAINER_CLUSTER: {
        OCI: {"klass": OCIClusterOrchestrator},
        EC2: {
            "klass": ApacheClusterOrchestrator,
            "options": {"driver": {"provider": ContainerProvider.ECS}},
        },
        KUBERNETES: {
            "klass": ApacheClusterOrchestrator,
            "options": {"driver": {"provider": ContainerProvider.KUBERNETES}},
        },
        DOCKER: {
            "klass": ApacheClusterOrchestrator,
            "options": {"driver": {"provider": ContainerProvider.DOCKER}},
        },
    },
    VIRTUAL_MACHINE: {
        OCI: {"klass": OCIInstanceOrchestrator},
        EC2: {
            "klass": ApacheInstanceOrchestrator,
            "options": {"driver": {"provider": ComputeProvider.EC2}},
        },
        LIBVIRT: {
            "klass": ApacheInstanceOrchestrator,
            "options": {"driver": {"provider": ComputeProvider.LIBVIRT}},
        },
    },
    BARE_METAL: {LOCAL: {"klass": LocalOrchestrator},},
}


def get_orchestrator(resource_type, provider):
    orchestrator_definition = ORCHESTRATORS[resource_type][provider]
    klass = orchestrator_definition.get("klass", None)
    options = {}
    try:
        options = klass.load_config_options(provider=provider)
    except NotImplementedError:
        pass
    options.update(orchestrator_definition.get("options", {}))
    return klass, options


# TODO, maybe more to a more sensible place
def get_provider_resource_creation_id(provider, resource_type):
    """ Returns the fields used to identify the resource type for a given provider """
    creation_id = RESOURCE_CREATION_IDENTIFERS[provider][resource_type]
    return creation_id
