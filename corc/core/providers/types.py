from libcloud.compute.types import Provider as ComputeProvider
from libcloud.container.types import Provider as ContainerProvider
from corc.core.providers.defaults import (
    CONTAINER_CLUSTER,
    CONTAINER,
    DOCKER,
    KUBERNETES,
)
from corc.core.orchestration.defaults import (
    BARE_METAL,
    VIRTUAL_MACHINE,
    OCI,
    EC2,
    LIBVIRT,
    LOCAL,
)
from corc.core.orchestration.providers.oci.instance import OCIInstanceOrchestrator
from corc.core.orchestration.providers.oci.cluster import OCIClusterOrchestrator
from corc.core.providers.apache.cluster import ApacheClusterOrchestrator
from corc.core.providers.apache.container import ApacheContainerOrchestrator
from corc.core.providers.apache.instance import ApacheInstanceOrchestrator
from corc.core.providers.dummy import LocalOrchestrator

# Define orchestrators for the various cloud backends
# HACK, for now use the non SSL port to connect to DOCKER locally
ORCHESTRATORS = {
    CONTAINER: {
        LOCAL: {
            "klass": ApacheContainerOrchestrator,
            "options": {
                "driver": {
                    "provider": ContainerProvider.DOCKER,
                    "kwargs": {"port": "2375"},
                },
            },
        }
    },
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
    BARE_METAL: {
        LOCAL: {"klass": LocalOrchestrator},
    },
}

RESOURCE_CREATION_IDENTIFERS = {
    LOCAL: {CONTAINER: "name"},
    OCI: {
        VIRTUAL_MACHINE: "display_name",
        CONTAINER_CLUSTER: "name",
    },
    EC2: {VIRTUAL_MACHINE: "name"},
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
