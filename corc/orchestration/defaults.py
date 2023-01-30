import os
from corc.config import default_base_path

LIBVIRT = "libvirt"
OCI = "oci"
EC2 = "ec2"

BARE_METAL = "bare_metal"
VIRTUAL_MACHINE = "virtual_machine"

SUPPORTED_ORCHESTRATION_PROVIDERS = [LIBVIRT, OCI, EC2]

default_orchestration_path = os.path.join(default_base_path, "orchestration")
