import argparse
import os
import oci
import shelve
import fcntl
from oci.core import ComputeClient
from oci.identity import IdentityClient
from oci.core.models import Instance
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from oci_helpers import new_client, get_compartment_id, get_instances
from conf import get_arguments

here = os.path.dirname(os.path.abspath(__file__))


def load_playbook_source(path):
    loader = DataLoader()
    play_source = loader.load_from_file(path)
    return play_source


def run_setup_playbook(play_source):
    play = Play()
    tqm = None
    try:
        tqm = TaskQueueManager()
        result = tqm.run(play)
    finally:
        if not tqm:
            tqm.cleanup()


if __name__ == "__main__":
    args = get_arguments()
    playbook_path = os.path.join(here, "..", "res", "playbook.yml")
    # Spawn an oci instance
    compute_client = new_client(ComputeClient, profile_name=args.profile_name)
    identity_client = new_client(IdentityClient, profile_name=args.profile_name)
    instances = get_instances(
        compute_client,
        args.compartment_id,
        lifecycle_state=Instance.LIFECYCLE_STATE_RUNNING,
    )

    # Save instances to the db
    # with shelve.open('instances.db') as db:
    #     for instance in instances:
    #         db[instance.id] = instance

    loader = DataLoader()
    # Load inventory
    inventory_manager = InventoryManager(loader)

    # After being started -> run ansible playbook (wagstaff)
    # Load playbook
    play_source = load_playbook_source(playbook_path)
    run_setup_playbook(play_source)

    ## Register the live instance -> add to shelve
    # with shelve.open(os.path.join()) as lock:

    # Pass job file

    # Schdule the container on the wagstaff instance with the job file

    # Run simulation inside the container

    # transfer back the results

    # Terminate the instance upon completion
