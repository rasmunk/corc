from libcloud.compute.types import Provider as ComputeProvider
from libcloud.container.types import Provider as ContainerProvider
from corc.providers.defaults import (
    BARE_METAL,
    CONTAINER_CLUSTER,
    CONTAINER,
    DOCKER,
    EC2,
    LOCAL,
    KUBERNETES,
    OCI,
    VIRTUAL_MACHINE,
)
from corc.providers.oci.instance import OCIInstanceOrchestrator
from corc.providers.oci.cluster import OCIClusterOrchestrator
from corc.providers.apache.cluster import ApacheClusterOrchestrator
from corc.providers.apache.container import ApacheContainerOrchestrator
from corc.providers.apache.instance import ApacheInstanceOrchestrator
from corc.providers.dummy import LocalOrchestrator

# Define orchestrators for the various cloud backends
# HACK, for now use the non SSL port to connect to DOCKER locally
ORCHESTRATORS = {
    CONTAINER: {
        LOCAL: {
            "klass": ApacheContainerOrchestrator,
            "options": {
                "driver": {
                    "provider": ContainerProvider.DOCKER,
                    "kwargs": {"port": "2345"},
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


# def get_scheduler(scheduler, provider):
#     scheduler_definition = SCHEDULERS[scheduler][provider]
#     klass = scheduler_definition.get("klass", None)
#     options = scheduler_definition.get("options", {})
#     return klass, options
