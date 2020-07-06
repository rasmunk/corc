# Package name
PACKAGE_NAME = "corc"

# Providers
AWS = "AWS"
AWS_LOWER = "aws"

OCI = "OCI"
OCI_LOWER = "oci"

PROVIDER = "PROVIDER"
DEFAULT_PROVIDER = OCI
DEFAULT_PROVIDER_LOWER = OCI_LOWER
PROVIDERS = [AWS, OCI]
PROVIDERS_LOWER = [AWS_LOWER, OCI_LOWER]

PROFILE = "PROFILE"

# Argument group defaults
ANSIBLE = "ANSIBLE"
CLUSTER = "CLUSTER"
NODE = "NODE"
CLUSTER_NODE = "{}_{}".format(CLUSTER, NODE)
COMPUTE = "COMPUTE"
CONFIG = "CONFIG"
JOB = "JOB"
META = "META"
JOB_META = "{}_{}".format(JOB, META)
RUN = "RUN"
STORAGE = "STORAGE"
S3 = "S3"

# Networking
SUBNET = "SUBNET"
VCN = "VCN"
VCN_SUBNET = "{}_{}".format(VCN, SUBNET)


# Action groups
ACTION_GROUPS = [
    ANSIBLE,
    CLUSTER,
    COMPUTE,
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
