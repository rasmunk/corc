from libcloud.compute.types import Provider as ComputeProvider
from libcloud.container.types import Provider as ContainerProvider
from corc.providers.defaults import (
    CONTAINER_CLUSTER,
    EC2,
    ECS,
    VIRTUAL_MACHINE,
    KUBERNETES,
    OCI,
)
from corc.providers.oci.instance import OCIInstanceOrchestrator
from corc.providers.oci.cluster import OCIClusterOrchestrator
from corc.providers.apache.cluster import ApacheClusterOrchestrator
from corc.providers.apache.instance import ApacheInstanceOrchestrator

# Define orchestrators for the various cloud backends
ORCHESTRATORS = {
    CONTAINER_CLUSTER: {
        OCI: {"klass": OCIClusterOrchestrator},
        ECS: {
            "klass": ApacheClusterOrchestrator,
            "options": {"driver": {"provider": ContainerProvider.ECS}},
        },
        KUBERNETES: {
            "klass": ApacheClusterOrchestrator,
            "options": {"driver": {"provider": ContainerProvider.KUBERNETES}},
        },
    },
    VIRTUAL_MACHINE: {
        OCI: {"klass": OCIInstanceOrchestrator},
        EC2: {
            "klass": ApacheInstanceOrchestrator,
            "options": {"driver": {"provider": ComputeProvider.EC2}},
        },
    },
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


# def get_scheduler(scheduler, provider):
#     scheduler_definition = SCHEDULERS[scheduler][provider]
#     klass = scheduler_definition.get("klass", None)
#     options = scheduler_definition.get("options", {})
#     return klass, options
