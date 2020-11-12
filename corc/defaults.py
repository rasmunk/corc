import os

from corc.providers.defaults import EC2

# Package name
PACKAGE_NAME = "corc"

# Providers
# AWS = "AWS"
AWS_LOWER = "aws"

OCI = "OCI"
OCI_LOWER = "oci"

PROVIDER = "PROVIDER"
DEFAULT_PROVIDER = OCI
DEFAULT_PROVIDER_LOWER = OCI_LOWER
PROVIDERS = [EC2, OCI]
PROVIDERS_LOWER = [EC2, OCI_LOWER]

PROFILE = "PROFILE"

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

STORAGE = "STORAGE"
S3 = "S3"
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
