from libcloud.container.drivers.ecs import ElasticContainerDriver
from libcloud.container.types import Provider as ContainerProvider
from corc.providers.defaults import (
    OCI,
    ECS,
    CONTAINER,
    CONTAINER_CLUSTER,
    KUBERNETES,
    SERVER,
    DOCKER,
)
from corc.providers.oci.cluster import OCIClusterOrchestrator
from corc.providers.apache.cluster import ApacheClusterOrchestrator


# Define orchestrators for the various cloud backends
# Provides the
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
}

# SCHEDULERS = {
#     DOCKER: {"klass": }
# }


def get_orchestrator(orchestrator, provider):
    orchestrator_definition = ORCHESTRATORS[orchestrator][provider]
    klass = orchestrator_definition.get("klass", None)
    options = orchestrator_definition.get("options", {})
    return klass, options


# def get_scheduler(scheduler, provider):
#     scheduler_definition = SCHEDULERS[scheduler][provider]
#     klass = scheduler_definition.get("klass", None)
#     options = scheduler_definition.get("options", {})
#     return klass, options
