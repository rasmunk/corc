import os
from corc.config import default_base_path

# Supported providers
ANSIBLE = "ansible"
SUPPORTED_CONFIGURER_PROVIDERS = [ANSIBLE]

default_configurer_path = os.path.join(default_base_path, "configurer")
