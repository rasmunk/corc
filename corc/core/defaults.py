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

# To get extra information about an entity
DETAILS = "DETAILS"

CONFIGURER = "configurer"
CONFIGURER_OPERATIONS = ["add_provider", "remove_provider"]
CONFIGURER_CLI = {CONFIGURER: CONFIGURER_OPERATIONS}

COMPUTE = "compute"
COMPUTE_OPERATIONS = ["add_provider", "remove_provider"]
COMPUTE_CLI = {COMPUTE: COMPUTE_OPERATIONS}

POOL = "pool"
POOL_OPERATIONS = ["create", "remove", "show", "ls", "add_instance", "remove_instance"]
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
CORC_CLI_STRUCTURE = [CONFIGURER_CLI, COMPUTE_CLI, ORCHESTRATION_CLI, STORAGE_CLI]

# Action groups
ACTION_GROUPS = [INSTANCE, CONFIG, JOB, META, NODE, RUN, STORAGE]

# Job defaults
JOB_DEFAULT_NAME = "job"

# Default state directory
default_base_path = os.path.join(os.path.expanduser("~"), ".{}".format(PACKAGE_NAME))
