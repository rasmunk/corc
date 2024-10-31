import os
import uuid
from corc.core.storage.dictdatabase import DictDatabase


class Pool(DictDatabase):
    def __init__(self, name, **kwargs):
        # The name of the pool is equal to the
        # database name
        super().__init__(name, **kwargs)


# Note, simple discover method that has be to be improved.
# Might create a designed path where the pools are stored
async def discover_pools(path, database_postfix=None):
    if not database_postfix:
        database_postfix = ".db"

    pools = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(database_postfix):
                pools.append(file.replace(database_postfix, ""))
    return pools


class Instance:
    def __init__(self, name, **kwargs):
        self.id = str(uuid.uuid4())
        self.name = name
        self.state = None
        self.config = kwargs

    def print_state(self):
        print(
            "Instance name: {}, state: {}, config: {}".format(
                self.name, self.state, self.config
            )
        )

    def __str__(self):
        return "Instance name: {}, state: {}, config: {}".format(
            self.name, self.state, self.config
        )

    def asdict(self):
        return {
            "name": self.name,
            "state": self.state,
            "config": self.config,
        }
