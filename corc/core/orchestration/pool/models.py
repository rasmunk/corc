import uuid
from corc.core.storage.dictdatabase import DictDatabase


class Pool(DictDatabase):
    def __init__(self, name, **kwargs):
        # The name of the pool is equal to the
        # database name
        super().__init__(name, **kwargs)


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
