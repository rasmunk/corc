import os
from corc.defaults import default_host_key_order
from corc.io import exists
from corc.helpers import recursive_format
from ansible.config.manager import ConfigManager
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.playbook import Playbook
from ansible.executor.task_queue_manager import TaskQueueManager


def load_playbook_source(path):
    loader = DataLoader()
    play_source = loader.load_from_file(path)
    return play_source


def run_playbook(
    play, variable_manager=None, inventory_manager=None, loader=None, passwords=None
):
    result = -1
    try:
        tqm = TaskQueueManager(
            inventory=inventory_manager,
            variable_manager=variable_manager,
            loader=loader,
            passwords=passwords,
        )
        result = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()
        if loader:
            loader.cleanup_all_tmp_files()
    if result == 0:
        return True
    return False


class AnsibleConfigurer:
    def __init__(self, options=None):
        if not options:
            options = {}
        self.options = options

        self.loader = DataLoader()
        if "inventory_path" in self.options:
            sources = self.options["inventory_path"]
        else:
            sources = None

        self.inventory_manager = InventoryManager(self.loader, sources=sources)

        self.variable_manager = VariableManager(
            loader=self.loader, inventory=self.inventory_manager
        )

        # TODO load ansible configuration
        self.config_manager = ConfigManager()

    def gen_configuration(self, options=None):
        configuration = {}
        if not options:
            options = {}

        configuration["host_variables"] = dict(
            ansible_connection="ssh",
            ansible_ssh_common_args="-o HostKeyAlgorithms={}".format(
                ",".join(default_host_key_order)
            ),
        )

        if "host_variables" in options and isinstance(options["host_variables"], dict):
            configuration["host_variables"].update(options["host_variables"])

        configuration["host_settings"] = {}
        if "host_settings" in options and isinstance(options["host_settings"], dict):
            configuration["host_settings"].update(options["host_settings"])

        configuration["apply_kwargs"] = {}
        if "apply_kwargs" in options and isinstance(options["apply_kwargs"], dict):
            configuration["apply_kwargs"].update(options["apply_kwargs"])
        return configuration

    def format_configuration(self, configuration, kwargs=None):
        if not kwargs:
            kwargs = {}

        host_variables_kwargs = {
            k: v
            for k, v in configuration["host_variables"].items()
            if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict)
        }

        host_settings_kwargs = {
            k: v
            for k, v in configuration["host_settings"].items()
            if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict)
        }

        apply_kwargs = {
            k: v
            for k, v in configuration["apply_kwargs"].items()
            if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict)
        }

        # Format with kwargs
        for key, value in kwargs.items():
            try:
                recursive_format(host_variables_kwargs, {key: value})
                recursive_format(host_settings_kwargs, {key: value})
                recursive_format(apply_kwargs, {key: value})
            except TypeError:
                pass

        configuration["host_variables"].update(host_variables_kwargs)
        configuration["host_settings"].update(host_settings_kwargs)
        configuration["apply_kwargs"].update(apply_kwargs)
        return configuration

    def apply(self, host, configuration=None, credentials=None):
        if not configuration:
            configuration = {}

        if (
            "group" in configuration["host_settings"]
            and configuration["host_settings"]["group"]
        ):
            self.inventory_manager.add_group(configuration["host_settings"]["group"])

        if host not in self.inventory_manager.hosts:
            self.inventory_manager.add_host(host, **configuration["host_settings"])

        for k, v in configuration["host_variables"].items():
            self.variable_manager.set_host_variable(host, k, v)

        if "playbook_paths" not in configuration["apply_kwargs"]:
            return False

        if not isinstance(configuration["apply_kwargs"]["playbook_paths"], (list, set)):
            return False

        for playbook_path in configuration["apply_kwargs"]["playbook_paths"]:
            # Expand the playbook path if it is using relative paths
            playbook_path = os.path.expanduser(playbook_path)
            if not exists(playbook_path):
                print("The playbook_path: {} does not exist".format(playbook_path))
                return False

            if credentials:
                self.variable_manager.set_host_variable(
                    host, "ansible_ssh_private_key_file", credentials.private_key_file
                )

            playbook = Playbook.load(
                playbook_path,
                variable_manager=self.variable_manager,
                loader=self.loader,
            )

            plays = playbook.get_plays()
            for play in plays:
                if not run_playbook(
                    play,
                    variable_manager=self.variable_manager,
                    inventory_manager=self.inventory_manager,
                    loader=self.loader,
                ):
                    return False
        return True

    @classmethod
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise TypeError("options is not a dictionary")
