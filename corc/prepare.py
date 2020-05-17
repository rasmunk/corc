import os
from oci.core import ComputeClient
from oci.identity import IdentityClient
from oci.core.models import Instance
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.playbook import Playbook
from ansible.executor.task_queue_manager import TaskQueueManager
from oci_helpers import new_client, get_instances
from args import get_arguments, OCI, ANSIBLE

here = os.path.dirname(os.path.abspath(__file__))


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


if __name__ == "__main__":
    args = get_arguments([OCI, ANSIBLE], strip_group_prefix=True)

    # Spawn an oci instance
    compute_client = new_client(ComputeClient, profile_name=args.profile_name)
    identity_client = new_client(IdentityClient, profile_name=args.profile_name)
    instances = get_instances(
        compute_client,
        args.compartment_id,
        lifecycle_state=Instance.LIFECYCLE_STATE_RUNNING,
    )

    # Load inventory
    loader = DataLoader()
    loader.set_basedir(args.root_path)
    inventory_manager = InventoryManager(loader, sources=args.inventory_path)
    variable_manager = VariableManager(loader=loader, inventory=inventory_manager)

    # After being started -> run ansible playbook (wagstaff)
    # Load playbook
    pb = Playbook.load(
        args.playbook_path, variable_manager=variable_manager, loader=loader
    )
    plays = pb.get_plays()

    for play in plays:
        run_playbook(
            play,
            variable_manager=variable_manager,
            inventory_manager=inventory_manager,
            loader=loader,
        )
