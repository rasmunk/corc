import os
import oci
import shelve
import fcntl
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager


here = os.path.abspath(__file__)

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

    playbook_path = os.path.join(here, '..', 'res', 'playbook.yml')
    # Spawn an oci instance
    print("Hello")
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
