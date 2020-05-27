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
    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory_manager,
            variable_manager=variable_manager,
            loader=loader,
            passwords=passwords,
        )
        _ = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()
        if loader:
            loader.cleanup_all_tmp_files()


class AnsibleConfigurer:
    def __init__(self, options):
        self.options = options
        self.loader = DataLoader()
        self.inventory_manager = InventoryManager(
            self.loader, sources=self.options["inventory_path"]
        )
        self.variable_manager = VariableManager(
            loader=self.loader, inventory=self.inventory_manager
        )

    def apply(self):

        playbook_path = self.options["playbook_path"]

        playbook = Playbook.load(
            playbook_path, variable_manager=self.variable_manager, loader=self.loader
        )

        plays = playbook.get_plays()
        for play in plays:
            run_playbook(
                play,
                variable_manager=self.variable_manager,
                inventory_manager=self.inventory_manager,
                loader=self.loader,
            )

    @classmethod
    def validate_options(cls, options):
        if not isinstance(options, dict):
            raise TypeError("options is not a dictionary")

        expected_ansible_keys = ["inventory_path", "playbook_path"]
