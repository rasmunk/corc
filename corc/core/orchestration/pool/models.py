import shelve
import os
from corc.utils.io import acquire_lock, release_lock, remove
from corc.utils.io import exists as file_exists
from corc.core.storage.dictdatabase import DictDatabase


class Pool(DictDatabase):
    def __init__(self, name):
        # The name of the pool is equal to the
        # database name
        super().__init__(name)


# Note, simple discover method that has be to be improved.
# Might create a designed path where the pools are stored
async def discover_pools(path):
    pools = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".db"):
                pools.append(file.replace(".db", ""))
    return pools


class Node:
    def __init__(self, name, **kwargs):
        self.name = name
        self.state = None
        self.config = kwargs

    def print_state(self):
        print(
            "Node name: {}, state: {}, config: {}".format(
                self.name, self.state, self.config
            )
        )

    def __str__(self):
        return "Node name: {}, state: {}, config: {}".format(
            self.name, self.state, self.config
        )

    def asdict(self):
        return {
            "name": self.name,
            "state": self.state,
            "config": self.config,
        }
