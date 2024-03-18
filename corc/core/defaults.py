import os

# Package name
PACKAGE_NAME = "corc"

PROVIDER = "PROVIDER"

# Profile group defaults
PROFILE = "PROFILE"
DRIVER = "DRIVER"
PROFILE_DRIVER = "{}_{}".format(PROFILE, DRIVER)

# Argument group defaults
ANSIBLE = "ANSIBLE"
CLUSTER = "CLUSTER"
NODE = "NODE"
CLUSTER_NODE = "{}_{}".format(CLUSTER, NODE)
INSTANCE = "INSTANCE"
CONFIG = "CONFIG"
JOB = "JOB"
META = "META"
JOB_META = "{}_{}".format(JOB, META)
RUN = "RUN"

STORAGE = "storage"
S3 = "s3"
STORAGE_S3 = "{}_{}".format(STORAGE, S3)

# Networking
SUBNET = "SUBNET"
INTERNETGATEWAY = "INTERNETGATEWAY"
ROUTETABLE = "ROUTETABLE"
ROUTERULES = "ROUTERULES"
VCN = "VCN"
VCN_SUBNET = "{}_{}".format(VCN, SUBNET)
VCN_INTERNETGATEWAY = "{}_{}".format(VCN, INTERNETGATEWAY)
VCN_ROUTETABLE = "{}_{}".format(VCN, ROUTETABLE)
VCN_ROUTETABLE_ROUTERULES = "{}_{}".format(VCN_ROUTETABLE, ROUTERULES)

# To get extra information about an entity
DETAILS = "DETAILS"

CONFIGURER = "configurer"
CONFIGURER_OPERATIONS = ["add_provider", "remove_provider"]
CONFIGURER_CLI = {CONFIGURER: CONFIGURER_OPERATIONS}

COMPUTE = "compute"
COMPUTE_OPERATIONS = ["add_provider", "remove_provider"]
COMPUTE_CLI = {COMPUTE: COMPUTE_OPERATIONS}

POOL = "pool"
POOL_OPERATIONS = ["create", "remove", "show", "ls", "add_node", "remove_node"]
POOL_CLI = {POOL: POOL_OPERATIONS}

STACK = "stack"
STACK_OPERATIONS = ["deploy", "destroy", "show", "ls"]
STACK_CLI = {STACK: STACK_OPERATIONS}

ORCHESTRATION = "orchestration"
ORCHESTRATION_OPERATIONS = ["add_provider", "remove_provider", POOL_CLI, STACK_CLI]
ORCHESTRATION_CLI = {ORCHESTRATION: ORCHESTRATION_OPERATIONS}

STORAGE_OPERATIONS = ["add_provider", "remove_provider"]
STORAGE_CLI = {STORAGE: STORAGE_OPERATIONS}

# List of functionality that corc supports
CORC_CLI_STRUCTURE = [ORCHESTRATION_CLI]

# Action groups
ACTION_GROUPS = [
    ANSIBLE,
    CLUSTER,
    INSTANCE,
    CONFIG,
    JOB,
    META,
    NODE,
    RUN,
    STORAGE,
    SUBNET,
    S3,
    VCN,
]

# Storage credentials secret name
STORAGE_CREDENTIALS_NAME = "storage-credentials"

# Kubernetes defaults
KUBERNETES_NAMESPACE = "default"

# Job defaults
JOB_DEFAULT_NAME = "job"

# Default state directory
default_base_path = os.path.join(os.path.expanduser("~"), ".{}".format(PACKAGE_NAME))

# Default HostKeyAlgorithm order to use across SSH implementations
# if no external configuration is given.
# The order is defined by recommendations from
# https://infosec.mozilla.org/guidelines/openssh.html
default_host_key_order = [
    "ssh-ed25519-cert-v01@openssh.com",
    "ssh-rsa-cert-v01@openssh.com",
    "ssh-ed25519",
    "ssh-rsa",
    "ecdsa-sha2-nistp521-cert-v01@openssh.com",
    "ecdsa-sha2-nistp384-cert-v01@openssh.com",
    "ecdsa-sha2-nistp256-cert-v01@openssh.com",
    "ecdsa-sha2-nistp521",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp256",
]
