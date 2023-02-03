import os
from corc.core.config import default_base_path

ORCHESTRATION_PROVIDER = "ORCHESTRATION_PROVIDER"

# Supported providers
LIBVIRT = "libvirt"
OCI = "oci"
EC2 = "ec2"
SUPPORTED_ORCHESTRATION_PROVIDERS = [LIBVIRT, OCI, EC2]

# Types that can be orchestrated
BARE_METAL = "bare_metal"
VIRTUAL_MACHINE = "virtual_machine"

default_orchestration_path = os.path.join(default_base_path, "orchestration")
