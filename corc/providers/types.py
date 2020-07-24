from corc.defaults import OCI
from corc.providers.oci.cluster import OCIClusterOrchestrator
from corc.providers.oci.job import OCIContainerScheduler
from corc.providers.oci.instance import OCIInstanceOrchestrator
from corc.providers.apache.cluster import ApacheClusterOrchestrator


VIRTUAL_MACHINE = "virtual_machine"
CONTAINER_CLUSTER = "container_cluster"


# Define orchestrators for the various cloud backends
# Provides the
ORCHESTRATORS = {
    CONTAINER_CLUSTER: {
        OCI: {"klass": OCIClusterOrchestrator},
        AWS: {"klass": ApacheClusterOrchestrator, "kwargs": {}},
    },
}

CONTAINER = "container"

# Provide driver and arguments to base container classes
SCHEDULERS = {CONTAINER: {}}
