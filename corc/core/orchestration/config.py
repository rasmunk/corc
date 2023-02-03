import os
from corc.core.orchestration.defaults import default_orchestration_path

default_general_config = {"providers": []}

valid_general_config = {"providers": list}

general_orcehstration_config_path = os.path.join(
    default_orchestration_path, "general.yml"
)
